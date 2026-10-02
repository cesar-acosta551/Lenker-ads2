#!/usr/bin/env python3
"""Build all Lenker ads from source/copy.json + source/crops.json + source/images.

Outputs
  docs/ads/<SET>_<WxH>/{bg.jpg, button.html, link.html}   looping ads (review site, social export)
  docs/index.html                                         review page (GitHub Pages: /docs)
  dist/google-html5/<SET>_<WxH>_<button|link>.zip         Google Display HTML5 (<150 KB, one run, holds last frame)

Usage:  python3 build/build.py            (everything)
        python3 build/build.py --no-zip   (skip the Google ZIPs)
"""
import io, json, re, shutil, sys, zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC, DOCS, DIST = ROOT / "source", ROOT / "docs", ROOT / "dist"
COPY = json.loads((SRC / "copy.json").read_text())
CROPS = json.loads((SRC / "crops.json").read_text())
BRAND = COPY["brand"]
FONT = (DOCS / "assets" / "Inter.woff2")
GOOGLE_LIMIT = 145 * 1024          # stay safely under Google's 150 KB cap
EASE = "cubic-bezier(.2,.7,.2,1)"

# size -> layout (values taken from the approved display-ad mockup)
L = {
 "300x250":  dict(w=300,h=250,pad="16px",logo=14,ls=".2em",hl=19,hlh=1.2,hls="-.01em",sub=16,g1=12,g2=6,cta=14,cpad="7px 14px",cr=4,grad=(38,78)),
 "336x280":  dict(w=336,h=280,pad="20px",logo=14,ls=".2em",hl=23,hlh=1.15,hls="-.01em",sub=16,g1=12,g2=6,cta=14,cpad="7px 14px",cr=4,grad=(38,78)),
 "160x600":  dict(w=160,h=600,pad="20px 12px",logo=14,ls=".16em",hl=19,hlh=1.2,hls="-.01em",sub=16,g1=16,g2=8,cta=14,cpad="7px 14px",cr=4,grad=(40,64)),
 "300x600":  dict(w=300,h=600,pad="24px",logo=14,ls=".2em",hl=33,hlh=1.1,hls="-.015em",sub=16,g1=20,g2=10,cta=14,cpad="8px 16px",cr=4,grad=(40,66)),
 "1080x1080":dict(w=1080,h=1080,pad="72px",logo=42,ls=".2em",hl=84,hlh=1.1,hls="-.015em",sub=48,g1=48,g2=24,cta=42,cpad="22px 44px",cr=12,grad=(46,82)),
 "1200x628": dict(w=1200,h=628,pad="56px 72px",logo=42,ls=".2em",hl=69,hlh=1.1,hls="-.015em",sub=48,g1=32,g2=16,cta=42,cpad="18px 40px",cr=10,grad=(0,0),wide=True),
}
GOOGLE_SIZES = {"300x250", "336x280", "160x600", "300x600"}
OUT_PX = {"300x250":(600,500),"336x280":(672,560),"160x600":(320,1200),"300x600":(600,1200),"1080x1080":(1080,1080),"1200x628":(1200,628)}

def esc(t): return t.replace("&","&amp;").replace("<","&lt;").replace("'","&#39;")

def crop(set_key, size, quality=82, scale=1.0):
    img = Image.open(SRC / "images" / COPY["sets"][set_key]["image"]).convert("RGB")
    W, H = img.size
    xc, y0, hc = CROPS[set_key][size]
    ow, oh = OUT_PX[size]
    wc = hc * ow / oh
    x0 = max(0, min(W - wc, xc - wc / 2)); y0 = max(0, min(H - hc, y0))
    out = img.crop((round(x0), round(y0), round(x0 + wc), round(y0 + hc))).resize((round(ow*scale), round(oh*scale)), Image.LANCZOS)
    buf = io.BytesIO(); out.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()

def fit_google(set_key, size):
    """Smallest-loss JPEG that keeps image + font + html under the Google limit."""
    budget = GOOGLE_LIMIT - FONT.stat().st_size - 6 * 1024
    for scale in (1.0, .85, .7):
        for q in (74, 66, 58, 50, 42):
            data = crop(set_key, size, q, scale)
            if len(data) <= budget: return data
    return data

def words(headline):
    """-> list of (word, is_accent)"""
    out, acc = [], False
    for w in headline.split(" "):
        if w.startswith("*"): acc, w = True, w[1:]
        end = w.endswith("*")
        if end: w = w[:-1]
        out.append((w, acc))
        if end: acc = False
    return out

def ad_html(set_key, size, variant, loop, font_url, bg_url="bg.jpg"):
    S = COPY["sets"][set_key]; cfg = L[size]; txt = S[COPY["size_length"][size]]
    ws = words(txt["headline"]); n = len(ws)
    it = "infinite" if loop else "1"
    wide = cfg.get("wide", False)
    hl = " ".join(
        f'<span class="w{" a" if a else ""}" style="animation-delay:{0.40+0.09*i:.2f}s">{esc(w)}</span>' for i, (w, a) in enumerate(ws))
    sub_d = max(1.35, 0.40 + 0.09 * n + 0.30); cta_d = sub_d + 0.45
    s0, e0 = cfg["grad"]
    if wide:
        scrim = "linear-gradient(to bottom,rgba(16,32,46,.5) 0%,rgba(16,32,46,0) 22%),linear-gradient(to right,rgba(24,46,64,.94) 0%,rgba(28,52,72,.86) 30%,rgba(38,68,90,0) 56%)"
        block_extra = "max-width:50%;"
    else:
        scrim = f"linear-gradient(to bottom,rgba(16,32,46,.6) 0%,rgba(16,32,46,0) 24%),linear-gradient(to top,rgba(30,55,75,.94) 0%,rgba(34,60,82,.86) {s0}%,rgba(38,68,90,0) {e0}%)"
        block_extra = ""
    if loop:
        kf = ("@keyframes adIn{0%{opacity:0;transform:translateY(.45em)}7%{opacity:1;transform:none}90%{opacity:1;transform:none}96%,100%{opacity:0;transform:none}}"
              "@keyframes adPop{0%{opacity:0;transform:scale(.85)}5%{opacity:1;transform:scale(1.04)}7%{transform:scale(1)}40%{transform:scale(1)}43%{transform:scale(1.06)}46%{transform:scale(1)}90%{opacity:1}96%,100%{opacity:0}}"
              "@keyframes adBg{0%{transform:scale(1.1)}92%{transform:scale(1)}100%{transform:scale(1.1)}}")
    else:  # Google: play once, hold the final frame
        kf = ("@keyframes adIn{0%{opacity:0;transform:translateY(.45em)}7%{opacity:1;transform:none}100%{opacity:1;transform:none}}"
              "@keyframes adPop{0%{opacity:0;transform:scale(.85)}5%{opacity:1;transform:scale(1.04)}7%{transform:scale(1)}40%{transform:scale(1)}43%{transform:scale(1.06)}46%{transform:scale(1)}100%{opacity:1;transform:scale(1)}}"
              "@keyframes adBg{0%{transform:scale(1.1)}100%{transform:scale(1)}}")
    cta_style = (f"background:{BRAND['lime']};color:#1E3747;padding:{cfg['cpad']};border-radius:{cfg['cr']}px;"
                 if variant == "button" else
                 f"color:{BRAND['lime']};text-decoration:underline;text-decoration-thickness:.08em;text-underline-offset:.28em;")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="ad.size" content="width={cfg['w']},height={cfg['h']}">
<title>Lenker {set_key} {size} {variant}</title>
<script>var clickTag = "{BRAND['click_url']}";</script>
<style>
@font-face{{font-family:'Inter';font-weight:100 900;font-style:normal;src:url('{font_url}') format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{cfg['w']}px;height:{cfg['h']}px;overflow:hidden;background:{BRAND['navy']};font-family:'Inter',-apple-system,Helvetica,Arial,sans-serif}}
{kf}
.ad{{position:relative;width:{cfg['w']}px;height:{cfg['h']}px;overflow:hidden;background:{BRAND['navy']};cursor:pointer}}
.bg{{position:absolute;inset:0;background:url('{bg_url}') center/cover no-repeat;transform-origin:60% 40%;animation:adBg 9s ease-out 0s {it} both}}
.scrim{{position:absolute;inset:0;background:{scrim}}}
.ui{{position:absolute;inset:0;padding:{cfg['pad']};display:flex;flex-direction:column;justify-content:space-between}}
.logo{{font-size:{cfg['logo']}px;font-weight:800;letter-spacing:{cfg['ls']};color:#F4F1EA;animation:adIn 9s {EASE} .1s {it} both}}
.stack{{display:flex;flex-direction:column;gap:{cfg['g1']}px;{block_extra}}}
.copy{{display:flex;flex-direction:column;gap:{cfg['g2']}px}}
.hl{{font-size:{cfg['hl']}px;line-height:{cfg['hlh']};font-weight:700;letter-spacing:{cfg['hls']};color:#F4F1EA;text-wrap:balance}}
.w{{display:inline-block;animation:adIn 9s {EASE} 0s {it} both}}
.a{{color:{BRAND['lime']}}}
.sub{{font-size:{cfg['sub']}px;line-height:1.3;color:#C3D1DC;text-wrap:balance;animation:adIn 9s {EASE} {sub_d:.2f}s {it} both}}
.cta{{align-self:flex-start;font-size:{cfg['cta']}px;font-weight:700;transform-origin:left center;{cta_style}animation:adPop 9s {EASE} {cta_d:.2f}s {it} both}}
</style></head>
<body>
<div class="ad" id="ad" onclick="window.open(window.clickTag,'_blank')">
  <div class="bg"></div><div class="scrim"></div>
  <div class="ui">
    <div class="logo">{BRAND['logo']}</div>
    <div class="stack">
      <div class="copy"><div class="hl">{hl}</div><div class="sub">{esc(txt['sub'])}</div></div>
      <div class="cta">{esc(S['cta'])}</div>
    </div>
  </div>
</div>
</body></html>
"""

def build_ads(zips=True):
    if (DOCS / "ads").exists(): shutil.rmtree(DOCS / "ads")
    if zips:
        for f in (DIST / "google-html5").glob("*.zip"): f.unlink()
    report = []
    for k in COPY["sets"]:
        for size in L:
            folder = DOCS / "ads" / f"{k}_{size}"; folder.mkdir(parents=True)
            google = size in GOOGLE_SIZES
            img = fit_google(k, size) if google else crop(k, size, 82)
            (folder / "bg.jpg").write_bytes(img)
            for variant in ("button", "link"):
                (folder / f"{variant}.html").write_text(ad_html(k, size, variant, True, "../../assets/Inter.woff2"))
                if zips and google:
                    z = DIST / "google-html5" / f"{k}_{size}_{variant}.zip"
                    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr("index.html", ad_html(k, size, variant, False, "Inter.woff2"))
                        zf.writestr("bg.jpg", img); zf.write(FONT, "Inter.woff2")
                    report.append((z.name, z.stat().st_size))
    return report

def review_page():
    nav = "".join(f'<a href="#set-{k}">Set {k} · {v["name"]}</a>' for k, v in COPY["sets"].items())
    parts = []
    for k, S in COPY["sets"].items():
        cards = []
        for size, cfg in L.items():
            for variant in ("button", "link"):
                z = 0.5 if cfg["w"] > 700 else 1
                cards.append(
                  f'<figure><figcaption>{k} · {size} · {variant}</figcaption>'
                  f'<div class="frame" style="width:{cfg["w"]*z:.0f}px;height:{cfg["h"]*z:.0f}px">'
                  f'<iframe src="ads/{k}_{size}/{variant}.html" width="{cfg["w"]}" height="{cfg["h"]}" scrolling="no" loading="lazy" '
                  f'style="transform:scale({z});transform-origin:0 0;border:0"></iframe></div></figure>')
        parts.append(f'<section id="set-{k}"><h2>Set {k} · {S["name"]}</h2><p>{S["note"]} CTA: <b>{S["cta"]}</b></p><div class="grid">{"".join(cards)}</div></section>')
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lenker display ads · review</title>
<style>@font-face{{font-family:'Inter';font-weight:100 900;src:url('assets/Inter.woff2') format('woff2')}}
body{{margin:0;padding:40px;background:#F8F5F1;color:#26445A;font-family:'Inter',-apple-system,Helvetica,sans-serif}}
h1{{font-size:30px;margin:0 0 8px}} h2{{font-size:26px;margin:0 0 6px}} p{{color:#5A6B78;max-width:880px;margin:0 0 16px}}
nav{{position:sticky;top:0;background:#F8F5F1;padding:12px 0;display:flex;gap:10px;flex-wrap:wrap;z-index:5}}
nav a{{background:#26445A;color:#F4F1EA;text-decoration:none;font-weight:700;font-size:14px;padding:8px 14px;border-radius:999px}}
section{{border-top:2px solid #26445A;padding:24px 0 40px}} .grid{{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start}}
figure{{margin:0}} figcaption{{font-size:13px;color:#5A6B78;margin-bottom:6px}} .frame{{overflow:hidden;background:#26445A}}</style></head>
<body><h1>Lenker display ads · review</h1>
<p>Four copy sets on the 400-people idea. Each ad loops every 9 seconds. Source: <code>source/copy.json</code>. Rebuild with <code>python3 build/build.py</code>.</p>
<nav>{nav}</nav>{"".join(parts)}</body></html>"""
    (DOCS / "index.html").write_text(html)

if __name__ == "__main__":
    zips = "--no-zip" not in sys.argv
    rep = build_ads(zips); review_page()
    print(f"built {len(list((DOCS/'ads').glob('*/button.html')))*2} looping ads + review page")
    if zips:
        worst = max(rep, key=lambda r: r[1])
        print(f"{len(rep)} Google ZIPs, largest {worst[0]} = {worst[1]/1024:.0f} KB (limit 150 KB)")
