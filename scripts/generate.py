"""Generate the Paper Signal profile artwork using GitHub's public REST API.

    python scripts/generate.py          # live public data
    python scripts/generate.py --demo   # deterministic offline preview
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PAPER = "#f3eedf"
INK = "#171717"
BLUE = "#2348f5"
CORAL = "#ff6559"
LIME = "#c8ef54"
MUTED = "#6d685f"

DEMO = {
    "public_repos": 86,
    "followers": 34,
    "following": 18,
    "stars": 119,
    "languages": [["TypeScript", 36], ["JavaScript", 28], ["Python", 17], ["CSS", 11], ["Other", 8]],
    "repos": [
        {"name": "Zeropoint-website", "description": "Digital home for a product-focused team.", "language": "TypeScript", "stargazers_count": 42},
        {"name": "Jenesyx-Website", "description": "Selected work, experiments and ideas.", "language": "JavaScript", "stargazers_count": 31},
        {"name": "TodoList", "description": "A focused task system with clean UX.", "language": "TypeScript", "stargazers_count": 27},
    ],
}


def config() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def api(url: str) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "paper-signal-profile"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def collect(username: str, featured: list[str]) -> dict:
    user = api(f"https://api.github.com/users/{username}")
    repos = api(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated")
    if not isinstance(user, dict) or not isinstance(repos, list):
        raise RuntimeError("Unexpected response from GitHub")
    original = [repo for repo in repos if not repo.get("fork")]
    names = {repo.get("name", "").lower(): repo for repo in original}
    selected = [names[name.lower()] for name in featured if name.lower() in names]
    selected_ids = {repo.get("id") for repo in selected}
    ranked = sorted(original, key=lambda repo: (repo.get("stargazers_count", 0), repo.get("updated_at", "")), reverse=True)
    selected.extend(repo for repo in ranked if repo.get("id") not in selected_ids and len(selected) < 3)
    counts: dict[str, int] = {}
    for repo in original:
        language = repo.get("language")
        if language:
            counts[language] = counts.get(language, 0) + 1
    return {
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "stars": sum(repo.get("stargazers_count", 0) for repo in original),
        "languages": sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5],
        "repos": selected[:3],
    }


def short(value: object, size: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= size else text[: size - 1].rstrip() + "…"


def styles() -> str:
    return """.serif{font-family:Georgia,'Times New Roman',serif;fill:__INK__}.sans{font-family:'Trebuchet MS',sans-serif;fill:__INK__}.mono{font-family:ui-monospace,Consolas,monospace;fill:__MUTED__}.caps{font-size:10px;font-weight:700;letter-spacing:2px}.intro{animation:enter .85s cubic-bezier(.32,.72,0,1) both}.mark{transform-origin:center;animation:turn 12s cubic-bezier(.32,.72,0,1) infinite}.wipe{transform-origin:left;animation:wipe .9s cubic-bezier(.32,.72,0,1) both}@keyframes enter{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@keyframes turn{50%{transform:rotate(8deg)}}@keyframes wipe{from{transform:scaleX(0)}to{transform:scaleX(1)}}@media(prefers-reduced-motion:reduce){.intro,.mark,.wipe{animation:none}}""".replace("__INK__", INK).replace("__MUTED__", MUTED)


def cover_svg(cfg: dict, stats: dict) -> str:
    service_nodes = []
    for index, service in enumerate(cfg["services"][:4]):
        x = 49 + (index % 2) * 215
        y = 265 + (index // 2) * 32
        service_nodes.append(f'<text x="{x}" y="{y}" class="sans" font-size="11" font-weight="700"><tspan fill="{BLUE if index % 2 == 0 else CORAL}">0{index + 1}.</tspan> {escape(service)}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="340" viewBox="0 0 900 340" role="img" aria-label="Paper Signal profile cover for {escape(cfg['name'])}">
<defs><style>{styles()}</style><pattern id="grain" width="17" height="17" patternUnits="userSpaceOnUse"><circle cx="2" cy="4" r=".45" fill="{INK}" opacity=".14"/><circle cx="12" cy="13" r=".35" fill="{INK}" opacity=".1"/></pattern></defs>
<rect width="900" height="340" rx="5" fill="{PAPER}"/><rect width="900" height="340" rx="5" fill="url(#grain)"/><path d="M25 39h850M25 315h850" stroke="{INK}" stroke-width="1.4"/>
<text x="26" y="27" class="sans caps">PAPER SIGNAL / INDEPENDENT PROFILE</text><text x="874" y="27" text-anchor="end" class="sans caps">ED. {escape(cfg['edition'])} · @{escape(cfg['username'].upper())}</text>
<g class="intro"><text x="39" y="111" class="serif" font-size="74" font-weight="700" letter-spacing="-4">{escape(cfg['name'])}</text><rect x="42" y="129" width="420" height="8" fill="{BLUE}" class="wipe"/><text x="42" y="169" class="sans" font-size="16" font-weight="700">{escape(cfg['role'])}</text><text x="42" y="199" class="serif" font-size="18" font-style="italic">“{escape(short(cfg['statement'], 54))}”</text><text x="42" y="230" class="mono" font-size="11">{escape(cfg['location'])}  /  {escape(cfg['website'])}</text>{''.join(service_nodes)}</g>
<path d="M548 71h309v225H548z" fill="{INK}"/><path d="M571 94h263v179H571z" fill="{CORAL}"/>
<g class="mark"><circle cx="703" cy="184" r="72" fill="{LIME}"/><path d="M648 188c31-72 78-76 111-12M647 201c30 32 75 39 112 4" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/><text x="703" y="199" text-anchor="middle" class="serif" font-size="58" font-weight="700">{escape(cfg['monogram'])}</text></g>
<text x="568" y="290" class="sans caps" fill="{PAPER}"><tspan fill="{PAPER}">{stats['public_repos']} REPOS · {stats['stars']} STARS · {stats['followers']} READERS</tspan></text>
<rect x="744" y="56" width="96" height="25" rx="13" fill="{BLUE}"/><text x="792" y="73" text-anchor="middle" class="sans caps" font-size="8" fill="{PAPER}"><tspan fill="{PAPER}">NEW WORK</tspan></text>
</svg>'''


def folio_svg(cfg: dict, stats: dict) -> str:
    total = max(1, sum(count for _, count in stats["languages"]))
    language_nodes = []
    cursor = 0
    palette = [BLUE, CORAL, LIME, "#7b5cff", "#d5cdb8"]
    for index, (language, count) in enumerate(stats["languages"][:5]):
        width = max(26, round(400 * count / total))
        language_nodes.append(f'<rect x="{39 + cursor}" y="157" width="{width}" height="26" fill="{palette[index]}" class="wipe" style="animation-delay:{index * .08:.2f}s"/><text x="{47 + cursor}" y="174" class="sans" font-size="9" font-weight="700" fill="{PAPER}"><tspan fill="{PAPER if index != 2 else INK}">{escape(short(language, 12))}</tspan></text>')
        cursor += width

    repo_nodes = []
    for index, repo in enumerate(stats["repos"][:3]):
        y = 230 + index * 70
        color = [BLUE, CORAL, LIME][index]
        repo_nodes.append(f'<g class="intro" style="animation-delay:{.1 + index * .1:.2f}s"><text x="40" y="{y}" class="serif" font-size="25" font-weight="700">0{index + 1}</text><line x1="85" y1="{y - 8}" x2="125" y2="{y - 8}" stroke="{color}" stroke-width="6"/><text x="143" y="{y - 2}" class="sans" font-size="14" font-weight="700">{escape(short(repo.get('name'), 28))}</text><text x="143" y="{y + 18}" class="mono" font-size="10">{escape(short(repo.get('description') or 'No description yet', 54))}</text><text x="449" y="{y + 18}" text-anchor="end" class="mono" font-size="9">★ {repo.get('stargazers_count', 0)} / {escape(repo.get('language') or 'Mixed')}</text></g>')

    metrics = [("REPOSITORIES", stats["public_repos"]), ("TOTAL STARS", stats["stars"]), ("FOLLOWERS", stats["followers"])]
    metric_nodes = []
    for index, (label, value) in enumerate(metrics):
        y = 116 + index * 90
        metric_nodes.append(f'<text x="560" y="{y}" class="sans caps" fill="{PAPER}"><tspan fill="{PAPER}">{label}</tspan></text><text x="812" y="{y + 34}" text-anchor="end" class="serif" font-size="48" font-weight="700" fill="{PAPER}"><tspan fill="{PAPER}">{value}</tspan></text><line x1="560" y1="{y + 48}" x2="812" y2="{y + 48}" stroke="{PAPER}" opacity=".22"/>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="460" viewBox="0 0 900 460" role="img" aria-label="Paper Signal GitHub folio for {escape(cfg['username'])}">
<defs><style>{styles()}</style><pattern id="dots" width="13" height="13" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{INK}" opacity=".16"/></pattern></defs>
<rect width="900" height="460" rx="5" fill="{PAPER}"/><rect x="515" width="385" height="460" fill="{INK}"/><rect x="515" width="385" height="460" fill="url(#dots)" opacity=".6"/>
<text x="39" y="47" class="sans caps">01 / WORK INDEX</text><text x="476" y="47" text-anchor="end" class="mono" font-size="10">LIVE GITHUB EDITION</text><line x1="39" y1="62" x2="476" y2="62" stroke="{INK}"/>
<text x="39" y="105" class="serif" font-size="35" font-weight="700">Tools, languages &amp; work.</text><text x="39" y="133" class="mono" font-size="10">Repository language mix — by project count</text>{''.join(language_nodes)}{''.join(repo_nodes)}
<text x="548" y="47" class="sans caps" fill="{LIME}"><tspan fill="{LIME}">02 / NUMBERS DESK</tspan></text><line x1="548" y1="62" x2="829" y2="62" stroke="{LIME}"/>{''.join(metric_nodes)}
<rect x="548" y="384" width="281" height="43" fill="{LIME}"/><text x="564" y="402" class="sans caps">CURRENT STATUS</text><text x="564" y="418" class="sans" font-size="11" font-weight="700">{escape(short(cfg['availability'], 38))}</text>
<text x="39" y="433" class="mono" font-size="9">Generated directly from GitHub public data · no paid card service</text>
</svg>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="use deterministic preview data")
    args = parser.parse_args()
    cfg = config()
    username = os.environ.get("GH_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or cfg["username"]
    cfg["username"] = username
    if args.demo:
        stats = DEMO
    else:
        try:
            stats = collect(username, cfg.get("featured_repos", []))
        except (urllib.error.URLError, RuntimeError) as exc:
            raise SystemExit(f"GitHub data request failed: {exc}. Use --demo for an offline preview.")
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "cover.svg").write_text(cover_svg(cfg, stats), encoding="utf-8")
    (ASSETS / "folio.svg").write_text(folio_svg(cfg, stats), encoding="utf-8")
    print(f"Generated Paper Signal assets for @{username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
