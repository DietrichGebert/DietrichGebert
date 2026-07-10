"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.

Runs daily via GitHub Actions. Stdlib only, no dependencies.
"""
import calendar
import html
import json
import os
import time
import urllib.request
from datetime import date, datetime, timezone

USER = "DietrichGebert"
BIRTHDAY = date(1989, 1, 15)
JOINED_YEAR = 2023  # account creation year, never changes
W = 56  # info column width in characters

ART = r"""
                 ++==---
            +==---------:-:::
          +==------::::::..... .
        *===----:::::...::::..   :#
       +==-=========++++++++==:.  .#
      =--=+*#%%######******++++-:  +
      -=*#%%%%%%#####*******+++=-:.=
      =*%%@@@@%%%######******+++=-:-
      +#%%##*+++*###**+----===+++=--#
      +#%#+===::-+##*=::::::-==++=--=*
    %#*#%#*+*+-=+#%%*=---:---=++++==+=   #
    %#*#%%%%%###%%%%*+++++++***+++=-=+##**
    @#+#%%%%%%%%%%%#*++++***+++++++==*###
     %###%%%%#####++=-=+++**+++++++++
      %%########%%#+++++++**++==+++*
        ##*###**#**++====++*++++++
         *##%#**##*++++++++*+++==*
          *###%%%##******+++++===+
           **##%%%#*****++====-==
         #+#*+++++=====------==++.
         ..%##*+=------:---===++=-.
     #+   :%%%%#*+=----====+++++=-.
 *+    .  :#%%###*++====++++*+++=-
       .  :+######****++*****+++=
          :+**#####************=
           :+***####***##****+:
             -+*##########+==.
               .=*#####*=.
"""

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""


def gh(url, payload=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read() or "{}")


def age(b, t):
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    if t.day >= b.day:
        days = t.day - b.day
    else:
        pm_year, pm = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        days = calendar.monthrange(pm_year, pm)[1] - b.day + t.day
    return years, months, days


def fetch_stats():
    yr_aliases = "\n".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
        " { totalCommitContributions restrictedContributionsCount }"
        for y in range(JOINED_YEAR, datetime.now(timezone.utc).year + 1)
    )
    query = f"""
    query {{
      user(login: "{USER}") {{
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER) {{
          totalCount
          nodes {{ name stargazerCount isFork }}
        }}
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
          totalCount
        }}
        {yr_aliases}
      }}
    }}"""
    _, resp = gh("https://api.github.com/graphql", {"query": query})
    u = resp["data"]["user"]
    commits = sum(
        v["totalCommitContributions"] + v["restrictedContributionsCount"]
        for k, v in u.items() if k.startswith("y")
    )
    stats = {
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "commits": commits,
    }
    stats.update(loc([n["name"] for n in u["repositories"]["nodes"] if not n["isFork"]]))
    return stats


def loc(repo_names):
    add = rem = 0
    for name in repo_names:
        for attempt in range(6):
            status, data = gh(f"https://api.github.com/repos/{USER}/{name}/stats/contributors")
            if status == 200 and isinstance(data, list):
                for c in data:
                    if c.get("author", {}).get("login") == USER:
                        add += sum(w["a"] for w in c["weeks"])
                        rem += sum(w["d"] for w in c["weeks"])
                break
            time.sleep(3)  # 202 = stats still being computed server-side
    return {"loc_add": add, "loc_del": rem, "loc": add - rem}


PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "art": "#8b949e", "h": "#58a6ff",
             "k": "#ffa657", "v": "#c9d1d9", "d": "#484f58", "g": "#3fb950", "r": "#f85149"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "art": "#57606a", "h": "#0969da",
              "k": "#953800", "v": "#24292f", "d": "#afb8c1", "g": "#1a7f37", "r": "#cf222e"},
}


def kv(key, val, width=W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]


def kv2(k1, v1, k2, v2):
    left = kv(k1, v1, 30)
    return left + [(" | ", "d")] + kv(k2, v2, 23)


def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (W - len(label)), "d")]


def info_lines(s):
    y, m, d = age(BIRTHDAY, date.today())
    n = lambda x: f"{x:,}"
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (W - len(USER) - 8), "d")],
        [],
        kv("OS", "Windows, macOS"),
        kv("Uptime", f"{y} years, {m} months, {d} days"),
        kv("Host", "Trimble"),
        kv("Kernel", "Lead GenAI Engineer"),
        kv("IDE", "Claude Code, Cursor, VS Code"),
        [],
        kv("Languages.Programming", "Python, Java, C#, TypeScript"),
        kv("Languages.Real", "German, English, Russian"),
        kv("Hobbies", "Fishing"),
        [],
        rule("Contact"),
        kv("Email", "dietrichgebert@gmail.com"),
        kv("LinkedIn", "in/dietrich-gebert-b3a314a9"),
        [],
        rule("GitHub Stats"),
        kv2("Repos", f"{s['repos']} {{Contributed: {s['contributed']}}}", "Stars", n(s["stars"])),
        kv2("Commits", n(s["commits"]), "Followers", n(s["followers"])),
        [("Lines of Code: ", "k"), (n(s["loc"]), "v"), (" ( ", "d"),
         (n(s["loc_add"]) + "++", "g"), (", ", "d"), (n(s["loc_del"]) + "--", "r"), (" )", "d")],
    ]


def render(mode, stats):
    p = PALETTES[mode]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="500" viewBox="0 0 840 500" '
        f'font-family="Consolas, Menlo, monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="839" height="499" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    for i, line in enumerate(ART.strip("\n").split("\n")):
        out.append(f'<text x="25" y="{40 + i * 15}" fill="{p["art"]}" xml:space="preserve">{html.escape(line)}</text>')
    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(f'<text x="390" y="{45 + i * 21}" xml:space="preserve">{spans}</text>')
    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert age(date(1989, 1, 15), date(2026, 7, 10)) == (37, 5, 25)
    assert age(date(2000, 3, 31), date(2026, 4, 1)) == (26, 0, 1)
    assert age(date(2000, 1, 1), date(2026, 1, 1)) == (26, 0, 0)
    assert len("".join(t for t, _ in kv("OS", "Windows, macOS"))) == W


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("stats:", stats)
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as f:
            f.write(render(mode, stats))
    print("wrote dark_mode.svg, light_mode.svg")
