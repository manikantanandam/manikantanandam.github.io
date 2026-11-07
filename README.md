# manikantanandam.github.io

Personal portfolio, plain HTML/CSS/JS, served by GitHub Pages at https://manikantanandam.github.io/.

- Light/dark theme switch and text-size controls (saved in the browser).
- Contact via WhatsApp, email and phone links.
- Buttons that open the India and International resumes in a new tab.

## Content: single source

Edit only `resume-builder/data.yaml` (shared content) and `resume-builder/overrides/{site,india,intl,de}.yaml` (changes specific to one output). `config.js` and `resumes/*` are generated; never edit them by hand.

```
pip install -r resume-builder/requirements.txt    # PyYAML, Jinja2 (Chrome is also required)
python3 resume-builder/build.py all               # or: site | india | intl | de
```

Outputs:
- `config.js`: site content, read by `script.js`.
- `resumes/`: India, International and German (Lebenslauf) ATS PDFs. The site buttons link to the India and International ones.

Fill the empty personal fields (date of birth, nationality, CTC, notice period) in the overrides to include them. The German text is a draft translation.

## Get a resume PDF from GitHub

Actions tab, "Build resume", Run workflow, pick `india`, `intl`, `de` or `all`, then download the artifact from the finished run.

## Deploy and run locally

Commit the regenerated files and push to `main`; GitHub Pages republishes automatically (it does not run the build). Preview locally with `python3 -m http.server`.
