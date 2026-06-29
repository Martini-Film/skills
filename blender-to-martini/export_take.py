"""Render a Blender viewport take for Martini — standalone, no addon, no auth.

The `blender-to-martini` skill injects this into the user's Blender through the
Blender MCP (`execute_blender_code`). It renders a CLEAN flythrough along the
authored camera (the "guide" Seedance follows) plus a first frame, samples the
camera path, and emits a small JSON result the agent feeds to Martini's
`render_blender_take` tool.

It does no networking and touches no credentials: Blender renders, the agent
carries the bytes to Martini. Media is base64 in the result; we keep it small
(a 480-720p guide clip + a 720p-class JPEG first frame) so the agent context
stays cheap.

Config (the agent fills CONFIG, or sets $MARTINI_TAKE_CONFIG to the same JSON):
  mode            "follow" (default) | "interpolate"
  guide_engine    "fast_eevee" (default) | "scene"
  shot_name       str
  first_frame     bool (default False)  render + return a first frame in Blender.
                  Default off: Martini frame-grabs frame 0 of the guide (same
                  camera, pixel-consistent, one fewer render). Turn ON only for a
                  materials-rich scene where you want a full scene-engine still.
  out_json        optional path to also write the result JSON to (test harness)

Result JSON (printed between ===MARTINI_TAKE_BEGIN/END=== markers):
  { ok, mode, shot_name, aspect_ratio, duration_seconds, fps, frame_start,
    frame_end, camera_name, guide_base64, first_frame_base64, last_frame_base64,
    camera_path }
"""

import base64
import json
import math
import os
import tempfile

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
    "mode": "follow",
    "guide_engine": "fast_eevee",
    "shot_name": "Blender Take",
    "first_frame": False,  # default: Martini frame-grabs frame 0 of the guide
    "out_json": None,
}


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

    first_path = os.path.join(out_dir, "first-frame.jpg")
    last_path = os.path.join(out_dir, "last-frame.jpg")
    guide_path = os.path.join(out_dir, "camera-guide.mp4")

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

        # First / last frames at guide-class resolution (keeps base64 small; it's a
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

    return {
        "ok": True,
        "mode": mode,
        "shot_name": cfg["shot_name"],
        "aspect_ratio": aspect,
        "duration_seconds": duration,
        "fps": fps,
        "frame_start": saved["frame_start"],
        "frame_end": saved["frame_end"],
        "camera_name": camera.name,
        "guide_base64": _b64(guide_path) if mode == "follow" else None,
        "first_frame_base64": _b64(first_path) if want_first else None,
        "last_frame_base64": _b64(last_path) if want_last else None,
        "camera_path": camera_path,
    }


def main():
    cfg = _load_config()
    try:
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


if __name__ == "__main__":
    main()
