# Knowledge pages: decisions

Decisions behind `knowledge/`, kept here so they travel with the repo.

## 1. Content is rendered from JSON in the browser
- `knowledge/{ios,system-design,coding}.html` are static shells. `knowledge/kb.js` fetches a manifest and the entry files it lists.
- Why: editing files under `knowledge/data/` and pushing is enough. No Python, Chrome or build step.
- Not routed through `resume-builder/build.py`, so content edits never trip the CI "generated files are stale" check.
- Trade-off: the content is not pre-rendered, so search engines see less than they do for the home page. Accepted for a personal notes repo.

## 1a. One file per entry, with a manifest per topic
- Each topic is a folder (`knowledge/data/ios/`, `/system-design/`, `/coding/`) holding `manifest.json` plus one numbered file per entry (`coding-challenge-1.json`, `ios-concept-1.json`, `system-design-1.json`, ...).
- Explicitly chosen over auto-numbered 404-probing: the manifest lists filenames up front, so loading doesn't guess at an upper bound, order/gaps don't matter, and adding an entry is "add a file + add its name to the manifest."
- `kb.js` fetches every entry file in parallel (`Promise.allSettled`), not one at a time, and reconstructs the categories shape the renderer already expects. A single bad/missing entry file is skipped rather than blanking the page.

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

## 6a. JSON is fetched with `cache: 'no-cache'`
- The browser revalidates every manifest/entry file (cheap 304 when unchanged), so edits show up on a normal reload.
- `cache: 'default'` let browsers reuse a stale manifest from heuristic caching (no `Cache-Control` from `python3 -m http.server`), hiding newly added entries.

## 7. Rendering failures are visible
- If the JSON is missing or invalid, the page shows a short error message instead of a blank page.

## 8. iOS entries are written for revision, in plain English
- The user found the original iOS notes too technical. Entries now lead with a one-line `summary`, then `body` paragraphs starting "In simple words" (plus an analogy where it helps), then the interview-facing lists.
- Three optional string-list fields, rendered by `kb.js` as headed lists: `keyPoints` ("Say this in the interview", before code), `mistakes` ("Common mistakes") and `followups` ("Likely follow-up questions", `**Q?** answer`), both after code. `keyPoints` and `followups` are searchable.
- Other topics can adopt these fields; entries without them render as before.
- Coverage targets a staff iOS interview: Swift basics through concurrency, SwiftUI/UIKit, performance, architecture and patterns, platform, accessibility/localization, security, testing/debugging/release, and a staff engineer playbook (migrations, leadership).
