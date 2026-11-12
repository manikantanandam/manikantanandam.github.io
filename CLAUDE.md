# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal portfolio at https://manikantanandam.github.io/, served by GitHub Pages from `main` (push to deploy). The site is plain HTML/CSS/JS with no build, lint or test tooling. Resume PDFs and the site (`index.html`, `sitemap.xml`, `robots.txt`) are generated from one source by a Python script.

## Commands

- Serve locally: `python3 -m http.server` in the repo root, then open `index.html`.
- Regenerate everything: `python3 resume-builder/build.py all` (or one of `site|india|intl|de`). Needs PyYAML, Jinja2 (`resume-builder/requirements.txt`) and Chrome (override with `$CHROME`).
- ATS check: one final score plus an 8-category x resume table and top fixes (own heuristic, needs poppler; keywords in `resume-builder/keywords.yaml`; only the Parseability category gates CI via `--min`; `--readme` refreshes the README table, CI fails if stale; CI also fails if a final score drops below main's, from `scores.json` on the `badges` branch, and posts a main → PR score table as a PR comment via `--comment`): `python3 resume-builder/ats_check.py [--min 89] [--jd job.txt]`; CI (`.github/workflows/ats-check.yml`) runs it on PRs and fails if the generated site files are stale.
- Check a PDF's ATS text order: `pdftotext -layout resumes/<file>.pdf -`.

## Single source of truth

- Edit only `resume-builder/data.yaml` (shared content) and `resume-builder/overrides/{site,india,intl,de}.yaml` (target-specific changes). Never hand-edit `index.html`, `sitemap.xml`, `robots.txt` or `resumes/*`; they are generated and committed (Pages has no build step).
- Overrides are deep-merged over the data. Lists whose items all have `id` merge per id; other lists are replaced. Items with `only: [targets]` are dropped elsewhere (e.g. `apoorva` is site-only).
- `resumes/` (repo root) holds the three PDFs; the site's two buttons (open in a new tab) link to the India and Intl ones via the `resumes` list in `site.yaml`.
- `.github/workflows/resume.yml` is a manual (`workflow_dispatch`) action: pick `india|intl|de|all`, it runs `build.py` and uploads the PDFs as a run artifact (no commit/deploy).
- German translations in `de.yaml` are a draft; DOB, nationality and India CTC/notice fields are empty and omitted until filled.
- The `badges` branch is bot-managed by `.github/workflows/ats-badges.yml` (shields.io endpoint JSON for the README badges, plus `scores.json`, the PR baseline). Don't edit it by hand or protect it.

## Site architecture

- `index.html` is pre-rendered (for SEO and link previews) by `build.py` from `resume-builder/templates/site.html.j2` (Jinja, autoescape on; keep it on). It includes meta/OG tags and JSON-LD `Person` built in `build.py` `json_ld()`. Site-only copy (headline, tagline, highlights, seo) lives in `overrides/site.yaml`. Empty `linkedin` or project `link` hide that element.
- `script.js` (IIFE) adds interactivity only: theme, text size, mobile menu, copy email, nav scroll-spy, `.reveal` fade-in.
- An inline script in `<head>` applies localStorage `theme`/`fontScale` before first paint (falls back to `prefers-color-scheme`) and adds `html.js`, so `.reveal` content stays visible without JS.
- `style.css` themes with CSS variables and a `:root[data-theme="dark"]` override, plus `--font-scale`.

## Knowledge pages

- `knowledge/{ios,system-design,coding}.html` are static shells. `knowledge/kb.js` fetches the manifest named in `<main data-src>` (e.g. `data/ios/manifest.json`), fetches every entry file it lists in parallel, and renders it. These pages are not generated and need no build step.
- Each topic is a folder under `knowledge/data/`: `manifest.json` plus one file per entry (`knowledge/data/coding/coding-challenge-1.json`, `ios-concept-1.json`, `system-design-1.json`, ...). To add an entry: add its numbered file, then add that filename to the topic's `manifest.json` `entries` array.
- `manifest.json` shape: `{ title, intro, categories: [{id, title}, ...], entries: ["<file>.json", ...] }`.
- Entry file fields: `id`, `title`, `category` (must match a category `id` in the manifest), `tags`, `summary`, `body` (strings; `` `code` `` and `**bold**` only; a string starting with ```` ``` ```` is a code block). Optional: `difficulty`, `approach`, `complexity`, `requirements`, `components`, `tradeoffs`, `code`, `solution` (both lists of `{lang, caption, text}`), `keyPoints`, `mistakes`, `followups` (string lists), `links`. Deep link: `knowledge/ios.html#<entry id>`.
- A single bad/missing entry file is skipped (logged to console) rather than blanking the page; a broken manifest shows an error message.
- Home-page cards and the sitemap read the `knowledge` list in `resume-builder/overrides/site.yaml`; rebuild with `python3 resume-builder/build.py site` when that list changes.

Design decisions for these pages are recorded in `knowledge/DECISIONS.md`; read it before changing the renderer or the JSON schema.
