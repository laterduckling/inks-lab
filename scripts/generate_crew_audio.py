#!/usr/bin/env python3
"""Generate ElevenLabs TTS clips for Ink's Crew.

Usage:
    ELEVEN_API_KEY=sk_xxx python3 scripts/generate_crew_audio.py

Writes one MP3 per character per language into ./audio/crew/<key>-<lang>.mp3
Skips files that already exist (delete + re-run to regenerate).

As more voice IDs are collected, append them to VOICES below and re-run —
existing files are kept so only new clips burn ElevenLabs credits.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_KEY = os.environ.get('ELEVEN_API_KEY')
if not API_KEY:
    sys.exit('Set ELEVEN_API_KEY env var. Find or create one at '
             'elevenlabs.io → My Account → API Keys.')

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'audio' / 'crew'
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = 'eleven_multilingual_v2'

# Map character key → ElevenLabs voice ID.
# Add more entries as Mathieu collects more voices.
VOICES = {
    'baby':    'ocZQ262SsZb9RIxcQBOj',
    'mama':    'TDdaEMZGTCMRB4x8bVQ2',
    'papa':    'uju3wxzG5OhpWcoi3SMy',
    'grandma': 'wGcFBfKz5yUQqhqr0mVy',
    'grandpa': 'MKlLqCItoCkvdhrxgtLv',
}

# Must stay in sync with CREW.factEN / factFR in index.html.
FACTS = {
    'baby': {
        'en': "Baby octopuses are about the size of a grain of rice when they hatch. They drift as plankton near the surface for weeks before they're big enough to settle to the seafloor.",
        'fr': "Les bébés poulpes ont à peu près la taille d'un grain de riz quand ils éclosent. Ils dérivent en plancton près de la surface pendant des semaines avant de descendre au fond.",
    },
    'mama': {
        'en': "Mother octopuses guard their eggs for months without eating. A blue-ringed octopus mom will literally starve to keep her babies safe until they hatch.",
        'fr': "Les mamans poulpes gardent leurs œufs pendant des mois sans manger. Une maman poulpe aux anneaux bleus se laisse littéralement mourir de faim pour protéger ses bébés jusqu'à l'éclosion.",
    },
    'papa': {
        'en': "Most male octopuses live only 1 to 2 years, and many die shortly after mating. A wandering explorer-dad octopus is extremely rare.",
        'fr': "La plupart des poulpes mâles ne vivent que 1 à 2 ans, et beaucoup meurent peu après l'accouplement. Un papa poulpe explorateur qui voyage est extrêmement rare.",
    },
    'grandma': {
        'en': "Blue-ringed octopuses typically live just 1 or 2 years. An octopus that lives long enough to have grandchildren is almost never seen by scientists.",
        'fr': "Les poulpes aux anneaux bleus vivent en général seulement 1 ou 2 ans. Un poulpe qui vit assez longtemps pour avoir des petits-enfants, les scientifiques n'en voient presque jamais.",
    },
    'grandpa': {
        'en': "An octopus's brain rewires itself every time it learns something new. By the time you're a grandpa octopus, your brain has been reorganized thousands of times.",
        'fr': "Le cerveau du poulpe se réorganise à chaque fois qu'il apprend quelque chose de nouveau. Quand tu es devenu un papi poulpe, ton cerveau a été réécrit des milliers de fois.",
    },
}


def generate(voice_id: str, text: str) -> bytes:
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    body = json.dumps({
        'text': text,
        'model_id': MODEL,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True,
        },
    }).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'xi-api-key': API_KEY,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg',
        },
    )
    with urllib.request.urlopen(req) as r:
        return r.read()


total_chars = 0
generated = 0
skipped = 0

for key, voice_id in VOICES.items():
    if key not in FACTS:
        print(f'  ⚠ no fact text defined for "{key}", skipping')
        continue
    for lang in ('en', 'fr'):
        text = FACTS[key][lang]
        out = OUT_DIR / f'{key}-{lang}.mp3'
        if out.exists():
            print(f'  ✓ {out.relative_to(ROOT)} (already exists, skipped)')
            skipped += 1
            continue
        print(f'Generating {key}-{lang} ({len(text)} chars)…', flush=True)
        try:
            data = generate(voice_id, text)
            out.write_bytes(data)
            print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
            total_chars += len(text)
            generated += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', 'replace')[:300]
            print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
        except Exception as e:
            print(f'  ✗ {e}')

print(
    f'\nDone. Generated {generated} new clip(s), skipped {skipped} existing. '
    f'Used roughly {total_chars} characters of ElevenLabs credit.'
)
