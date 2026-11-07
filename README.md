# manikantanandam.github.io
![ATS India](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-india.json) ![ATS Intl](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-intl.json) ![ATS DE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-de.json)

Badges show our own final ATS score for the committed PDFs (not a real ATS score); the "ATS badges" workflow refreshes them after every push to `main`.

Personal portfolio, plain HTML/CSS/JS, served by GitHub Pages at https://manikantanandam.github.io/.

- Light/dark theme switch and text-size controls (saved in the browser).
- Contact via WhatsApp, email and phone links.
- Buttons that open the India and International resumes in a new tab.

## Content: single source

Edit only `resume-builder/data.yaml` (shared content) and `resume-builder/overrides/{site,india,intl,de}.yaml` (changes specific to one output). `index.html`, `sitemap.xml`, `robots.txt` and `resumes/*` are generated; never edit them by hand.

```
pip install -r resume-builder/requirements.txt    # PyYAML, Jinja2 (Chrome is also required)
python3 resume-builder/build.py all               # or: site | india | intl | de
```

Outputs:
- `index.html`: the pre-rendered site (content, meta tags, JSON-LD for SEO) from `resume-builder/templates/site.html.j2`; `script.js` adds interactivity only.
- `sitemap.xml`, `robots.txt`: for search engines.
- `resumes/`: India, International and German (Lebenslauf) ATS PDFs. The site buttons link to the India and International ones.

Fill the empty personal fields (date of birth, nationality, CTC, notice period) in the overrides to include them. The German text is a draft translation.

## ATS check

`python3 resume-builder/ats_check.py [--min 89] [--jd job.txt]` prints one final score per PDF in `resumes/`, a table of 8 weighted categories (Parseability, Structure & headings, Contact info, Experience & dates, Keywords & skills, Impact & wording, Length, Market fit) by resume, and the fixes that lose the most points. Checks are distilled from public ATS guidance (Jobscan-style categories, Workday/Greenhouse parsing notes, German Lebenslauf norms); keywords come from `resume-builder/keywords.yaml`. It is our own heuristic, not a real ATS score (none is standard). Only the Parseability category gates CI (`--min`). `--jd` adds a keyword match against a job description. Needs poppler. The "ATS check" workflow runs it on every PR to `main`.

## Get a resume PDF from GitHub

Actions tab, "Build resume", Run workflow, pick `india`, `intl`, `de` or `all`, then download the artifact from the finished run.

## Deploy and run locally

Commit the regenerated files and push to `main`; GitHub Pages republishes automatically (it does not run the build). Preview locally with `python3 -m http.server`.
