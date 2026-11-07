# manikantanandam.github.io
![ATS India](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-india.json) ![ATS Intl](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-intl.json) ![ATS DE](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/manikantanandam/manikantanandam.github.io/badges/ats-de.json)

Badges show our own final ATS score (out of 100) for each committed resume PDF; the "ATS badges" workflow rebuilds the PDFs and refreshes them after every push to `main`. It is not a real ATS score (none is standard).

Personal portfolio, plain HTML/CSS/JS, served by GitHub Pages at https://manikantanandam.github.io/.

- Editorial design, mobile-friendly, with fade-in sections and nav scroll-spy.
- Light/dark theme switch and text-size controls (saved in the browser).
- Pre-rendered for SEO and link previews (meta/OG tags, JSON-LD).
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

## ATS score

Our own score, built from public ATS guidance (Jobscan-style categories, Workday/Greenhouse parsing notes, German Lebenslauf norms). Each category is scored 0-100 from weighted checks; the final score is the weighted sum of categories.

<!-- ats-table:start -->
| Category | Weight | India | Intl | DE |
|---|---:|---:|---:|---:|
| Parseability | 15 | 100 | 100 | 100 |
| Structure & headings | 10 | 100 | 100 | 100 |
| Contact info | 10 | 100 | 100 | 100 |
| Experience & dates | 15 | 91 | 100 | 100 |
| Keywords & skills | 20 | 88 | 88 | 88 |
| Impact & wording | 20 | 61 | 61 | 60 |
| Length | 5 | 100 | 100 | 100 |
| Market fit | 5 | 40 | 80 | 40 |
| **Final** | **100** | **85** | **89** | **87** |
<!-- ats-table:end -->

| Category | What it checks |
|---|---|
| Parseability | Extractable text, no images, single column / no tables, embedded fonts, no odd glyphs, file under 2 MB |
| Structure & headings | All standard sections, conventional order and wording, none empty |
| Contact info | Name on line 1, email/phone/location as text in the top 5 lines, LinkedIn |
| Experience & dates | Date range on every job, one date format, dates on the role line, newest first, no gaps over 6 months |
| Keywords & skills | Coverage of `resume-builder/keywords.yaml`, keywords used in bullets (not just the skills list), target title in headline and summary, 15-50 skills |
| Impact & wording | 40%+ bullets with numbers, 2+ bullets per job, action verbs, no weak phrases, varied openers, 8-30 words per bullet |
| Length | At most 2 pages, 350-800 words, 30-60 word summary |
| Market fit | India: A4, notice period, CTC. Intl: Letter, no personal data, relocation line. DE: A4, German headings, birth date/nationality, languages |

```
python3 resume-builder/ats_check.py [--min 89] [--jd job.txt] [--readme] [--baseline scores.json] [--comment out.md] [india|intl|de ...]
```

- Prints the final scores, the category table and the fixes that lose the most points. Needs poppler.
- `--readme` rewrites the table above; CI fails if it is stale, so rerun it after rebuilding the PDFs.
- `--jd` adds a keyword match against a job description.
- The "ATS check" workflow runs on every PR to `main` and fails if Parseability is below `--min` or any resume's final score drops below main's (`--baseline`, read from `scores.json` on the `badges` branch). It also posts a PR comment with a main → PR score table per category and resume (`--comment`), updated in place on each run.

## Get a resume PDF from GitHub

Actions tab, "Build resume", Run workflow, pick `india`, `intl`, `de` or `all`, then download the artifact from the finished run.

## Deploy and run locally

Commit the regenerated files and push to `main`; GitHub Pages republishes automatically (it does not run the build). Preview locally with `python3 -m http.server`.
