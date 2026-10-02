# Lenker display ads

Four copy sets built on the "This ad is for about 400 people" idea, in six sizes, with retro-futurist imagery.

| Set | Idea | Image |
|---|---|---|
| A | The Number: "This ad is for about 400 people." | Launch Complex crowd |
| B | We did our job | Hangar |
| C | We found you | Summons at the mailbox |
| D | No wasted impressions | Planning room |

## Quick start

```bash
pip install -r requirements.txt     # Pillow
python3 build/build.py              # builds everything
npm install && npm run export:social   # optional: PNGs for Meta and LinkedIn (uses your Chrome)
```

Then open `docs/index.html` to review all 48 ads.

## Where things live

```
source/copy.json      all headlines, subs and CTAs per set and length (edit copy here)
source/crops.json     how each image is cropped per ad size
source/images/        the four approved, retouched images (tracked with Git LFS)
build/build.py        generates everything below
docs/                 review site (publish with GitHub Pages: branch main, folder /docs)
dist/google-html5/    one ZIP per Google Display ad (limit 150 KB, plays once, holds last frame)
dist/social-static/   PNGs for Meta and LinkedIn (1080x1080, 1200x628)
```

## Common changes

- **Change a line of copy:** edit `source/copy.json`, run `python3 build/build.py`. Put `*asterisks*` around the lime accent word.
- **Swap an image:** replace the file in `source/images/` keeping the same name, rebuild. If the subject moves, adjust `source/crops.json` (`[x_centre, y_top, crop_height]` in source pixels).
- **Click-through URL:** `brand.click_url` in `copy.json`. It is a placeholder (`https://lenker.com`). Google Ads replaces `clickTag` at serve time, so check it matches your campaign setup.

## Platform notes

- **Google Display (300x250, 336x280, 160x600, 300x600):** upload the ZIPs. Each runs once (9 s) and holds the final frame. No external requests.
- **Meta and LinkedIn (1080x1080, 1200x628):** upload the PNGs. HTML5 is not accepted.
- **Rights:** the images are AI-generated. Confirm usage rights and any disclosure requirements before publishing. Keep this repository private until then.

## Publishing the review site

Repo Settings, Pages, Source: `main`, folder `/docs`. Private repos need a paid GitHub plan for Pages.
