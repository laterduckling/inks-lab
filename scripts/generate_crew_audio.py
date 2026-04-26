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
import random
import re
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
    # Family
    'baby':           'ocZQ262SsZb9RIxcQBOj',
    'mama':           'TDdaEMZGTCMRB4x8bVQ2',
    'papa':           'uju3wxzG5OhpWcoi3SMy',
    'grandma':        'wGcFBfKz5yUQqhqr0mVy',
    'grandpa':        'MKlLqCItoCkvdhrxgtLv',
    # Other octopus species
    'giant-pacific':  'WV1q3LPagg6vb034LpdG',
    'mimic':          'OTMqA7lryJHXgAnPIQYt',
    'coconut':        'av1BMOR1GPgThz9p4fLo',
    'flapjack':       'XJ2fW4ybq7HouelYYGcL',
    'argonaut':       'mqyRCI8OeJTogXjYUGZ5',
    'wunderpus':      '4HvexEZMAmq2M66Ae0nD',
    # Other sea creatures
    'hammerhead':     'A921zklid24OpyVy1Elb',
    'cuttlefish':     'YgzytRZyVmEux6PCtJYB',
    'whale-shark':    'lAqElvydqyTzitpwAdj6',
    'dumbo':          'oQeBs2hQbwq5LlUV8TtR',
    'giant-squid':    '5egO01tkUjEzu7xSSE8M',
    'nautilus':       'bD9maNcCuQQS75DGuteM',
    'colossal-squid': '2tTjAGX0n5ajDmazDcWk',
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
    'giant-pacific': {
        'en': "The giant Pacific octopus is the biggest octopus on Earth. A single one has about 2,200 suckers across its eight arms — every sucker can taste, smell, AND grip on its own.",
        'fr': "Le poulpe géant du Pacifique est le plus grand poulpe du monde. Un seul a environ 2 200 ventouses sur ses huit bras — chacune peut goûter, sentir et saisir toute seule.",
    },
    'mimic': {
        'en': "The mimic octopus can impersonate over 15 different sea creatures — flatfish, lionfish, sea snakes — by changing its shape, color, AND movement to match.",
        'fr': "Le poulpe mime peut imiter plus de 15 créatures marines — poissons plats, rascasses, serpents de mer — en changeant sa forme, sa couleur ET ses mouvements.",
    },
    'coconut': {
        'en': "The coconut octopus carries halves of coconut shells along the seafloor and snaps them shut around itself for shelter. It's one of the only invertebrates known to use tools.",
        'fr': "Le poulpe noix de coco transporte des moitiés de noix de coco sur le fond marin et les referme autour de lui pour se cacher. C'est un des seuls invertébrés connus à utiliser des outils.",
    },
    'flapjack': {
        'en': "Flapjack octopuses live thousands of meters deep where there's almost no food. Their flat pancake shape lets them drift slowly and save energy in the near-freezing dark.",
        'fr': "Les poulpes crêpes vivent à des milliers de mètres de profondeur où il n'y a presque rien à manger. Leur forme plate leur permet de dériver lentement et d'économiser de l'énergie dans le noir glacé.",
    },
    'argonaut': {
        'en': "Argonauts are the only octopuses that live in the open ocean. Females secrete their own thin paper-like white shell to carry their eggs, and sometimes they hitch rides on jellyfish.",
        'fr': "Les argonautes sont les seuls poulpes qui vivent en pleine mer. Les femelles fabriquent elles-mêmes une fine coquille blanche et s'accrochent parfois à des méduses pour voyager.",
    },
    'wunderpus': {
        'en': "Every wunderpus has a unique pattern of orange and white stripes, like a fingerprint. Scientists can identify individual wunderpuses from photos just by matching the stripes.",
        'fr': "Chaque wunderpus a un motif unique de rayures orange et blanches, comme une empreinte digitale. Les scientifiques peuvent identifier chaque individu juste en regardant ses rayures.",
    },
    'hammerhead': {
        'en': "Hammerhead sharks have eyes on the ends of their hammer, giving them almost 360-degree vision. They can see above AND below themselves at the same time.",
        'fr': "Les requins marteaux ont les yeux aux extrémités du marteau, ce qui leur donne une vision presque à 360 degrés. Ils peuvent voir au-dessus et en dessous d'eux en même temps.",
    },
    'cuttlefish': {
        'en': "A cuttlefish can put a rival to sleep with a hypnotic light-show on its skin. Some cuttlefish even show male colors on one side and female colors on the other at the same time.",
        'fr': "Une seiche peut endormir un rival avec un spectacle hypnotique de couleurs. Certaines seiches montrent même des couleurs de mâle d'un côté et de femelle de l'autre en même temps.",
    },
    'whale-shark': {
        'en': "The whale shark is the biggest fish in the ocean — up to 18 meters long, about the length of a school bus — but it only eats plankton and tiny fish. Each one's spot pattern is unique, like a fingerprint.",
        'fr': "Le requin-baleine est le plus grand poisson de l'océan — jusqu'à 18 mètres, à peu près la taille d'un bus scolaire — mais il ne mange que du plancton et de tout petits poissons. Chaque individu a un motif de taches unique, comme une empreinte digitale.",
    },
    'dumbo': {
        'en': "The dumbo octopus lives deeper than any other octopus — over 4 kilometers down — where the water pressure would crush a human. It flies by flapping its ear-like fins.",
        'fr': "Le poulpe Dumbo vit plus profondément que tous les autres poulpes — à plus de 4 kilomètres de profondeur — là où la pression de l'eau écraserait un humain. Il vole en battant ses nageoires qui ressemblent à des oreilles.",
    },
    'giant-squid': {
        'en': "The giant squid has the largest eye of any animal — about the size of a basketball — to catch faint flashes of bioluminescent light in the pitch-black deep sea.",
        'fr': "Le calmar géant a le plus grand œil du règne animal — environ la taille d'un ballon de basket — pour capter les faibles flashs de lumière bioluminescente dans les abysses noirs.",
    },
    'nautilus': {
        'en': "The nautilus is a living fossil. Its relatives have been swimming in Earth's oceans for over 500 million years — older than dinosaurs, older than trees, older than almost anything still alive today.",
        'fr': "Le nautile est un fossile vivant. Ses cousins nagent dans les océans de la Terre depuis plus de 500 millions d'années — plus vieux que les dinosaures, plus vieux que les arbres, plus vieux que presque tout ce qui vit encore.",
    },
    'colossal-squid': {
        'en': "The colossal squid has the LARGEST eye ever measured in any animal — up to 30 centimeters across. And unlike other squids, its tentacles have sharp rotating hooks instead of just suction cups.",
        'fr': "Le calmar colossal a le PLUS GRAND œil jamais mesuré chez un animal — jusqu'à 30 centimètres de diamètre. Et contrairement aux autres calmars, ses tentacules ont des crochets rotatifs tranchants au lieu de simples ventouses.",
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


# ─── Ink narration (greeting + 40 random facts, voiced by Mark) ────────────
INK_VOICE_ID = 's3TPKV1kjDlVtZbl4Ksh'  # Adam — Engaging, Friendly and Bright (storyteller)
INK_OUT = ROOT / 'audio' / 'ink'
INK_OUT.mkdir(parents=True, exist_ok=True)

# Match the JS regex used in speak() for emoji stripping (so the audio doesn't
# include "sparkles" being read literally).
EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001FFFF☀-➿⌀-⏿️‍]',
    re.UNICODE,
)

INK_GREETINGS = {
    'en': 'Hi Jules!',
    'fr': 'Salut Jules !',
}

INK_INTROS = {
    'en': [
        "Hey, want to hear a fun octopus fact?",
        "Did you know that...",
        "Oh — random one for you.",
        "Okay, this one's cool.",
        "Did you know?",
        "Quick one —",
        "Here's something wild.",
        "Let me tell you something.",
        "Oh! I just remembered something.",
        "Want to hear something weird?",
    ],
    'fr': [
        "Hé, tu veux entendre un fait marrant sur les poulpes ?",
        "Tu savais que...",
        "Oh — un truc au hasard pour toi.",
        "Ok, celui-là est cool.",
        "Le savais-tu ?",
        "Un truc rapide —",
        "Voici quelque chose de dingue.",
        "Laisse-moi te dire un truc.",
        "Oh ! Je viens de me rappeler quelque chose.",
        "Tu veux entendre quelque chose de bizarre ?",
    ],
}

# Must stay 1:1 (and in same order) with OCT_FACTS_EN / OCT_FACTS_FR in
# index.html so JS index lookups (audio/ink/fact-NN-<lang>.mp3) match.
INK_FACTS = {
    'en': [
        "🧪 Blue-ringed octopuses carry tetrodotoxin — the same neurotoxin pufferfish have. One bite can kill a grown adult in minutes, and there is still no antivenom.",
        "❤️ Octopuses have three hearts. Two pump blood through the gills, one through the rest of the body. The main heart actually stops when they swim — that's why they prefer to crawl.",
        "💙 Octopus blood is blue because it uses copper-based hemocyanin instead of iron-based hemoglobin. Hemocyanin carries oxygen better in cold, deep, low-oxygen water.",
        "🧠 An octopus has nine brain-like clusters: one central brain, plus a big ganglion in each of its eight arms. Each arm can figure things out on its own.",
        "🧬 Octopuses can edit their own RNA — changing how their proteins are built on the fly. Almost no other animal does this. Scientists think it helps them adapt to different waters fast.",
        "🎭 The mimic octopus can impersonate over 15 other sea creatures — lionfish, flatfish, sea snakes — by changing shape, color, and movement to match.",
        "👁️ Octopuses are color-blind — they see in grayscale. But they camouflage perfectly to any color. Researchers think they may sense color through light-reading proteins in their skin.",
        "🥚 A mother octopus guards her eggs for months without eating. When they hatch, a gland in her brain triggers her body to shut down. She doesn't survive long after.",
        "👅 Every sucker on an octopus arm can taste and smell what it touches. Imagine tasting everything you pick up with your hands.",
        "🥥 Coconut octopuses collect coconut shell halves, carry them along the seafloor, and snap them shut to hide inside — one of the only invertebrates known to use tools.",
        "🕳️ An octopus can squeeze through any hole bigger than its beak — the only hard part of its body. A 600-pound giant Pacific octopus can fit through a gap the size of an orange.",
        "🎨 Octopus skin has chromatophores — tiny pigment sacs controlled by muscles. They can change color and pattern in less than a second.",
        "⚠️ When threatened, a blue-ringed octopus flashes its rings in about a third of a second — a warning that its bite is deadly. That fast flash is the whole point of the rings.",
        "🦑 Giant Pacific octopuses can grow over 5 meters from tentacle tip to tentacle tip — but they only live 3 to 5 years, and most of that time alone.",
        "🧸 Octopuses have been filmed playing — pushing plastic bottles into a tank current, catching them, releasing them again. Play is rare in the animal world; it usually means high intelligence.",
        "💨 Octopus ink doesn't just hide them. It contains chemicals that temporarily disable a predator's sense of smell and taste — a sensory bomb as well as a smoke screen.",
        "🧠 Octopuses can recognize individual humans. Aquarium keepers have reported being sprayed with water by one octopus (a grudge) while another nearby treated them gently.",
        "🐚 The argonaut is a strange octopus where the female secretes her own thin, translucent white shell to carry her eggs — the only cephalopod that makes a shell as an adult.",
        "💪 If an octopus loses an arm to a predator, it can regrow it completely — nerves, suckers, and all. It takes a few months.",
        "💘 In some octopus species, the male's mating arm can DETACH from his body and swim on its own to find a female. It's called a hectocotylus.",
        "🩱 Female blanket octopuses are up to 10,000 times heavier than males. The tiny males carry stolen Portuguese man-o-war tentacles as stinging weapons — they're immune to the venom.",
        "💤 Recent studies show octopuses cycle through REM-like sleep stages and change color while asleep — which some scientists think may mean they dream.",
        "⚡ An octopus has about 500 million neurons — roughly as many as a dog — and two-thirds of them are in its arms, not its brain.",
        "🧛 The vampire squid isn't a true octopus, but a close relative. It lives in the 'oxygen minimum zone' — water so low in oxygen that almost nothing else survives — kilometers down in the deep sea.",
        "🦴 An octopus's beak is made of chitin — the same material as insect exoskeletons. It's hard enough to crack open a crab, while the rest of the octopus is completely soft.",
        "👽 Cephalopods split off from our evolutionary line about 600 million years ago. Scientists sometimes call them the closest thing to aliens on Earth — their intelligence evolved completely separately from ours.",
        "⏳ The Dumbo octopus lives so deep and in such cold water that its metabolism is very slow — it can live up to 24 years. Most shallow-water octopuses only live 1 to 5 years.",
        "🔍 A giant Pacific octopus has about 280 suckers on each arm, in two rows. That's over 2,200 suckers total — each one can taste, smell, and grip independently.",
        "☀️ Octopus skin contains opsins — the same light-sensitive proteins found in eyes. That's why scientists think octopuses might 'see' colors through their skin, even though their actual eyes can't.",
        "🐟 Cuttlefish and squid have an internal shell (a cuttlebone or a gladius). Octopuses are the only cephalopods with no shell at all — which is why they can squish through almost any hole.",
        "🦐 The smallest octopus is the star-sucker pygmy (Octopus wolfi). Fully grown, it's only about 15 millimeters long — small enough to fit on your fingertip.",
        "🫙 Octopuses can open jars. Not just from the outside — they can figure it out from the inside too. Some have learned by watching another octopus do it first.",
        "🐋 Octopus beaks are so tough they survive being eaten. Scientists find them intact in sperm whale stomachs and use them to identify which species the whale was hunting.",
        "🪨 Octopuses can change the TEXTURE of their skin, not just the color. Tiny bumps called papillae pop up to match rough coral or jagged rocks.",
        "🦾 Each octopus arm has its own mini-brain of sorts. Even an arm cut off from the body (don't) can still grab food and move it toward where the mouth would be — for about an hour.",
        "📚 'Octopus' is Greek for 'eight feet.' The correct plurals are 'octopuses' or 'octopodes' — NOT 'octopi.' That one sounds right but is grammatically wrong because the word isn't Latin.",
        "⏳ Cephalopod fossils date back nearly 500 million years. Octopuses and their relatives are among the oldest animal lineages still alive on Earth today.",
        "👁️ The California two-spot octopus has two fake 'eye spots' painted onto its mantle. If a predator strikes the fake eyes, the real octopus has time to jet away.",
        "🛡️ Some octopuses carry rocks, shells, or pieces of kelp to use as makeshift body armor when threatened — another clear case of real tool use.",
        "💡 A captive octopus named Otto, at an aquarium in Germany, repeatedly squirted water at a bright ceiling lamp until it shorted out. The aquarists think he did it because the light annoyed him.",
    ],
    'fr': [
        "🧪 Le poulpe aux anneaux bleus contient de la tétrodotoxine — le même poison mortel que le poisson-globe. Une morsure peut tuer un adulte en quelques minutes, et il n'existe toujours aucun antidote.",
        "❤️ Les poulpes ont trois cœurs. Deux envoient le sang dans les branchies, un dans le reste du corps. Le cœur principal s'arrête quand ils nagent — c'est pour ça qu'ils préfèrent ramper.",
        "💙 Le sang du poulpe est bleu parce qu'il utilise de l'hémocyanine (à base de cuivre) au lieu de l'hémoglobine (fer). L'hémocyanine transporte mieux l'oxygène dans l'eau froide et profonde.",
        "🧠 Le poulpe a neuf regroupements de neurones : un cerveau central, plus un gros ganglion dans chacun de ses huit bras. Chaque bras peut réfléchir un peu tout seul.",
        "🧬 Les poulpes savent modifier leur propre ARN — ils changent la façon dont leurs protéines sont fabriquées en direct. Presque aucun autre animal ne fait ça. Ça les aide à s'adapter vite à des milieux différents.",
        "🎭 Le poulpe mime peut imiter plus de 15 créatures marines — rascasse, poisson plat, serpent de mer — en changeant sa forme, sa couleur et ses mouvements.",
        "👁️ Les poulpes sont daltoniens — ils voient en noir et blanc. Mais ils se camouflent parfaitement en n'importe quelle couleur. Les scientifiques pensent qu'ils 'voient' les couleurs grâce à des protéines dans leur peau.",
        "🥚 La maman poulpe protège ses œufs pendant des mois sans manger. Quand ils éclosent, une glande dans son cerveau déclenche l'arrêt de son corps. Elle ne survit pas très longtemps après.",
        "👅 Chaque ventouse sur un bras de poulpe peut goûter et sentir ce qu'elle touche. Imagine goûter tout ce que tu prends avec tes mains.",
        "🥥 Le poulpe noix de coco ramasse des demi-coquilles de noix de coco, les transporte, et les referme pour se cacher dedans — un des seuls invertébrés connus à utiliser des outils.",
        "🕳️ Un poulpe peut passer par n'importe quel trou plus grand que son bec — la seule partie dure de son corps. Un poulpe géant de 270 kg peut se glisser par un trou de la taille d'une orange.",
        "🎨 La peau du poulpe contient des chromatophores — de petits sacs de pigment contrôlés par des muscles. Ils changent de couleur et de motif en moins d'une seconde.",
        "⚠️ Quand il se sent menacé, le poulpe aux anneaux bleus fait clignoter ses anneaux en environ un tiers de seconde — un signal d'alerte qu'une morsure est mortelle.",
        "🦑 Le poulpe géant du Pacifique peut mesurer plus de 5 mètres d'une pointe de tentacule à l'autre — mais il ne vit que 3 à 5 ans, souvent en solitaire.",
        "🧸 Des poulpes ont été filmés en train de jouer — ils poussent des bouteilles en plastique dans le courant d'un aquarium, les rattrapent, recommencent. Le jeu est rare chez les animaux et signe souvent d'une grande intelligence.",
        "💨 L'encre du poulpe ne sert pas qu'à le cacher. Elle contient des produits chimiques qui désactivent temporairement l'odorat et le goût d'un prédateur — une bombe sensorielle autant qu'un écran de fumée.",
        "🧠 Les poulpes reconnaissent les humains individuellement. Des soigneurs d'aquarium racontent avoir été arrosés d'eau par un poulpe rancunier tandis qu'un autre à côté les accueillait gentiment.",
        "🐚 L'argonaute est un étrange poulpe dont la femelle sécrète elle-même une fine coquille blanche translucide pour porter ses œufs — le seul céphalopode à fabriquer une coquille à l'âge adulte.",
        "💪 Si un poulpe perd un bras à cause d'un prédateur, il peut le faire repousser complètement — nerfs, ventouses et tout. Ça prend quelques mois.",
        "💘 Chez certaines espèces de poulpe, le bras reproducteur du mâle peut SE DÉTACHER de son corps et nager tout seul jusqu'à la femelle. On l'appelle un hectocotyle.",
        "🩱 Les femelles du poulpe à couverture sont jusqu'à 10 000 fois plus lourdes que les mâles. Les tout petits mâles transportent des tentacules de physalie volés comme armes — ils sont immunisés contre le venin.",
        "💤 Des études récentes montrent que les poulpes passent par des phases de sommeil de type paradoxal et changent de couleur pendant leur sommeil — certains scientifiques pensent qu'ils pourraient rêver.",
        "⚡ Un poulpe a environ 500 millions de neurones — à peu près comme un chien — et deux tiers se trouvent dans ses bras, pas dans son cerveau.",
        "🧛 Le vampire des abysses n'est pas un vrai poulpe, mais un proche parent. Il vit dans la « zone de minimum d'oxygène » — une eau si pauvre en oxygène que presque rien d'autre n'y survit — à des kilomètres sous la mer.",
        "🦴 Le bec du poulpe est fait de chitine — la même matière que les exosquelettes d'insectes. Il est assez dur pour casser un crabe, alors que tout le reste du poulpe est tout mou.",
        "👽 Les céphalopodes se sont séparés de notre lignée évolutive il y a environ 600 millions d'années. Les scientifiques les appellent parfois ce qui ressemble le plus à des extraterrestres sur Terre — leur intelligence a évolué complètement à part de la nôtre.",
        "⏳ Le poulpe Dumbo vit si profondément, dans une eau si froide, que son métabolisme est très lent — il peut vivre jusqu'à 24 ans. La plupart des poulpes des eaux peu profondes ne vivent que 1 à 5 ans.",
        "🔍 Un poulpe géant du Pacifique a environ 280 ventouses sur chaque bras, en deux rangées. Ça fait plus de 2 200 ventouses au total — chacune peut goûter, sentir et agripper indépendamment.",
        "☀️ La peau du poulpe contient des opsines — les mêmes protéines sensibles à la lumière que l'on trouve dans les yeux. C'est pourquoi les scientifiques pensent que les poulpes pourraient « voir » les couleurs à travers leur peau, même si leurs vrais yeux ne le peuvent pas.",
        "🐟 Les seiches et les calmars ont une coquille interne (un os de seiche ou une plume). Les poulpes sont les seuls céphalopodes sans aucune coquille — c'est pour ça qu'ils peuvent se glisser dans presque n'importe quel trou.",
        "🦐 Le plus petit poulpe est le pygmée à ventouses étoilées (Octopus wolfi). Adulte, il ne mesure qu'environ 15 millimètres — assez petit pour tenir sur le bout d'un doigt.",
        "🫙 Les poulpes savent ouvrir des bocaux. Pas seulement de l'extérieur — ils peuvent aussi y arriver de l'intérieur. Certains ont même appris en observant un autre poulpe le faire.",
        "🐋 Le bec du poulpe est si dur qu'il survit à la digestion. Les scientifiques le retrouvent intact dans l'estomac des cachalots et s'en servent pour identifier quelle espèce la baleine chassait.",
        "🪨 Les poulpes peuvent changer la TEXTURE de leur peau, pas seulement la couleur. De petites bosses appelées papilles se dressent pour imiter le corail rugueux ou les rochers pointus.",
        "🦾 Chaque bras de poulpe a son propre mini-cerveau en quelque sorte. Même un bras coupé du corps (à ne pas faire) peut encore saisir de la nourriture et la diriger vers la bouche — pendant environ une heure.",
        "📚 « Poulpe » se dit « octopus » en anglais, un mot grec qui veut dire « huit pieds ». Le pluriel correct est « octopuses » ou « octopodes » — PAS « octopi ». Ça sonne bien mais c'est grammaticalement faux, car le mot n'est pas latin.",
        "⏳ Les fossiles de céphalopodes remontent à près de 500 millions d'années. Les poulpes et leurs cousins font partie des plus anciennes lignées animales encore vivantes sur Terre.",
        "👁️ Le poulpe à deux taches de Californie a deux faux « yeux » peints sur son manteau. Si un prédateur attaque les faux yeux, le vrai poulpe a le temps de s'échapper d'un jet.",
        "🛡️ Certains poulpes transportent des cailloux, des coquillages ou des morceaux de varech pour s'en servir comme armure de fortune face à un danger — encore un cas évident d'utilisation d'outils.",
        "💡 Un poulpe nommé Otto, dans un aquarium en Allemagne, arrosait d'eau une lampe de plafond trop brillante jusqu'à la court-circuiter. Les soigneurs pensent que la lumière l'agaçait.",
    ],
}

# Generate greeting clips
for lang, text in INK_GREETINGS.items():
    out = INK_OUT / f'greeting-{lang}.mp3'
    if out.exists():
        print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
        skipped += 1
        continue
    print(f'Generating greeting-{lang} ({len(text)} chars)…', flush=True)
    try:
        data = generate(INK_VOICE_ID, text)
        out.write_bytes(data)
        print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
        total_chars += len(text)
        generated += 1
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', 'replace')[:300]
        print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
    except Exception as e:
        print(f'  ✗ {e}')

# Reward celebrations — Ink's reaction after every completed task. One file
# per line, indexed 1-based to match JS pool order.
INK_CELEBRATIONS = {
    'en': [
        "YESSSSS!! Tentacle #4 is doing the victory wiggle and it will NOT stop!!",
        "BLOOPSNORK!! You did it!! Ink is crying ink-tears of joy right now!!",
        "BY THE GREAT CORAL REEF!! You are a GENIUS EXPLORER!!",
        "SQUIDZOOKS!! My entire space station just lit up!! ALL THE BUTTONS!!",
        "Ink is SO proud he accidentally squirted ink on the telescope. WORTH IT!!",
    ],
    'fr': [
        "OUIIIII!! Le tentacule numéro quatre fait la danse de la victoire et ne s'arrête PLUS!!",
        "BLOOPSNORK!! Tu l'as fait!! Ink pleure des larmes d'encre de joie!!",
        "PAR LE GRAND RÉCIF!! Tu es un GÉNIE EXPLORATEUR!!",
        "CALMAZOUILLE!! Toute la station vient de s'allumer!! TOUS LES BOUTONS!!",
        "Ink est tellement fier qu'il a accidentellement encré le télescope. ÇA VALAIT LE COUP!!",
    ],
}

# Mission-idle humor lines (when Jules pauses mid-homework). Indexed to match
# JS pool order so playback can locate the right clip.
INK_IDLE_LINES = {
    'en': [
        "🦑 ...hello? Is anyone there? One of my tentacles fell asleep waiting...",
        "💭 Ink is counting his tentacles to pass the time. 1... 2... wait, did that one move?",
        "🌊 BLOOP. That was just a bubble. Ink is fine. Very fine. Not bored at all.",
        "👀 Ink is still here. Ink has been here for 47 years apparently.",
        "🐙 Tentacle #3 just submitted a formal complaint about the waiting. HR is involved.",
        "☄️ A comet just flew past the space station. It waved. Ink waved back. With 8 tentacles. It was a lot.",
    ],
    'fr': [
        "🦑 ...allô ? Il y a quelqu'un ? Un de mes tentacules s'est endormi en attendant...",
        "💭 Ink compte ses tentacules pour passer le temps. 1... 2... attends, celui-là a bougé ?",
        "🌊 BLOOP. C'était juste une bulle. Ink va bien. Très bien. Pas du tout ennuyé.",
        "👀 Ink est toujours là. Ink a apparemment attendu 47 ans.",
        "🐙 Le tentacule numéro 3 vient de déposer une plainte officielle. Les RH sont impliqués.",
        "☄️ Une comète vient de passer. Elle a fait signe. Ink a fait signe avec 8 tentacules. C'était beaucoup.",
    ],
}

def _gen_indexed(prefix, pool):
    """Generate one clip per (lang, idx) pair into audio/ink/."""
    global total_chars, generated, skipped
    for lang in ('en', 'fr'):
        for idx, raw in enumerate(pool[lang], start=1):
            clean = EMOJI_RE.sub('', raw).strip()
            out = INK_OUT / f'{prefix}-{idx:02d}-{lang}.mp3'
            if out.exists():
                print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
                skipped += 1
                continue
            print(f'Generating {prefix}-{idx:02d}-{lang} ({len(clean)} chars)…', flush=True)
            try:
                data = generate(INK_VOICE_ID, clean)
                out.write_bytes(data)
                print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
                total_chars += len(clean)
                generated += 1
            except urllib.error.HTTPError as e:
                err = e.read().decode('utf-8', 'replace')[:300]
                print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
            except Exception as e:
                print(f'  ✗ {e}')

_gen_indexed('celebration', INK_CELEBRATIONS)
_gen_indexed('idle', INK_IDLE_LINES)

# Misc static lines (no list, one clip per language).
INK_STATIC_LINES = {
    'venk': {
        'en': "⚠️ OH NO. This problem is TOO hard. Ink is transforming into... VENK! 😈",
        'fr': "⚠️ OH NON. Ce problème est TROP difficile. Ink se transforme en... VENK ! 😈",
    },
    'next-mission': {
        'en': "Great! Next mission!",
        'fr': "Super ! Prochaine mission !",
    },
    'net-error': {
        'en': "🌊 Oops, a bubble blocked the signal! Try again...",
        'fr': "🌊 Oups, une bulle a bloqué le signal ! Réessaie...",
    },
    'resume': {
        'en': "Ink is back! Let's continue the mission!",
        'fr': "Ink est de retour ! On continue la mission !",
    },
}
for key, langs in INK_STATIC_LINES.items():
    for lang, raw in langs.items():
        clean = EMOJI_RE.sub('', raw).strip()
        out = INK_OUT / f'{key}-{lang}.mp3'
        if out.exists():
            print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
            skipped += 1
            continue
        print(f'Generating {key}-{lang} ({len(clean)} chars)…', flush=True)
        try:
            data = generate(INK_VOICE_ID, clean)
            out.write_bytes(data)
            print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
            total_chars += len(clean)
            generated += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', 'replace')[:300]
            print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
        except Exception as e:
            print(f'  ✗ {e}')

# Mood gallery pose lines — Adam voices most moods (since he IS Ink), but
# Venk and Dragon get distinct voices that match their transformation drama.
INK_POSE_LINES = {
    'happy':    {'en': "That's my happy face!",                                                  'fr': "C'est ma tête contente !"},
    'excited':  {'en': "WOOHOO! Excited mode activated!",                                        'fr': "WOUHOU ! Mode excité activé !"},
    'thinking': {'en': "Hmm... let me think about it.",                                          'fr': "Hmm... laisse-moi réfléchir."},
    'sleeping': {'en': "Shhh... I was just taking a nap.",                                       'fr': "Chut... je faisais juste une petite sieste."},
    'victory':  {'en': "YES! We did it!",                                                        'fr': "OUI ! On a réussi !"},
    'venk':     {'en': "Careful. This is my venom form. Do NOT touch.",                          'fr': "Attention. C'est ma forme venimeuse. Ne touche PAS."},
    'dragon':   {'en': "Behold — the legendary dragon-fire form!",                               'fr': "Contemple — la forme légendaire du dragon de feu !"},
}
# Per-mood voice override: Venk = menacing demon, Dragon = epic boss monster.
# All other moods use Ink's main narration voice (Adam) below.
INK_POSE_VOICES = {
    'venk':   'vfaqCOvlrKi4Zp7C2IAm',  # Malyx — Echoey, Menacing and Deep Demon
    'dragon': 'QzD8JR9v8A4kqCDL8XD4',  # Gorex — Vicious & Hungry boss monster
}
for mood, langs in INK_POSE_LINES.items():
    voice = INK_POSE_VOICES.get(mood, INK_VOICE_ID)
    for lang, raw in langs.items():
        clean = EMOJI_RE.sub('', raw).strip()
        out = INK_OUT / f'pose-{mood}-{lang}.mp3'
        if out.exists():
            print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
            skipped += 1
            continue
        print(f'Generating pose-{mood}-{lang} ({len(clean)} chars)…', flush=True)
        try:
            data = generate(voice, clean)
            out.write_bytes(data)
            print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
            total_chars += len(clean)
            generated += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', 'replace')[:300]
            print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
        except Exception as e:
            print(f'  ✗ {e}')

# Engagement transitions — Ink chimes in at key flow moments to keep Jules engaged.
# Some keys are language-fixed (subject buttons that switch language); others
# follow the current S.lang so they get both EN and FR clips.
INK_TRANSITIONS_BILINGUAL = {
    'ready':    {'en': "Ready for some fun homework?",                                            'fr': "Prêt pour des devoirs rigolos ?"},
    'poesie':   {'en': "Time for some poetry!",                                                  'fr': "C'est l'heure de la poésie !"},
    'upload':   {'en': "Take a clear picture of your homework page. Hold the iPad steady and make sure the page is well lit.", 'fr': "Prends une photo bien nette de ta page de devoirs. Tiens l'iPad bien droit et vérifie que la page est bien éclairée."},
    'quest':    {'en': "This is Ink's Quest! Every time you finish your homework, a new friend or sea creature joins my crew. Find them all!",
                 'fr': "C'est la quête d'Ink ! À chaque fois que tu finis tes devoirs, un nouvel ami ou une créature marine rejoint mon équipe. Trouve-les tous !"},
}
# Subject-button transitions are SINGLE-language (the button locks the lang).
INK_TRANSITIONS_SINGLE = {
    'subject-en': {'lang': 'en', 'text': "Alright! Let's do the English homework."},
    'subject-fr': {'lang': 'fr', 'text': "Allez ! On fait les devoirs en français."},
}
for key, langs in INK_TRANSITIONS_BILINGUAL.items():
    for lang, raw in langs.items():
        clean = EMOJI_RE.sub('', raw).strip()
        out = INK_OUT / f'{key}-{lang}.mp3'
        if out.exists():
            print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
            skipped += 1
            continue
        print(f'Generating {key}-{lang} ({len(clean)} chars)…', flush=True)
        try:
            data = generate(INK_VOICE_ID, clean)
            out.write_bytes(data)
            print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
            total_chars += len(clean)
            generated += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', 'replace')[:300]
            print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
        except Exception as e:
            print(f'  ✗ {e}')
for key, info in INK_TRANSITIONS_SINGLE.items():
    raw, lang = info['text'], info['lang']
    clean = EMOJI_RE.sub('', raw).strip()
    out = INK_OUT / f'{key}.mp3'
    if out.exists():
        print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
        skipped += 1
        continue
    print(f'Generating {key} ({len(clean)} chars)…', flush=True)
    try:
        data = generate(INK_VOICE_ID, clean)
        out.write_bytes(data)
        print(f'  → {out.relative_to(ROOT)} ({len(data):,} bytes)')
        total_chars += len(clean)
        generated += 1
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8', 'replace')[:300]
        print(f'  ✗ HTTP {e.code} {e.reason}: {err}')
    except Exception as e:
        print(f'  ✗ {e}')

# Generate fact clips with random intros baked in (deterministic seed so
# re-runs produce stable intro→fact pairings; new facts only affect new clips).
random.seed(42)
for idx, (en, fr) in enumerate(zip(INK_FACTS['en'], INK_FACTS['fr']), start=1):
    for lang, raw in (('en', en), ('fr', fr)):
        intro = random.choice(INK_INTROS[lang])
        clean = EMOJI_RE.sub('', raw).strip()
        text = f'{intro} {clean}'
        out = INK_OUT / f'fact-{idx:02d}-{lang}.mp3'
        if out.exists():
            print(f'  ✓ {out.relative_to(ROOT)} (skipped)')
            skipped += 1
            continue
        print(f'Generating fact-{idx:02d}-{lang} ({len(text)} chars)…', flush=True)
        try:
            data = generate(INK_VOICE_ID, text)
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
