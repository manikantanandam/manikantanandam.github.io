#!/usr/bin/env python3
"""Our own ATS score for the generated resume PDFs in resumes/ (no standard ATS score exists).

Checks are distilled from public ATS guidance (Jobscan-style searchability / hard skills / recruiter tips,
Workday/Greenhouse parsing notes, German Lebenslauf norms) and grouped into weighted categories. Prints one
final score per resume, a category x resume table, and the fixes worth the most points.
Needs poppler (pdftotext, pdfinfo, pdfimages, pdffonts).

Usage: python3 resume-builder/ats_check.py [--min 89] [--jd job.txt] [--json-dir DIR] [--readme] [--baseline scores.json] [--comment out.md] [india|intl|de ...]
--min gates the Parseability category (the part our template controls), not the final score.
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter

import yaml

import build

STOP = set("""a an and are as at be by for from has have in is it of on or our that the their this to with you your
we will can who what when where which about all any more most other such than then them they were work
experience years year team teams strong ability etc using use used must should including include able
looking join role candidate responsibilities requirements skills knowledge good new""".split())
DATE = re.compile(r"(\d{2}/\d{4}|[A-Z][a-z]{2} \d{4})\s*-\s*(\d{2}/\d{4}|[A-Z][a-z]{2} \d{4}|Present|heute)")
IRREGULAR = set("built led ran wrote made grew began drove took set won taught".split())
WEAK = re.compile(r"\b(responsible for|worked on|helped|various|duties included|i|my|me)\b", re.I)
STD_HEADINGS = {
    "en": {"summary", "professional summary", "profile", "skills", "technical skills", "experience",
           "work experience", "professional experience", "projects", "selected projects", "education"},
    "de": {"profil", "kurzprofil", "kenntnisse", "fähigkeiten", "berufserfahrung", "projekte", "ausbildung"},
}
# Category weights in the final score (sum 100).
CATEGORIES = [("Parseability", 15), ("Structure & headings", 10), ("Contact info", 10),
              ("Experience & dates", 15), ("Keywords & skills", 20), ("Impact & wording", 20),
              ("Length", 5), ("Market fit", 5)]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def ym(v):
    """'2025-08' / date / 'present' -> months since year 0."""
    if str(v).lower() == "present":
        return 9999 * 12
    y, m = str(v).split("-")[:2]
    return int(y) * 12 + int(m)


def score(target, pdf):
    """Returns ({category: [(check, weight, fraction 0..1, fix hint)]}, text)."""
    d = build.resolve(target)
    text = run(["pdftotext", "-layout", pdf, "-"])
    low, lines, words = text.lower(), [l for l in text.splitlines() if l.strip()], len(text.split())
    en = d["lang"] == "en"
    info = run(["pdfinfo", pdf])
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    size = (re.search(r"Page size:.*\((\w+)\)", info) or [None, "other"])[1].upper().replace("LETTER", "Letter")
    images = len(run(["pdfimages", "-list", pdf]).strip().splitlines()) - 2
    fonts = run(["pdffonts", pdf]).strip().splitlines()[2:]
    odd = [c for c in text if ord(c) > 0x024F and c not in "–—•’“”…€"]
    columns = [l for l in lines if re.search(r"\S {4,}\S", l.strip())]

    keys = ("summary", "skills", "experience", "projects", "education")
    heads = [d["labels"][k].lower() for k in keys]
    pos = [m.start() if (m := re.search(r"^\s*%s\s*$" % re.escape(h), low, re.M)) else -1 for h in heads]
    found = sorted(p for p in pos if p >= 0)
    section = {k: low[p:min([q for q in found if q > p], default=len(low))] if p >= 0 else ""
               for k, p in zip(keys, pos)}
    empty = [h for k, h in zip(keys, heads) if section[k] and len(section[k]) - len(h) < 20]

    jobs = d["experience"]
    bullets = [b for j in jobs for b in j["points"]] + [b for p in d["projects"] for b in p["points"]]
    quantified = [b for b in bullets if re.search(r"\d", b)]
    verbs = [b for b in bullets if b.split()[0].lower().rstrip(",") in IRREGULAR or b.split()[0].lower().endswith("ed")]
    firsts = Counter(b.split()[0].lower() for b in bullets)
    bad_len = [b for b in bullets if not 8 <= len(b.split()) <= 30]
    weak = [b for b in bullets + [d["summary"]] if WEAK.search(b)]
    short_jobs = [j["company"] for j in jobs if len(j["points"]) < 2]

    ranges = DATE.findall(text)
    fmts = {re.sub(r"\d", "9", re.sub(r"[A-Z][a-z]{2}", "Mon", a)) for a, _ in ranges}
    no_date_line = [j["company"] for j in jobs
                    if not any(j["company"].lower() in l.lower() and DATE.search(l) for l in lines)]
    starts = [ym(j["start"]) for j in jobs]
    gaps = [j["company"] for prev, j in zip(jobs, jobs[1:]) if ym(prev["start"]) - ym(j["end"]) > 6]
    edu_wrapped = [e["school"] for e in d["education"]
                   if not any(e["school"].lower() in l.lower() and re.search(r"\d{4}\s*-\s*\d{4}", l) for l in lines)]

    kws = yaml.safe_load(open(os.path.join(build.HERE, "keywords.yaml"), encoding="utf-8"))
    missing = [k for k in kws if k not in low]
    outside = low.replace(section["skills"], "")
    skills_only = [k for k in kws if k in low and k not in outside]
    n_skills = sum(len(s["items"]) for s in d["skills"])
    title = d["title"].lower()
    top = "\n".join(lines[:5])
    contact = {"email": d["email"] in text, "phone": d["phone"] in text.replace(" ", ""),
               "location": d["location"].split(",")[0] in text}
    std = STD_HEADINGS["en" if en else "de"]
    details = {k: v for k, v in (d.get("details") or {}).items()}
    swords = len(d["summary"].split())

    frac = lambda bad, total: 1 - len(bad) / max(total, 1)
    market = {
        "india": [
            ("A4 page size", 1, size == "A4", "set page_size: A4"),
            ("Notice period stated", 2, bool(details.get("Notice period")), "fill Notice period in overrides/india.yaml"),
            ("Current/expected CTC stated", 1, bool(details.get("Current CTC") and details.get("Expected CTC")),
             "fill Current CTC / Expected CTC in overrides/india.yaml"),
            ("Total experience stated", 1, "years" in low[:1500], "show total_experience near the top"),
        ],
        "intl": [
            ("Letter page size", 1, size == "Letter", "set page_size: Letter"),
            ("No personal data (DOB, photo, nationality)", 3, not details and images <= 0, "drop details in overrides/intl.yaml"),
            ("Work authorization / relocation line", 1, bool(re.search(r"visa|relocat|authori[sz]", low)),
             "add a relocation / work-authorization note"),
        ],
        "de": [
            ("A4 page size", 1, size == "A4", "set page_size: A4"),
            ("German standard headings", 1, all(h in std for h in heads), "use Berufserfahrung, Ausbildung, Kenntnisse"),
            ("Geburtsdatum / Staatsangehörigkeit", 1, all(details.values()) and bool(details),
             "fill Geburtsdatum and Staatsangehörigkeit in overrides/de.yaml"),
            ("Sprachkenntnisse section", 2, bool(re.search(r"sprachkenntnisse|deutsch\s*\(|englisch", low)),
             "add a languages list with levels (e.g. Englisch C1, Deutsch A2)"),
        ],
    }[target]

    cats = {
        "Parseability": [
            ("Text extractable", 3, words > 200, "PDF has little extractable text"),
            ("No images", 2, images <= 0, "%d images in PDF" % images),
            ("Single column, no tables", 3, not columns, "column/table-like gaps on %d lines" % len(columns)),
            ("Fonts embedded", 2, bool(fonts) and all(re.search(r"\byes\b", l[-30:]) for l in fonts), "embed all fonts"),
            ("No icons/emoji/odd glyphs", 1, not odd, "odd glyphs: " + "".join(sorted(set(odd)))[:20]),
            ("File under 2 MB", 1, os.path.getsize(pdf) < 2_000_000, "shrink the PDF"),
        ],
        "Structure & headings": [
            ("All standard sections present", 3, all(p >= 0 for p in pos),
             "missing: " + ", ".join(h for h, p in zip(heads, pos) if p < 0)),
            ("Sections in conventional order", 2, pos == sorted(pos), "reorder sections"),
            ("Common heading wording", 2, all(h in std for h in heads),
             "unusual headings: " + ", ".join(h for h in heads if h not in std)),
            ("No empty sections", 1, not empty, "empty: " + ", ".join(empty)),
        ],
        "Contact info": [
            ("Name on first line", 2, d["name"] in lines[0], "put the name alone on line 1"),
            ("Email, phone, location as text", 4, frac([k for k, v in contact.items() if not v], 3),
             "missing: " + ", ".join(k for k, v in contact.items() if not v)),
            ("Contact in top 5 lines (not header/footer)", 2, d["email"] in top, "move contact line to the top"),
            ("LinkedIn URL", 2, bool(d["linkedin"]), "set linkedin in data.yaml"),
        ],
        "Experience & dates": [
            ("Date range on every job", 3, frac(range(max(len(jobs) - len(ranges), 0)), len(jobs)), "add start - end dates"),
            ("One consistent date format", 2, len(fmts) <= 1, "formats seen: " + ", ".join(sorted(fmts))),
            ("Dates on the role/company line", 2, frac(no_date_line, len(jobs)), "dates not on header line: " + ", ".join(no_date_line)),
            ("Reverse-chronological", 2, starts == sorted(starts, reverse=True), "list newest job first"),
            ("No gaps over 6 months", 1, not gaps, "gap before: " + ", ".join(gaps)),
            ("Education years on one line", 1, frac(edu_wrapped, len(d["education"])),
             "education years wrap onto a new line: " + ", ".join(edu_wrapped)),
        ],
        "Keywords & skills": [
            ("Core keyword coverage", 4, frac(missing, len(kws)), "missing keywords: " + ", ".join(missing)),
            ("Keywords used in bullets, not just skills list", 2, frac(skills_only, len(kws) - len(missing)),
             "only in skills list: " + ", ".join(skills_only)),
            ("Target title in headline and summary", 2, title in "\n".join(lines[:3]).lower() and title in section["summary"],
             "repeat '%s' in headline and summary" % d["title"]),
            ("Skills list 15-50 items", 1, 15 <= n_skills <= 50, "%d skills listed" % n_skills),
        ],
        "Impact & wording": [
            ("40%+ bullets quantified", 6, min(1, len(quantified) / max(len(bullets), 1) / 0.4),
             "%d of %d bullets have a number; add metrics (users, %%, ms, crash-free rate)" % (len(quantified), len(bullets))),
            ("Every job has 2+ bullets", 2, frac(short_jobs, len(jobs)), "add bullets for: " + ", ".join(short_jobs)),
            ("Bullets open with action verbs", 2, len(verbs) / max(len(bullets), 1) if en else 1,
             "start bullets with Built, Led, Shipped..."),
            ("No weak phrases / first person", 2, frac(weak, len(bullets) + 1), "%d bullets use weak phrases" % len(weak)),
            ("Varied bullet openers", 1, max(firsts.values(), default=0) <= 2,
             "repeated openers: " + ", ".join(w for w, c in firsts.items() if c > 2)),
            ("Bullets 8-30 words", 1, frac(bad_len, len(bullets)), "%d bullets too short/long" % len(bad_len)),
        ],
        "Length": [
            ("At most 2 pages", 2, pages <= 2, "%d pages" % pages),
            ("350-800 words", 2, 350 <= words <= 800, "%d words" % words),
            ("Summary 30-60 words", 1, 30 <= swords <= 60, "summary has %d words" % swords),
        ],
        "Market fit": market,
    }
    return {c: [(n, w, float(f), h) for n, w, f, h in checks] for c, checks in cats.items()}, text


def pct(checks):
    return 100 * sum(w * f for _, w, f, _ in checks) / sum(w for _, w, _, _ in checks)


def keyword_match(text, jd_path):
    tok = lambda s: re.findall(r"[a-z][a-z+#.\-]{2,}", s.lower())
    have = set(tok(text))
    jd = Counter(t for t in tok(open(jd_path, encoding="utf-8").read()) if t not in STOP)
    hit = [t for t in jd if t in have]
    missing = [t for t, _ in jd.most_common() if t not in have][:15]
    return 100 * len(hit) / max(len(jd), 1), missing


def write_readme(res, final):
    """Replace the block between the ats-table markers in README.md with a markdown score table."""
    names = [build.PDF_NAMES[t] for t in res]
    rows = ["| Category | Weight | %s |" % " | ".join(names), "|---|---:|" + "---:|" * len(names)]
    rows += ["| %s | %d | %s |" % (c, w, " | ".join("%d" % round(pct(res[t][0][c])) for t in res)) for c, w in CATEGORIES]
    rows.append("| **Final** | **100** | %s |" % " | ".join("**%d**" % round(final[t]) for t in res))
    path = os.path.join(build.ROOT, "README.md")
    s = open(path, encoding="utf-8").read()
    start, end = "<!-- ats-table:start -->", "<!-- ats-table:end -->"
    s = re.sub(re.escape(start) + ".*?" + re.escape(end), lambda _: "%s\n%s\n%s" % (start, "\n".join(rows), end), s, flags=re.S)
    open(path, "w", encoding="utf-8").write(s)


def write_comment(path, scores, base, dropped):
    """Markdown table of main's score -> this PR's score per category and resume."""
    def cell(t, c):
        new, old = scores[t][c], base.get(t, {}).get(c)
        if old is None or old == new:
            return "%d" % new
        return "%d → %d (%+d)" % (old, new, new - old)
    names = [build.PDF_NAMES[t] for t in scores]
    rows = ["<!-- ats-score-comment -->", "### ATS score: main → this PR", "",
            "| Category | %s |" % " | ".join(names), "|---|" + "---:|" * len(names)]
    rows += ["| %s | %s |" % (c, " | ".join(cell(t, c) for t in scores)) for c, _ in CATEGORIES]
    rows.append("| **Final** | %s |" % " | ".join("**%s**" % cell(t, "Final") for t in scores))
    rows.append("")
    if dropped:
        rows.append("❌ Score dropped below main for: " + ", ".join(build.PDF_NAMES[t] for t in dropped))
    elif base:
        rows.append("✅ No resume scores lower than main.")
    else:
        rows.append("No baseline from main yet; showing this PR's scores only.")
    open(path, "w", encoding="utf-8").write("\n".join(rows) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", default=["india", "intl", "de"])
    ap.add_argument("--min", type=int, default=89, help="minimum Parseability category score")
    ap.add_argument("--jd")
    ap.add_argument("--json-dir", help="write shields.io endpoint JSON per variant here")
    ap.add_argument("--readme", action="store_true", help="rewrite the score table in README.md")
    ap.add_argument("--baseline", help="scores.json from main; fail if any final score drops below it")
    ap.add_argument("--comment", help="write a markdown main-vs-PR score table here (for a PR comment)")
    a = ap.parse_args()
    res = {}
    for t in a.targets:
        pdf = os.path.join(build.ROOT, "resumes", "Manikanta_Nandam_Resume_%s.pdf" % build.PDF_NAMES[t])
        res[t] = score(t, pdf)
    final = {t: sum(w * pct(res[t][0][c]) for c, w in CATEGORIES) / 100 for t in res}

    names = [build.PDF_NAMES[t] for t in res]
    print("ATS score (own heuristic, not a real ATS): " + "  ".join("%s %d/100" % (n, round(final[t])) for n, t in zip(names, res)))
    print()
    print("%-24s %6s " % ("Category", "Weight") + " ".join("%6s" % n for n in names))
    for c, w in CATEGORIES:
        print("%-24s %6d " % (c, w) + " ".join("%6d" % round(pct(res[t][0][c])) for t in res))
    print("%-24s %6d " % ("Final", 100) + " ".join("%6d" % round(final[t]) for t in res))

    # Fixes ranked by points lost in the final score (summed across resumes).
    lost = {}
    for t in res:
        for c, w in CATEGORIES:
            checks = res[t][0][c]
            total = sum(cw for _, cw, _, _ in checks)
            for n, cw, f, hint in checks:
                if f < 1:
                    pts = w * cw / total * (1 - f)
                    lost.setdefault((c, n), {"hint": hint, "pts": {}})["pts"][t] = pts
    if lost:
        print("\nWhere points are lost (final-score points per resume):")
        for (c, n), v in sorted(lost.items(), key=lambda kv: -sum(kv[1]["pts"].values())):
            per = " ".join("%s -%.1f" % (build.PDF_NAMES[t], p) for t, p in v["pts"].items())
            print("  [%s] %s (%s): %s" % (c, n, per, v["hint"]))

    if a.readme:
        write_readme(res, final)

    failed = False
    scores = {t: dict({c: round(pct(res[t][0][c])) for c, _ in CATEGORIES}, Final=round(final[t])) for t in res}
    if a.json_dir:
        os.makedirs(a.json_dir, exist_ok=True)
        with open(os.path.join(a.json_dir, "scores.json"), "w") as f:
            json.dump(scores, f)
    base = json.load(open(a.baseline)) if a.baseline and os.path.exists(a.baseline) else {}
    # Older scores.json held only {target: final}.
    base = {t: v if isinstance(v, dict) else {"Final": v} for t, v in base.items()}
    dropped = [t for t in res if t in base and scores[t]["Final"] < base[t]["Final"]]
    for t in dropped:
        print("FAIL: %s ATS score %d is below main's %d" % (build.PDF_NAMES[t], scores[t]["Final"], base[t]["Final"]))
        failed = True
    if a.comment:
        write_comment(a.comment, scores, base, dropped)
    for t in res:
        text = res[t][1]
        if a.jd:
            jd_pct, missing = keyword_match(text, a.jd)
            print("%s JD keyword match: %.0f%%; missing: %s" % (build.PDF_NAMES[t], jd_pct, ", ".join(missing)))
        if a.json_dir:
            os.makedirs(a.json_dir, exist_ok=True)
            s = round(final[t])
            color = "brightgreen" if s >= 89 else "yellow" if s >= 75 else "red"
            with open(os.path.join(a.json_dir, "ats-%s.json" % t), "w") as f:
                json.dump({"schemaVersion": 1, "label": "ATS (%s)" % build.PDF_NAMES[t], "message": "%d/100" % s,
                           "color": color}, f)
        parse = pct(res[t][0]["Parseability"])
        if parse < a.min:
            print("FAIL: %s parseability %d < %d" % (build.PDF_NAMES[t], round(parse), a.min))
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
