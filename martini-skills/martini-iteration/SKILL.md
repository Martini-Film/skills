---
name: martini-iteration
description: >-
  Use when the user has seen a generated result and wants to improve, fix, or
  retry it — diagnosing why a shot failed, rewriting the prompt based on problems,
  fixing camera movement, adjusting mood or framing, improving subject consistency,
  or making a shot more cinematic. Do NOT use for initial story development,
  full storyboard planning from scratch, or export.
---

# martini-iteration — Improving generated results

## What this skill does

Takes a generated result the user isn't happy with and turns their feedback into
a better retry. Diagnoses what went wrong, proposes a fix, and either rewrites
the prompt or adjusts the approach.

## What this skill does NOT do

- Initial story development → use **martini-script**
- Planning a full storyboard from scratch → use **martini-storyboard**
- Setting up Subjects for the first time → use **martini-subjects**
- Export → use **martini-export**

## Common user requests

- "This result looks wrong. How should I fix the prompt?"
- "The character is too stiff."
- "The camera movement is not what I wanted."
- "Make this more cinematic."
- "The subject disappeared / changed / looks inconsistent."
- "The lighting is off."
- "It generated the wrong action."

## Diagnosing the problem

Before rewriting, identify what category of failure this is:

| Symptom | Likely cause | Fix |
|---|---|---|
| Character looks different | Subject not used or wrong element | Check `elements` array, confirm Subject is set, see **martini-subjects** |
| Action is wrong | Prompt too vague or action buried at the end | Move action earlier, be more explicit with timing |
| Camera doesn't move right | Camera direction missing or too abstract | Add explicit movement with timing (e.g. "slow push-in 0-5s") |
| Too static / boring | No motion described | Add camera movement and action beats |
| Wrong mood / lighting | Style not specified | Add explicit light, grade, and lens language |
| Too short / truncated | Duration parameter too low | Increase duration or use timeline prompting |
| Looks artificial / "AI-ish" | Over-prompted or conflicting instructions | Simplify — remove redundant adjectives |
| Moderated / rejected | Trigger word in prompt | Note the trigger, rephrase concept, try a different model if it persists |

## How to fix it

### Vague action → explicit beats
Before: `"She walks through the city."`
After:
```
0-5s: she steps off the curb into a busy intersection, looking left — wide shot.
5-12s: she weaves through pedestrians, pace quickening — handheld follow.
12-15s: she stops at a storefront window, catching her reflection — slow push-in.
```

### Wrong or inconsistent subject
Check that the `elements` array has the right Subject and the prompt uses `@Element1`
(not a prose description of the character). If the Subject has too few reference
images, ask the user for more angles — see **martini-subjects**.

### Wrong camera movement
Be explicit about movement type, start/end, and timing:
- Vague: `"camera moves in"`
- Better: `"slow dolly-in from wide to medium, 0–8s"`
- Better: `"handheld, slight drift left, stationary by 5s"`

### Mood and cinematic quality
If it looks flat or generic, add:
- **Lens:** 35mm / 50mm / 85mm — each reads differently
- **Light:** "overcast natural light", "golden hour backlight", "neon-lit, practical sources only"
- **Grade:** "desaturated muted palette", "warm teal-and-orange", "high contrast black and white"
- **Texture:** "film grain", "shallow depth of field", "anamorphic lens flare"

### Variation vs. full regeneration
For a near-miss, prefer a **variation** or **offshoot** node over regenerating
from scratch — it preserves what worked while changing what didn't. Only regenerate
from scratch if the core framing or Subject setup was wrong.

## Keeping notes across the session

Track what's working: which camera/lighting language hit, which model handled a
character well, which prompt structure produced the best result. Reuse it.
`create_text_note` on the canvas is a good place to log this.

## Rejected prompts

When a prompt is moderated:
1. Note the likely trigger.
2. Avoid that word/phrase for the rest of the session.
3. Reframe the concept without the trigger.
4. If a model keeps refusing a concept, suggest switching models — don't retry
   the same prompt on the same model.

## Handoff

When the shot is good → move to the next shot (**martini-shot-generation**) or,
if all shots are done, **martini-export**.
