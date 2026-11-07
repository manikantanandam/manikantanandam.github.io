#!/usr/bin/env python3
"""Heuristic ATS-readiness check (parseability + content) for the generated resume PDFs in resumes/.

This is OUR OWN structural score, not a real ATS score (no standard one exists). It checks that
common parsers can read the file; it says nothing about whether a recruiter will shortlist.
Needs poppler (pdftotext, pdfinfo, pdfimages, pdffonts).

Usage: python3 resume-builder/ats_check.py [--min 89] [--jd job.txt] [--json-dir DIR] [india|intl|de ...]
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


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def checks(target, pdf):
    d = build.resolve(target)
    text = run(["pdftotext", "-layout", pdf, "-"])
    words = len(text.split())
    labels = d["labels"]
    heads = [labels[k].lower() for k in ("summary", "skills", "experience", "projects", "education")]
    low = text.lower()
    pos = [m.start() if (m := re.search(r"^\s*%s\s*$" % re.escape(h), low, re.M)) else -1 for h in heads]
    pages = int(re.search(r"Pages:\s+(\d+)", run(["pdfinfo", pdf])).group(1))
    images = len(run(["pdfimages", "-list", pdf]).strip().splitlines()) - 2
    fonts = run(["pdffonts", pdf]).strip().splitlines()[2:]
    sections_ok = all(
        len(low[p + len(h) + 1:(pos[i + 1] if i + 1 < len(pos) else len(low))].strip()) > 20
        for i, (p, h) in enumerate(zip(pos, heads)) if p >= 0)
    odd = [c for c in text if ord(c) > 0x024F and c not in "–—•’“”…€"]
    contact = [d["email"] in text, d["phone"] in text.replace(" ", ""), d["location"].split(",")[0] in text]
    return [
        ("Text extractable", 15, words > 200),
        ("No images", 10, images <= 0),
        ("Standard headings, in order", 15, all(p >= 0 for p in pos) and pos == sorted(pos)),
        ("Email, phone, location as text", 10, all(contact)),
        ("Date range on every job", 10, len(DATE.findall(text)) >= len(d["experience"])),
        ("<= 2 pages", 10, pages <= 2),
        ("350-800 words", 10, 350 <= words <= 800),
        ("Fonts embedded", 10, bool(fonts) and all(" yes " in " %s " % l[-30:] or " yes" in l for l in fonts)),
        ("No icon/odd glyphs", 5, not odd),
        ("No empty sections", 5, sections_ok),
    ], text


IRREGULAR = set("built led ran wrote made grew began drove took set won taught".split())


def content_checks(target, text):
    """Own heuristic for content quality. Returns [(name, weight, fraction 0..1, fix hint)]."""
    d = build.resolve(target)
    jobs = d["experience"]
    bullets = [b for j in jobs for b in j["points"]] + [b for p in d["projects"] for b in p["points"]]
    has_num = [b for b in bullets if re.search(r"\d", b)]
    verbs = [b for b in bullets if b.split()[0].lower().rstrip(",") in IRREGULAR or b.split()[0].lower().endswith("ed")]
    firsts = Counter(b.split()[0].lower() for b in bullets)
    kws = yaml.safe_load(open(os.path.join(build.HERE, "keywords.yaml"), encoding="utf-8"))
    low = text.lower()
    missing = [k for k in kws if k not in low]
    short_jobs = [j["company"] for j in jobs if len(j["points"]) < 2]
    swords = len(d["summary"].split())
    en = d["lang"] == "en"
    return [
        ("Every job has >= 2 bullets", 25, 1 - len(short_jobs) / len(jobs),
         "add bullets for: " + ", ".join(short_jobs)),
        ("40%+ bullets quantified", 25, min(1, len(has_num) / max(len(bullets), 1) / 0.4),
         "%d of %d bullets contain a number; add metrics (users, %%, time saved)" % (len(has_num), len(bullets))),
        ("Bullets start with action verbs", 10, 1 if not en else len(verbs) / max(len(bullets), 1),
         "start bullets with verbs like Built, Led, Implemented"),
        ("Summary 30-60 words", 10, 1 if 30 <= swords <= 60 else 0, "summary has %d words" % swords),
        ("LinkedIn present", 10, 1 if d["linkedin"] else 0, "set linkedin in data.yaml"),
        ("Core keyword coverage", 15, 1 - len(missing) / len(kws), "missing keywords: " + ", ".join(missing)),
        ("Varied bullet openers", 5, 1 if max(firsts.values(), default=0) <= 2 else 0,
         "repeated openers: " + ", ".join(w for w, c in firsts.items() if c > 2)),
    ]


def keyword_match(text, jd_path):
    tok = lambda s: re.findall(r"[a-z][a-z+#.\-]{2,}", s.lower())
    have = set(tok(text))
    jd = Counter(t for t in tok(open(jd_path, encoding="utf-8").read()) if t not in STOP)
    hit = [t for t in jd if t in have]
    missing = [t for t, _ in jd.most_common() if t not in have][:15]
    return 100 * len(hit) / max(len(jd), 1), missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", default=["india", "intl", "de"])
    ap.add_argument("--min", type=int, default=89)
    ap.add_argument("--jd")
    ap.add_argument("--json-dir", help="write shields.io endpoint JSON per variant here")
    a = ap.parse_args()
    failed = False
    for t in a.targets:
        pdf = os.path.join(build.ROOT, "resumes", "Manikanta_Nandam_Resume_%s.pdf" % build.PDF_NAMES[t])
        res, text = checks(t, pdf)
        score = sum(w for _, w, ok in res if ok)
        cres = content_checks(t, text)
        content = round(sum(w * f for _, w, f, _ in cres))
        print("%s: parseability %d/100, content %d/100 (own heuristics, not a real ATS score)"
              % (os.path.basename(pdf), score, content))
        for name, w, ok in res:
            if not ok:
                print("  FAIL (-%d) %s" % (w, name))
        for name, w, f, hint in cres:
            if f < 1:
                print("  content -%d %s: %s" % (round(w * (1 - f)), name, hint))
        if a.json_dir:
            os.makedirs(a.json_dir, exist_ok=True)
            low_score = min(score, content)
            color = "brightgreen" if low_score >= 89 else "yellow" if low_score >= 75 else "red"
            with open(os.path.join(a.json_dir, "ats-%s.json" % t), "w") as f:
                json.dump({"schemaVersion": 1, "label": "ATS (%s)" % build.PDF_NAMES[t], "message": "parse %d | content %d" % (score, content),
                           "color": color}, f)
        if a.jd:
            pct, missing = keyword_match(text, a.jd)
            print("  JD keyword match: %.0f%%; missing: %s" % (pct, ", ".join(missing)))
        failed |= score < a.min
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
