# Finance Shorts: production pipeline

Animated finance storytelling for a US audience (business case studies, financial habits, money advice, scams). The look follows the
reference short: flat 2D cartoon characters acting in lit, stylised-realistic 3D worlds, fast cuts, one or two words of captions at a time, and an expressive
narrator. See [`reference/STYLE_BIBLE.md`](reference/STYLE_BIBLE.md) for the full frame-by-frame breakdown.

Formats: **Shorts / Reels 9:16 1080×1920** (default, 45–60 s) and occasional **YouTube long-form 16:9 3840×2160/1920×1080**.

## Workflow (each step needs the owner's approval before the next one starts)

| Step | Output | Where | Gate |
|---|---|---|---|
| 1. Topic research | Ranked shortlist with data + fact-check plan | `research/` | Owner picks one topic |
| 2. Script | Narration + shot-by-shot storyboard + on-screen text + sources | `scripts/<slug>/` | Owner reviews hook/engagement, gives feedback, approves |
| 3. Audio | Fish Audio S2.1 Pro voiceover (voice audition first), word timestamps | `audio/<slug>/` | Owner approves the voice and the read |
| 4. Visuals | Environments, characters, animation, captions, SFX + music, −14 LUFS master | `visuals/<slug>/` → `deliverables/` | Owner reviews the full cut, requests changes or approves |
| 5. Publish | YouTube (Shorts or long-form) + Instagram Reels for 9:16 | `deliverables/<slug>/publish.json` | Upload only after final approval |

## Tooling

* **Voice:** `audio/fish_tts.py`, model `s2.1-pro-free` (Fish Audio S2.1 Pro, free route). The paid `s2.1-pro` needs wallet credit.
  The API key is stored as a network secret on the cloud environment, never in the repo.
* **Visuals:** 3D environments and props, our own original vector character rigs composited into the plates with perspective, contact
  shadows, light-wrap and depth of field, a moving virtual camera, and word-timed captions. Rendered at 1080×1920 / 30 fps.
* **Publishing:** YouTube and Instagram via the connected vidIQ integration (account connection is checked at step 5).

## Reference video

`tools/fetch_reference.sh` downloads it into the session scratchpad. It isn't committed.
