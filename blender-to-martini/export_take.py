"""Render a Blender viewport take for Martini — standalone, no addon, no auth.

The `blender-to-martini` skill injects this into the user's Blender through the
Blender MCP (`execute_blender_code`). It renders a CLEAN flythrough along the
authored camera (the "guide" Seedance follows) plus an optional first/last
frame, samples the camera path, and emits a small JSON result the agent feeds to
Martini.

Two ops (set CONFIG["op"], default "render"):

  op="render"  Render the guide (+ frames) to files on the Blender host and
               return their paths + sizes + scene params + camera_path. By
               default it returns NO base64 — the agent prepares a presigned R2
               upload (upload_assets_prepare, sized from the reported bytes) and
               then runs op="put" so the bytes go straight to R2, never through
               the agent. Set CONFIG["inline"]=True to also return base64 (the
               small-clip / filesystem-storage fallback for render_blender_take's
               guideBase64).

  op="put"     Given CONFIG["puts"]=[{"path","url","content_type"}], PUT each
               file to its presigned URL via urllib (Content-Type only; R2 signs
               the rest). Returns a per-file status. This is the no-addon,
               no-credentials upload: the presigned URL carries the auth.

Result JSON is printed between ===MARTINI_TAKE_BEGIN=== / ===MARTINI_TAKE_END===
markers so the agent can extract it from Blender's noisy stdout.
"""

import base64
import json
import math
import os
import tempfile
import urllib.error
import urllib.request

import bpy

SEEDANCE_MAX_SECONDS = 15

# Standard aspect ratios Seedance accepts, with 480-720p guide sizes.
ASPECTS = (
    ("16:9", 16 / 9, (1280, 720)),
    ("9:16", 9 / 16, (720, 1280)),
    ("1:1", 1.0, (768, 768)),
    ("4:3", 4 / 3, (960, 720)),
    ("3:4", 3 / 4, (720, 960)),
    ("21:9", 21 / 9, (1280, 548)),
)

DEFAULTS = {
    "op": "render",
    "mode": "follow",
    "guide_engine": "fast_eevee",
    "shot_name": "Blender Take",
    "first_frame": False,  # render a scene-engine first frame (else frame-grabbed in Martini)
    "inline": False,  # also return base64 (small-clip / filesystem-storage fallback)
    "out_json": None,
}

GUIDE_FILENAME = "camera-guide.mp4"
FIRST_FRAME_FILENAME = "first-frame.jpg"
LAST_FRAME_FILENAME = "last-frame.jpg"
CAMERA_PATH_FILENAME = "camera-path.json"


def _load_config():
    cfg = dict(DEFAULTS)
    env = os.environ.get("MARTINI_TAKE_CONFIG")
    if env:
        try:
            cfg.update(json.loads(env))
        except ValueError:
            pass
    # The agent may also inject a CONFIG global before exec.
    injected = globals().get("CONFIG")
    if isinstance(injected, dict):
        cfg.update(injected)
    return cfg


def _nearest_aspect(width, height):
    if not width or not height:
        return "16:9"
    ratio = width / height
    return min(ASPECTS, key=lambda a: abs(a[1] - ratio))[0]


def _guide_dimensions(aspect_key):
    for key, _ratio, dims in ASPECTS:
        if key == aspect_key:
            return dims
    return (1280, 720)


def _pick_eevee_engine():
    try:
        engines = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    except Exception:
        engines = set()
    for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if candidate in engines:
            return candidate
    return None


def _active_camera(scene):
    if scene.camera is None:
        raise RuntimeError("No active scene camera. Set one (View > Cameras > Set Active) before sending to Martini.")
    return scene.camera


def _camera_sample(scene, camera, frame):
    scene.frame_set(frame)
    matrix = camera.matrix_world.copy()
    loc = matrix.translation
    quat = matrix.to_quaternion()
    data = camera.data
    return {
        "frame": frame,
        "time_seconds": round((frame - scene.frame_start) / max(1.0, scene.render.fps), 6),
        "position": {"x": loc.x, "y": loc.y, "z": loc.z},
        "quaternion": {"x": quat.x, "y": quat.y, "z": quat.z, "w": quat.w},
        "fov": math.degrees(data.angle),
        "focal_length_mm": data.lens,
        "sensor_width_mm": data.sensor_width,
    }


def _set_output_format(render, kind):
    """Still JPEG or H.264 MP4. Blender 5.x gates video behind media_type='VIDEO'; 4.x takes FFMPEG directly."""
    img = render.image_settings
    if kind == "image":
        if hasattr(img, "media_type"):
            img.media_type = "IMAGE"
        img.file_format = "JPEG"
        img.quality = 90
    else:
        if hasattr(img, "media_type"):
            img.media_type = "VIDEO"
        img.file_format = "FFMPEG"
        render.ffmpeg.format = "MPEG4"
        render.ffmpeg.codec = "H264"
        render.ffmpeg.audio_codec = "NONE"


def _b64(path):
    with open(path, "rb") as handle:
        return base64.b64encode(handle.read()).decode("ascii")


def _file_ref(path, content_type, filename):
    """A small descriptor the agent turns into an upload_assets_prepare file entry."""
    return {
        "path": path,
        "filename": filename,
        "content_type": content_type,
        "size_bytes": os.path.getsize(path),
    }


def export_take(cfg):
    scene = bpy.context.scene
    camera = _active_camera(scene)
    out_dir = tempfile.mkdtemp(prefix="martini_take_")

    aspect = _nearest_aspect(scene.render.resolution_x, scene.render.resolution_y)
    gw, gh = _guide_dimensions(aspect)
    fps = max(1.0, scene.render.fps)
    frame_start = scene.frame_start
    max_frames = int(SEEDANCE_MAX_SECONDS * fps)
    frame_end = min(scene.frame_end, frame_start + max_frames - 1)
    duration = round(max(1, frame_end - frame_start + 1) / fps, 3)

    first_path = os.path.join(out_dir, FIRST_FRAME_FILENAME)
    last_path = os.path.join(out_dir, LAST_FRAME_FILENAME)
    guide_path = os.path.join(out_dir, GUIDE_FILENAME)

    mode = cfg["mode"]
    # Interpolate needs both frames rendered (no guide to grab from). Follow
    # defaults to frame-grab (first_frame off) — render one only when opted in.
    want_first = mode == "interpolate" or (bool(cfg.get("first_frame", False)) and mode == "follow")
    want_last = mode == "interpolate"
    eevee = _pick_eevee_engine()

    saved = {
        "filepath": scene.render.filepath,
        "engine": scene.render.engine,
        "media_type": getattr(scene.render.image_settings, "media_type", None),
        "file_format": scene.render.image_settings.file_format,
        "ffmpeg_format": scene.render.ffmpeg.format,
        "ffmpeg_codec": scene.render.ffmpeg.codec,
        "ffmpeg_audio": scene.render.ffmpeg.audio_codec,
        "res_x": scene.render.resolution_x,
        "res_y": scene.render.resolution_y,
        "res_pct": scene.render.resolution_percentage,
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_current": scene.frame_current,
        "film_transparent": scene.render.film_transparent,
    }

    try:
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = False

        # First / last frames at guide-class resolution (keeps them small; they're a
        # restyle reference, not the final image). Scene engine = the artist's look.
        _set_output_format(scene.render, "image")
        scene.render.resolution_x = gw
        scene.render.resolution_y = gh
        if want_first:
            scene.render.engine = saved["engine"]
            scene.frame_set(frame_start)
            scene.render.filepath = first_path
            bpy.ops.render.render(write_still=True)
        if want_last:
            scene.frame_set(frame_end)
            scene.render.filepath = last_path
            bpy.ops.render.render(write_still=True)

        # Guide flythrough: EEVEE for speed (Seedance only takes MOTION from it),
        # clean full render (no overlays/gizmos), clamped to the guide size.
        if mode == "follow":
            scene.render.resolution_x = gw
            scene.render.resolution_y = gh
            if cfg["guide_engine"] == "fast_eevee" and eevee:
                scene.render.engine = eevee
            else:
                scene.render.engine = saved["engine"]
            _set_output_format(scene.render, "video")
            scene.frame_start = frame_start
            scene.frame_end = frame_end
            scene.render.filepath = guide_path
            bpy.ops.render.render(animation=True)

        # Sample the authored camera over the FULL authored range (preserve the
        # whole move even if the guide clip is clamped to Seedance's max length).
        samples = [_camera_sample(scene, camera, f) for f in range(saved["frame_start"], saved["frame_end"] + 1)]
        camera_path = {
            "version": 1,
            "source": "blender_viewport",
            "shot_name": cfg["shot_name"],
            "fps": fps,
            "frame_start": saved["frame_start"],
            "frame_end": saved["frame_end"],
            "duration_seconds": round((saved["frame_end"] - saved["frame_start"] + 1) / fps, 3),
            "aspect_ratio": aspect,
            "lens_mm": camera.data.lens,
            "camera": {"name": camera.name, "samples": samples},
        }
    finally:
        scene.render.filepath = saved["filepath"]
        scene.render.engine = saved["engine"]
        if saved["media_type"] is not None:
            scene.render.image_settings.media_type = saved["media_type"]
        scene.render.image_settings.file_format = saved["file_format"]
        scene.render.ffmpeg.format = saved["ffmpeg_format"]
        scene.render.ffmpeg.codec = saved["ffmpeg_codec"]
        scene.render.ffmpeg.audio_codec = saved["ffmpeg_audio"]
        scene.render.resolution_x = saved["res_x"]
        scene.render.resolution_y = saved["res_y"]
        scene.render.resolution_percentage = saved["res_pct"]
        scene.frame_start = saved["frame_start"]
        scene.frame_end = saved["frame_end"]
        scene.frame_set(saved["frame_current"])
        scene.render.film_transparent = saved["film_transparent"]

    # The camera path is written to a file and uploaded as a sidecar of the guide
    # asset (presigned PUT), so the multi-KB sample blob never rides the agent
    # context. render_blender_take reads it back by reference (guideAssetId).
    camera_path_json = os.path.join(out_dir, CAMERA_PATH_FILENAME)
    with open(camera_path_json, "w", encoding="utf-8") as handle:
        json.dump(camera_path, handle)

    guide = _file_ref(guide_path, "video/mp4", GUIDE_FILENAME) if mode == "follow" else None
    first_frame = _file_ref(first_path, "image/jpeg", FIRST_FRAME_FILENAME) if want_first else None
    last_frame = _file_ref(last_path, "image/jpeg", LAST_FRAME_FILENAME) if want_last else None

    result = {
        "ok": True,
        "op": "render",
        "mode": mode,
        "shot_name": cfg["shot_name"],
        "aspect_ratio": aspect,
        "duration_seconds": duration,
        "fps": fps,
        "frame_start": saved["frame_start"],
        "frame_end": saved["frame_end"],
        "camera_name": camera.name,
        "guide": guide,
        "first_frame": first_frame,
        "last_frame": last_frame,
        "camera_path_file": _file_ref(camera_path_json, "application/json", CAMERA_PATH_FILENAME),
    }

    # Fallback path: also return base64 + the full camera_path for
    # render_blender_take's inline inputs — use only for tiny clips or
    # filesystem-only local storage where presigned upload isn't available.
    if bool(cfg.get("inline", False)):
        result["camera_path"] = camera_path
        result["inline"] = {
            "guide_base64": _b64(guide_path) if guide else None,
            "first_frame_base64": _b64(first_path) if first_frame else None,
            "last_frame_base64": _b64(last_path) if last_frame else None,
        }

    return result


def put_files(cfg):
    """PUT already-rendered files to presigned R2 URLs. No credentials needed —
    the presigned URL carries the signature; we send only Content-Type (R2 signs
    Content-Length from the body, matching the size given to upload_assets_prepare)."""
    puts = cfg.get("puts") or []
    if not isinstance(puts, list) or not puts:
        raise RuntimeError("op='put' requires CONFIG['puts'] = [{path, url, content_type}, ...]")

    results = []
    for item in puts:
        path = item.get("path")
        url = item.get("url")
        content_type = item.get("content_type", "application/octet-stream")
        try:
            with open(path, "rb") as handle:
                body = handle.read()
            request = urllib.request.Request(url, data=body, method="PUT")
            request.add_header("Content-Type", content_type)
            with urllib.request.urlopen(request, timeout=180) as response:
                status = response.status
            results.append({"path": path, "ok": 200 <= status < 300, "status": status, "size_bytes": len(body)})
        except urllib.error.HTTPError as exc:
            results.append({"path": path, "ok": False, "status": exc.code, "error": f"HTTP {exc.code}: {exc.reason}"})
        except Exception as exc:  # noqa: BLE001 — surface any failure cleanly to the agent
            results.append({"path": path, "ok": False, "error": str(exc)})

    return {"ok": all(r["ok"] for r in results), "op": "put", "results": results}


def main():
    cfg = _load_config()
    try:
        if cfg.get("op") == "put":
            result = put_files(cfg)
        else:
            result = export_take(cfg)
    except Exception as exc:  # surface a clean error to the agent
        result = {"ok": False, "error": str(exc)}

    payload = json.dumps(result)
    if cfg.get("out_json"):
        with open(cfg["out_json"], "w", encoding="utf-8") as handle:
            handle.write(payload)
    # Markers let the agent extract the JSON from Blender's noisy stdout.
    print("===MARTINI_TAKE_BEGIN===")
    print(payload)
    print("===MARTINI_TAKE_END===")


main()
