# Knowledge pages: decisions

Decisions behind `knowledge/`, kept here so they travel with the repo.

## 1. Content is rendered from JSON in the browser
- `knowledge/{ios,system-design,coding}.html` are static shells. `knowledge/kb.js` fetches the JSON named in `<main data-src>`.
- Why: editing `knowledge/data/*.json` and pushing is enough. No Python, Chrome or build step.
- Not routed through `resume-builder/build.py`, so content edits never trip the CI "generated files are stale" check.
- Trade-off: the content is not pre-rendered, so search engines see less than they do for the home page. Accepted for a personal notes repo.

## 2. Three separate pages, one per topic
- iOS, System Design and Coding Challenges each have their own page and JSON file.
- Each entry has its own anchor (`#<entry id>`) for deep links.

## 3. No difficulty levels (basic / intermediate / advanced)
- Explicitly rejected by the user. Do not add a `level` field.
- Coding challenges may still use `difficulty` (Easy / Medium / Hard), which is a property of the problem, not a learning tier.

## 4. Every code snippet is a code block
- Snippets from `code`, `solution`, and ```` ``` ```` fences in `body` all render as `<pre><code>` with a language label and a Copy button.
- Syntax highlighting uses highlight.js 11.9.0 from cdnjs, with light and dark themes switched by `data-theme`.

## 5. Safe text handling
- JSON text is inserted with `textContent`. The only markup in text is inline `` `code` `` and `**bold**`.
- No `innerHTML` for content from JSON.

## 6. Home-page cards and sitemap come from `site.yaml`
- The `knowledge` list in `resume-builder/overrides/site.yaml` drives the home cards and the `sitemap.xml` entries.
- Changing that list requires `python3 resume-builder/build.py site`.

## 7. Rendering failures are visible
- If the JSON is missing or invalid, the page shows a short error message instead of a blank page.
