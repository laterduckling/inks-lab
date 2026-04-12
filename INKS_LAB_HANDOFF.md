# Ink's Lab — Project Handoff Document
*For Claude Code / Opus session. This document contains all context needed to continue development.*

---

## What This Is

A personalized AI homework companion for a 5-year-old boy in 1st grade at a French-American bilingual school. The app is named **Ink's Lab** and is centered on a character called **Ink** — a chaotic, funny, brilliant octopus scientist who lives in an underwater space station.

The core problem being solved: homework is a nightly fight. The goal is to eliminate the activation energy of starting, make the 15–20 minutes genuinely fun, and have the child do it willingly — even enthusiastically.

**The north star:** the parent wants to hear his son giggle during homework.

---

## The Child — User Profile

- **Age:** 5 years old, 1st grade
- **School:** French-American bilingual. Two teachers (one EN, one FR), separate classes, separate homework.
- **Homework cadence:** 4 days/week, ~15 min normally, up to 30 min with a poem/poésie
- **Homework types:** math, reading aloud, writing, spelling, dictation, poems (poésie)
- **Languages:** 50/50 English and French — treated as completely separate session modes
- **Interests (critical for engagement):** octopuses (favorite animal), sea animals of all kinds, insects, space, engineering, Minecraft, Lego, Ninjago (Lego TV show on Netflix)

---

## Character Design — Ink

- **Ink** is a genius octopus scientist with 8 tentacles, each with its own personality
- Lives in an **underwater space station** (sea + space + engineering unified)
- Personality: chaotic, funny, uses made-up silly words (BLOOPSNORK, SQUIDZOOKS, TENTACULOUS), accidentally squirts ink on equipment, his tentacles argue mid-sentence, makes wildly over-the-top celebrations
- **VENK MODE:** After the 2nd hint request, Ink dramatically "transforms" into VENK — a villain alter-ego. Red/dark bubble styling, speaks in dramatic ALL-CAPS villain speeches that are secretly still just hints. Ink briefly breaks through mid-VENK: *"wait this is Ink for one second — you're doing GREAT — ok VENK IS BACK."* Designed specifically to make the child giggle.
- **Idle tickles:** if child goes quiet for 22 seconds, Ink says something absurd (e.g., *"Tentacle #3 just submitted a formal HR complaint about the waiting"*)
- **Celebrations:** unhinged reactions on task completion (e.g., *"YESSSSS!! Tentacle #4 is doing the victory wiggle and it will NOT stop!!"*)

---

## Core UX Principles (non-negotiable)

1. **Speed to start:** photo → mission brief in <60 seconds. No onboarding friction.
2. **Never give the answer:** Ink is always Socratic — guiding questions only, always
3. **Hard time cap:** sessions should feel short. Ink wraps and declares victory the moment homework is done. No "want to keep going?"
4. **Ink speaks everything aloud** via TTS — the child is 5 and can't fully read
5. **The fight is about starting, not attention span** — once he's in, he'll be fine
6. **Parent visibility without hovering** — parent report auto-generated at end of each session

---

## What's Built — Current State

### Single file: `inks-lab-v2.html`
A self-contained vanilla JS + HTML/CSS app, ~1,350 lines, 65KB. No build system, no dependencies, no framework. Runs in any browser. Currently requires an Anthropic API key (entered once, saved to localStorage).

### Screens (11 total)
1. **API Key screen** — one-time setup, saved to localStorage, auto-skipped on return visits
2. **Welcome screen** — language selector (🇺🇸 / 🇫🇷), space station progress preview, creature card mini-collection
3. **Upload screen** — photo of homework (camera or file), drag & drop support
4. **Analyzing screen** — animated loading while Claude Vision parses the homework
5. **Mission screen** — Ink's briefing, task list with progress bar, launch button
6. **Task screen** — Socratic chat with Ink, hint button, verify button, done button
7. **Verify Written screen** — 2nd photo → Claude Vision checks work is actually done
8. **Verify Reading screen** — live microphone → speech-to-text → Claude checks fluency + asks comprehension question
9. **Reward screen** — confetti, VENK-or-Ink celebration quote, space station block added, creature card flip animation (if new card unlocked)
10. **Summary screen** — updated station grid, parent report (completed / shone / struggled / tip / cognitive insight)
11. **Parent Mode** — accessed by long-pressing "INK'S LAB" title for 1.5s. Shows session history, cognitive profile stats, struggle pattern insights after 3+ sessions. Has "Forget key" button.

### Features implemented
- ✅ Claude Vision homework parsing → structured JSON task plan
- ✅ Socratic chat (never gives answers, 2-3 short sentences, age-appropriate)
- ✅ EN/FR full separation — language set per session, all prompts/UI adapt
- ✅ TTS (Web Speech API) — Ink speaks every message. Mute toggle top-right.
- ✅ STT (Web Speech API) — for reading verification
- ✅ Written work verification via 2nd photo
- ✅ 3-tier progressive hint system (Hint 1 → Hint 2 → VENK transformation)
- ✅ VENK mode (triggers at hint #2, red styling, villain persona, still Socratic)
- ✅ Idle tickle system (22s silence → Ink says something absurd)
- ✅ Haptic feedback (navigator.vibrate patterns)
- ✅ Confetti on task completion
- ✅ Space station grid (30 blocks, persists in localStorage, fills session by session)
- ✅ Creature card collection system (23 cards: sea/space/insects, 3 rarity tiers, flip animation)
- ✅ Session history persistence (up to 20 sessions in localStorage)
- ✅ Cognitive profile: tracks hints-per-session, subjects, duration, surfaces struggle patterns
- ✅ Parent report generated by Claude at session end
- ✅ API key saved to localStorage (enter once, never again)
- ✅ PWA meta tags (Add to Home Screen on iOS)

### Model usage
- All calls use `claude-sonnet-4-6` (the latest Sonnet)
- Vision call (homework analysis): ~900 max tokens
- Chat calls (Ink responses): ~180 max tokens  
- Verification calls: ~200 max tokens
- Summary/parent report: ~320 max tokens
- Cost per session: ~$0.05–0.10

---

## Tech Stack

- **Pure vanilla JS** — no React, no build system, no npm
- **Single HTML file** — everything inline (CSS + JS + HTML)
- **APIs used:**
  - Anthropic `/v1/messages` — called directly from browser with `anthropic-dangerous-direct-browser-access: true` header
  - Web Speech API — TTS (`speechSynthesis`) and STT (`SpeechRecognition`)
  - `navigator.vibrate` — haptics
  - `localStorage` — persistence (API key, station blocks, cards, sessions)
  - `FileReader` + base64 — image uploads to Claude Vision

---

## Deployment Problem (why we're here)

The app works perfectly as a local file on Mac. The problem is **iOS Safari**:
- Safari on iOS doesn't reliably retain localStorage for files opened via AirDrop
- No persistent URL = no bookmarkable link = can't "Add to Home Screen" cleanly

**Agreed solution: host on GitHub Pages**
- Free, permanent URL (e.g. `https://[username].github.io/inks-lab`)
- Works perfectly with localStorage on iOS Safari
- Add to Home Screen → feels like a native app, full screen, no browser chrome
- Takes ~10 minutes to set up

---

## Immediate Next Steps (Priority Order)

### 1. GitHub Pages deployment (do this first)
- Create GitHub repo
- Push `inks-lab-v2.html` as `index.html`
- Enable GitHub Pages
- Test on iPhone/iPad Safari
- Add to Home Screen

### 2. Custom app icon for Home Screen
- Currently uses default icon
- Need a 180×180px PNG of Ink (the octopus) for `apple-touch-icon`
- Could generate with image AI or use an emoji-rendered PNG

### 3. Session continuity — "Ink remembers you"
- Currently Ink has no memory of past sessions at chat level
- Enhancement: inject last 2-3 sessions' weak spots into the system prompt
- *"Last time we worked on addition, you found carrying numbers tricky — let's see if that's easier today!"*

### 4. Weekend Recap Mission (Phase 2 feature, already designed)
- Friday evening: Ink sends a "weekend mission" that's purely game-framed
- Recaps week's weak spots as a fun challenge, not homework
- Could involve the parent as co-player

### 5. Poem/Poésie mode
- Special handling for memorization tasks
- Ink reads the poem aloud (TTS) line by line
- Child repeats, STT checks
- Spaced repetition: 3 passes, getting less scaffolded each time

### 6. Space station visual upgrade
- Currently simple emoji grid
- Could render a proper pixel-art station that visually grows
- Each subject unlocks a different module type (math = engine room, reading = library, etc.)

### 7. Cognitive profile deepening
- Track which *specific* concepts are hard (not just subjects)
- E.g., "addition with carrying" vs just "math"
- Requires structured hint logging per concept

---

## Known Issues / Things to Watch

- `reSpeak()` function in HTML uses element ID text, which may include the "Ink 🐙" label — should strip that before speaking
- VENK mode resets on `startTask()` but hintCount is also reset — this is correct behavior, just document it
- STT (reading verification) requires HTTPS on iOS — another reason GitHub Pages deployment matters
- The `capture="environment"` attribute on file inputs opens rear camera on mobile — correct for homework photos
- Parent mode is hidden (long press) intentionally — don't surface it in the child's UI

---

## Decisions Already Made (don't relitigate these)

| Decision | Rationale |
|---|---|
| Single HTML file | Zero friction deployment, works offline, easy to AirDrop |
| Vanilla JS (no framework) | Same reason. Also: 5yo app doesn't need React |
| Sonnet for all calls | Fast enough, cheap enough. Opus not needed at runtime |
| Opus for dev decisions | Use Opus (this session) for architecture/design decisions |
| No backend | API key in localStorage is acceptable for personal family use |
| Dark space/ocean theme | Matches the child's interests. Non-negotiable. |
| VENK after hint #2 (not #1) | Gives one normal hint first before going full villain |
| 22s idle timer | Long enough not to be annoying, short enough to re-engage |
| 30-block station | Gives ~30 sessions of progression before "completing" — roughly one school term |

---

## File Structure (current — single file, to be expanded)

```
inks-lab/
├── index.html          ← the entire app (rename from inks-lab-v2.html)
└── INKS_LAB_HANDOFF.md ← this document
```

**Future structure (Phase 2):**
```
inks-lab/
├── index.html
├── manifest.json       ← PWA manifest
├── icon-180.png        ← Home Screen icon
├── icon-512.png        ← PWA icon
└── sw.js               ← Service worker for offline support
```

---

## How to Start the Claude Code Session

Paste this at the top of your first message:

> "I'm continuing development of Ink's Lab — a personalized AI homework app for my 5-year-old son. Full context is in INKS_LAB_HANDOFF.md in this folder. Please read it before we start. The app is currently a single HTML file (index.html). First priority is GitHub Pages deployment so it works reliably on his iPad. Then we'll continue feature development from the roadmap in the handoff doc."

---

*Last updated: from Claude Sonnet chat session. All features listed as ✅ are confirmed working with syntax-validated JS.*
