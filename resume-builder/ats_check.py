#!/usr/bin/env python3
"""Heuristic ATS-readiness check for the generated resume PDFs in resumes/.

This is OUR OWN structural score, not a real ATS score (no standard one exists). It checks that
common parsers can read the file; it says nothing about whether a recruiter will shortlist.
Needs poppler (pdftotext, pdfinfo, pdfimages, pdffonts).

Usage: python3 resume-builder/ats_check.py [--min 89] [--jd job.txt] [--json-dir DIR] [india|intl|de ...]
"""
import argparse, json, os, re, subprocess, sys
from collections import Counter

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
        print("%s: %d/100 (structural heuristic)" % (os.path.basename(pdf), score))
        for name, w, ok in res:
            if not ok:
                print("  FAIL (-%d) %s" % (w, name))
        if a.json_dir:
            os.makedirs(a.json_dir, exist_ok=True)
            color = "brightgreen" if score >= 89 else "yellow" if score >= 75 else "red"
            with open(os.path.join(a.json_dir, "ats-%s.json" % t), "w") as f:
                json.dump({"schemaVersion": 1, "label": "ATS (%s)" % build.PDF_NAMES[t], "message": "%d/100" % score,
                           "color": color}, f)
        if a.jd:
            pct, missing = keyword_match(text, a.jd)
            print("  JD keyword match: %.0f%%; missing: %s" % (pct, ", ".join(missing)))
        failed |= score < a.min
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
