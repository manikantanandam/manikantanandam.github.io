#!/usr/bin/env python3
"""Generate the site (index.html, sitemap.xml, robots.txt) and ATS resume PDFs (india, intl, de)
from resume-builder/data.yaml.

Usage: python3 resume-builder/build.py [site|india|intl|de|all]
Overrides in resume-builder/overrides/<target>.yaml are deep-merged over data.yaml; lists whose items
all have an `id` are merged per id, other lists are replaced. Items with `only: [targets]`
are dropped from other targets. PDFs are rendered with headless Chrome (override via $CHROME).
"""
import copy, json, os, re, subprocess, sys, tempfile
from urllib.parse import quote
import yaml
from jinja2 import Environment, FileSystemLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGETS = ["site", "india", "intl", "de"]
PDF_NAMES = {"india": "India", "intl": "Intl", "de": "DE"}
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chrome",
]
MONTHS = {"en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_id_list(v):
    return isinstance(v, list) and v and all(isinstance(i, dict) and "id" in i for i in v)


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        elif is_id_list(v) and is_id_list(out.get(k)):
            by_id = {i["id"]: i for i in v}
            out[k] = [merge(i, by_id[i["id"]]) if i["id"] in by_id else i for i in out[k]]
        else:
            out[k] = copy.deepcopy(v)
    return out


def filter_only(data, target):
    for k, v in data.items():
        if isinstance(v, list):
            data[k] = [i for i in v if not (isinstance(i, dict) and "only" in i and target not in i["only"])]
    return data


def resolve(target):
    data = load(os.path.join(HERE, "data.yaml"))
    return filter_only(merge(data, load(os.path.join(HERE, "overrides", target + ".yaml"))), target)


def fmt_date(v, lang, present):
    v = str(v)
    if v == "present":
        return present
    m = re.match(r"^(\d{4})-(\d{2})$", v)
    if not m:
        return v
    return ("%s/%s" % (m.group(2), m.group(1))) if lang == "de" else "%s %s" % (MONTHS["en"][int(m.group(2)) - 1], m.group(1))


def period(item, lang, present):
    return "%s - %s" % (fmt_date(item["start"], lang, present), fmt_date(item["end"], lang, present))


def json_ld(d):
    url = d["site_url"]
    person = {
        "@context": "https://schema.org", "@type": "Person", "name": d["name"], "url": url,
        "image": url + d["photo"], "jobTitle": d["title"], "email": "mailto:" + d["email"],
        "description": d["summary"],
        "address": {"@type": "PostalAddress", "addressLocality": d["location"].split(",")[0].strip(),
                    "addressCountry": "IN"},
        "worksFor": {"@type": "Organization", "name": d["experience"][0]["company"]},
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": e["school"]} for e in d["education"]],
        "knowsAbout": [i for s in d["skills"] for i in s["items"]][:20],
        "sameAs": [u for u in (d["github"], d["linkedin"]) if u],
    }
    site = {"@context": "https://schema.org", "@type": "WebSite", "name": d["name"], "url": url}
    # Escape "</" so the JSON can never close the surrounding <script> tag.
    return json.dumps([person, site], ensure_ascii=False, indent=2).replace("</", "<\\/")


def build_site():
    d = resolve("site")
    d["summary"] = d["summary"].strip()
    d["wa_url"] = "https://wa.me/%s?text=%s" % (re.sub(r"\D", "", d["phone"]), quote(d["whatsappMessage"]))
    d["mailto"] = "mailto:%s?subject=%s" % (d["email"], quote(d["emailSubject"]))
    d["experience"] = [dict(e, period=period(e, "en", "Present")) for e in d["experience"]]
    d["json_ld"] = json_ld(d)
    env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)
    outputs = {
        "index.html": env.get_template("site.html.j2").render(**d),
        "sitemap.xml": '<?xml version="1.0" encoding="UTF-8"?>\n'
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                       + "".join("  <url><loc>%s</loc></url>\n" % u for u in
                                 [d["site_url"]] + [d["site_url"] + k["href"] for k in d["knowledge"]])
                       + "</urlset>\n",
        "robots.txt": "User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n" % d["site_url"],
    }
    for name, body in outputs.items():
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(body)
        print("wrote", name)


def find_chrome():
    for c in [os.environ.get("CHROME")] + CHROME_CANDIDATES:
        if c and (os.path.exists(c) or subprocess.call(["which", c], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0):
            return c
    sys.exit("Chrome/Chromium not found; set $CHROME")


def build_pdf(target):
    d = resolve(target)
    lang = d["lang"]
    present = d["labels"].get("present", "Present")
    d["experience"] = [dict(e, period=period(e, lang, present)) for e in d["experience"]]
    d["education"] = [dict(e, start=e["start"], end=e["end"]) for e in d["education"]]
    contact = [d["location"], d["phone"], d["email"], d["github"]] + ([d["linkedin"]] if d["linkedin"] else [])
    d["contact_line"] = " | ".join(contact)
    d["details_line"] = " | ".join("%s: %s" % (k, v) for k, v in d.get("details", {}).items() if v)
    d["summary"] = d["summary"].strip()
    env = Environment(loader=FileSystemLoader(os.path.join(HERE, "templates")), autoescape=True)
    html = env.get_template("resume.html.j2").render(**d)
    out = os.path.join(ROOT, "resumes", "Manikanta_Nandam_Resume_%s.pdf" % PDF_NAMES[target])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "resume.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(html)
        subprocess.check_call([find_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                               "--print-to-pdf=" + out, "file://" + src],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", os.path.relpath(out, ROOT))
    return out


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = TARGETS if arg == "all" else [arg]
    if any(t not in TARGETS for t in targets):
        sys.exit(__doc__)
    for t in targets:
        build_site() if t == "site" else build_pdf(t)


if __name__ == "__main__":
    main()
