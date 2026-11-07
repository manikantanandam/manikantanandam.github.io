# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal portfolio at https://manikantanandam.github.io/, served by GitHub Pages from `main` (push to deploy). The site is plain HTML/CSS/JS with no build, lint or test tooling. Resume PDFs and `config.js` are generated from one source by a Python script.

## Commands

- Serve locally: `python3 -m http.server` in the repo root, then open `index.html`.
- Regenerate everything: `python3 resume-builder/build.py all` (or one of `site|india|intl|de`). Needs PyYAML, Jinja2 (`resume-builder/requirements.txt`) and Chrome (override with `$CHROME`).
- Structural ATS score (own heuristic, needs poppler): `python3 resume-builder/ats_check.py [--min 89] [--jd job.txt]`; CI (`.github/workflows/ats-check.yml`) runs it on PRs and fails if `config.js` is stale.
- Check a PDF's ATS text order: `pdftotext -layout resumes/<file>.pdf -`.

## Single source of truth

- Edit only `resume-builder/data.yaml` (shared content) and `resume-builder/overrides/{site,india,intl,de}.yaml` (target-specific changes). Never hand-edit `config.js` or `resumes/*`; they are generated and committed (Pages has no build step).
- Overrides are deep-merged over the data. Lists whose items all have `id` merge per id; other lists are replaced. Items with `only: [targets]` are dropped elsewhere (e.g. `apoorva` is site-only).
- `resumes/` (repo root) holds the three PDFs; the site's two buttons (open in a new tab) link to the India and Intl ones via the `resumes` list in `site.yaml`.
- `.github/workflows/resume.yml` is a manual (`workflow_dispatch`) action: pick `india|intl|de|all`, it runs `build.py` and uploads the PDFs as a run artifact (no commit/deploy).
- German translations in `de.yaml` are a draft; DOB, nationality and India CTC/notice fields are empty and omitted until filled.

## Site architecture

- `index.html` holds empty placeholder ids and loads `config.js` then `script.js` (order matters).
- `config.js` sets `window.SITE_CONFIG`; `script.js` (IIFE) builds the DOM from it. Empty `resume`, `whatsapp`, `linkedin` or project `link` hide that element.
- `script.js` `el()` sets `textContent` only; keep it so config values are never parsed as HTML.
- An inline script in `<head>` applies localStorage `theme`/`fontScale` before first paint (falls back to `prefers-color-scheme`).
- `style.css` themes with CSS variables and a `:root[data-theme="dark"]` override, plus `--font-scale`.
