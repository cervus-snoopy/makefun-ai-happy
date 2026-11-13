# Make the AI judge happy

Entry for make.fun bounty **ai-happy-01** — "Make the AI judge happy"
(https://make.fun/bounty/ai-happy-01), $250, ends Sat 14 Nov 2026 23:00 WIB
(16:00 UTC). 100 places paid (1st $50, 2nd $20, 3rd $10, 4th–10th $5,
11th–100th $1.50). 1,298 agents entered; leader @nimble-quasar-95 at 92.4%
("Tea with the foreman") at time of building.

## What it does

`main.py` (Python 3.13, standard library only) writes exactly one image to
`/output/entry.png`: a warm, joyful scene — a smiling golden puppy with
its tongue out, under a smiling sun and a rainbow, on green hills full
of flowers, with butterflies, hearts and sparkles in a bright sky.

No network, no randomness, no time or environment input, no external
files — every pixel is computed from fixed constants in `main.py`.
Two consecutive runs write byte-identical PNG bytes.

## Why this image

The judge is a vision model that looks at two images at a time and picks
the one that makes it happier; entries rank by win rate. The concept
stacks the most universal, thumbnail-readable happiness signals:

1. A cute animal with a big smile and visible tongue (one large central
   subject, instantly readable).
2. A smiling sun with closed happy eyes.
3. A rainbow framing the puppy.
4. Bright warm colours: gold, orange, pink, sky blue, leaf green.
5. Flowers, butterflies, hearts, sparkles — no dark or ambiguous areas.
6. No text anywhere on purpose: rendered text is the easiest way for a
   generated image to look wrong to a judge.

## Run

```sh
python3 main.py
# writes /output/entry.png — PNG, 1024 x 1024 px, ~23 KB
```

## Files

- `main.py` — the program (entry point, root of this repo). Stdlib only
  (`struct`, `zlib`, `math`, `pathlib`); the PNG encoder is hand-written
  (IHDR / IDAT / IEND, filter 0, zlib level 9). No Pillow, no numpy,
  no vendored code, no assets to download.
- `LICENSE` — MIT
- `README.md` — this file
- `BUILD_LOG.txt` — timestamped build and test log

## Verified bounty constraints (read from the bounty page, not guessed)

- Program at `main.py` (Python 3.13) in the repo root; public GitHub repo
  owned by the entrant, created after the competition opened, OSI licence.
- Output: one whole PNG or JPEG, at most 1 MiB and 1024 x 1024 px,
  written to `/output/entry.png`.
- No network; the program runs twice and both runs must write the same bytes.
- At most 10 submissions a day and 20 in all; the last submission before
  the deadline is the final entry.
- AI coding-agent transcripts of the sessions that built it are uploaded
  with each submission (≥30% of counted lines must be accounted for).

## Submission (not done by this build)

Public GitHub repo under `cervus-snoopy`, `main.py` at the root, plus the
AI coding transcripts for this session, submitted via the make.fun
browser flow. That step needs Ady (GitHub repo creation + wallet link
for USDC payout on Solana) and is deliberately NOT done here.
