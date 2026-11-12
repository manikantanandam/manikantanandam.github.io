// Renders a knowledge page from the JSON file named in <main data-src>.
// Edit the JSON under knowledge/data/ to change content; this file needs no changes.
(function () {
  'use strict';

  var HLJS = 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/';
  var main = document.getElementById('kb');
  var state = { data: null, category: 'all', query: '' };

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // Inline subset only: `code` and **bold**. Built with textContent, never innerHTML.
  function inline(text) {
    var frag = document.createDocumentFragment();
    String(text).split(/(`[^`]+`|\*\*[^*]+\*\*)/).forEach(function (part) {
      if (!part) return;
      if (part[0] === '`' && part.length > 2) frag.appendChild(el('code', null, part.slice(1, -1)));
      else if (part.slice(0, 2) === '**' && part.length > 4) frag.appendChild(el('strong', null, part.slice(2, -2)));
      else frag.appendChild(document.createTextNode(part));
    });
    return frag;
  }

  function codeBlock(snippet) {
    var wrap = el('div', 'kb-code');
    var bar = el('div', 'kb-code-bar');
    bar.appendChild(el('span', 'kb-code-caption', snippet.caption || snippet.lang || 'code'));
    var btn = el('button', 'kb-copy', 'Copy');
    btn.type = 'button';
    btn.addEventListener('click', function () {
      var done = function () { btn.textContent = 'Copied'; setTimeout(function () { btn.textContent = 'Copy'; }, 1500); };
      try {
        navigator.clipboard.writeText(snippet.text).then(done, function () {});
      } catch (e) { /* clipboard unavailable */ }
    });
    bar.appendChild(btn);
    wrap.appendChild(bar);
    var pre = el('pre');
    var code = el('code', 'language-' + (snippet.lang || 'plaintext'));
    code.textContent = snippet.text;
    pre.appendChild(code);
    wrap.appendChild(pre);
    if (window.hljs) window.hljs.highlightElement(code);
    return wrap;
  }

  function list(title, items) {
    if (!items || !items.length) return null;
    var box = el('div', 'kb-block');
    box.appendChild(el('h4', null, title));
    var ul = el('ul');
    items.forEach(function (item) { var li = el('li'); li.appendChild(inline(item)); ul.appendChild(li); });
    box.appendChild(ul);
    return box;
  }

  function renderEntry(entry) {
    var d = el('details', 'kb-entry');
    d.id = entry.id;
    var s = el('summary');
    s.appendChild(el('span', 'kb-entry-title', entry.title));
    if (entry.difficulty) s.appendChild(el('span', 'kb-badge', entry.difficulty));
    d.appendChild(s);

    var body = el('div', 'kb-entry-body');
    if (entry.summary) { var p = el('p', 'kb-summary'); p.appendChild(inline(entry.summary)); body.appendChild(p); }
    if (entry.approach) { var a = el('div', 'kb-block'); a.appendChild(el('h4', null, 'Approach')); var ap = el('p'); ap.appendChild(inline(entry.approach)); a.appendChild(ap); body.appendChild(a); }
    if (entry.complexity) { var c = el('p', 'kb-muted'); c.appendChild(inline('Complexity: ' + entry.complexity)); body.appendChild(c); }

    (entry.body || []).forEach(function (text) {
      if (/^```/.test(text)) {
        var lines = text.split('\n');
        body.appendChild(codeBlock({ lang: lines[0].slice(3).trim(), text: lines.slice(1, -1).join('\n') }));
      } else {
        var para = el('p'); para.appendChild(inline(text)); body.appendChild(para);
      }
    });

    [['Requirements', entry.requirements], ['Components', entry.components], ['Trade-offs', entry.tradeoffs]]
      .forEach(function (pair) { var b = list(pair[0], pair[1]); if (b) body.appendChild(b); });

    (entry.code || []).concat(entry.solution || []).forEach(function (sn) { body.appendChild(codeBlock(sn)); });

    if (entry.links && entry.links.length) {
      var links = el('ul', 'kb-links');
      entry.links.forEach(function (l) {
        var li = el('li'); var a2 = el('a', null, l.label); a2.href = l.url; a2.target = '_blank'; a2.rel = 'noopener';
        li.appendChild(a2); links.appendChild(li);
      });
      body.appendChild(links);
    }

    if (entry.tags && entry.tags.length) {
      var tags = el('ul', 'tags');
      entry.tags.forEach(function (t) { tags.appendChild(el('li', null, t)); });
      body.appendChild(tags);
    }

    d.appendChild(body);
    return d;
  }

  function matches(entry, query) {
    if (!query) return true;
    var text = [entry.title, entry.summary, entry.approach, (entry.tags || []).join(' '), (entry.body || []).join(' ')].join(' ').toLowerCase();
    return text.indexOf(query) !== -1;
  }

  function render() {
    var data = state.data;
    main.textContent = '';
    main.appendChild(el('h1', 'kb-title', data.title));
    if (data.intro) main.appendChild(el('p', 'kb-intro', data.intro));

    var bar = el('div', 'kb-toolbar');
    var search = el('input', 'kb-search');
    search.type = 'search';
    search.placeholder = 'Search topics, tags, text';
    search.setAttribute('aria-label', 'Search entries');
    search.value = state.query;
    search.addEventListener('input', function () { state.query = search.value.trim().toLowerCase(); renderList(listEl); });
    bar.appendChild(search);

    var chips = el('div', 'kb-chips');
    chips.setAttribute('role', 'group');
    chips.setAttribute('aria-label', 'Filter by category');
    var all = [{ id: 'all', title: 'All' }].concat(data.categories);
    all.forEach(function (cat) {
      var b = el('button', 'kb-chip', cat.title);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.category === cat.id));
      b.addEventListener('click', function () { state.category = cat.id; render(); });
      chips.appendChild(b);
    });
    bar.appendChild(chips);
    main.appendChild(bar);

    var listEl = el('div', 'kb-list');
    main.appendChild(listEl);
    renderList(listEl);
    openFromHash();
  }

  function renderList(listEl) {
    listEl.textContent = '';
    var shown = 0;
    state.data.categories.forEach(function (cat) {
      if (state.category !== 'all' && state.category !== cat.id) return;
      var entries = (cat.entries || []).filter(function (e) { return matches(e, state.query); });
      if (!entries.length) return;
      var section = el('section', 'kb-category');
      section.appendChild(el('h2', null, cat.title));
      entries.forEach(function (e) { section.appendChild(renderEntry(e)); shown++; });
      listEl.appendChild(section);
    });
    if (!shown) listEl.appendChild(el('p', 'kb-muted', 'Nothing matches that search.'));
  }

  function openFromHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var target = document.getElementById(id);
    if (target && target.tagName === 'DETAILS') {
      target.open = true;
      target.scrollIntoView({ block: 'start' });
    }
  }

  // Keep highlight.js colors in step with the site theme.
  function syncHighlightTheme() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    var light = document.getElementById('hljs-light');
    var night = document.getElementById('hljs-dark');
    if (light) light.disabled = dark;
    if (night) night.disabled = !dark;
  }

  function loadHighlight() {
    [['hljs-light', 'github.min.css'], ['hljs-dark', 'github-dark.min.css']].forEach(function (pair) {
      var link = document.createElement('link');
      link.id = pair[0];
      link.rel = 'stylesheet';
      link.href = HLJS + 'styles/' + pair[1];
      document.head.appendChild(link);
    });
    var script = document.createElement('script');
    script.src = HLJS + 'highlight.min.js';
    script.onload = function () {
      // Re-highlight blocks already rendered before the library arrived.
      document.querySelectorAll('pre code').forEach(function (c) { window.hljs.highlightElement(c); });
    };
    document.head.appendChild(script);
    new MutationObserver(syncHighlightTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    setTimeout(syncHighlightTheme, 0);
  }

  function fail(err) {
    main.textContent = '';
    main.appendChild(el('p', 'kb-error', 'Could not load this page’s content. Check the manifest file for syntax errors.'));
    console.error(err);
  }

  function showSkeleton() {
    main.textContent = '';
    var box = el('div', 'kb-skeleton-wrap');
    for (var i = 0; i < 3; i++) box.appendChild(el('div', 'kb-skeleton kb-entry'));
    main.appendChild(box);
  }

  function fetchJSON(url) {
    return fetch(url, { cache: 'default' }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + url);
      return r.json();
    });
  }

  // Manifest lists each entry's own small file; fetched in parallel, not one by one,
  // and a single bad/missing entry file doesn't blank the rest of the page.
  function loadTopic(manifestUrl) {
    return fetchJSON(manifestUrl).then(function (manifest) {
      var base = new URL(manifestUrl, location.href);
      var byId = {};
      manifest.categories.forEach(function (c) { byId[c.id] = { id: c.id, title: c.title, entries: [] }; });
      var unfiled = { id: 'uncategorized', title: 'Uncategorized', entries: [] };

      return Promise.allSettled(manifest.entries.map(function (name) {
        return fetchJSON(new URL(name, base));
      })).then(function (results) {
        results.forEach(function (res, i) {
          if (res.status !== 'fulfilled') { console.error('Skipping ' + manifest.entries[i], res.reason); return; }
          var entry = res.value;
          var bucket = byId[entry.category] || unfiled;
          bucket.entries.push(entry);
        });
        var categories = manifest.categories.map(function (c) { return byId[c.id]; });
        if (unfiled.entries.length) categories.push(unfiled);
        return { title: manifest.title, intro: manifest.intro, categories: categories };
      });
    });
  }

  window.addEventListener('hashchange', openFromHash);
  loadHighlight();
  showSkeleton();
  loadTopic(main.getAttribute('data-src'))
    .then(function (data) { state.data = data; render(); })
    .catch(fail);
})();
