// Interactivity only: all content is pre-rendered into index.html by resume-builder/build.py.
(function () {
  function $(id) { return document.getElementById(id); }
  var root = document.documentElement;
  var toggle = $('theme-toggle');

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* storage unavailable */ }
  }

  function renderToggle() {
    var dark = root.getAttribute('data-theme') === 'dark';
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
  }

  toggle.addEventListener('click', function () {
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    store('theme', next);
    renderToggle();
  });
  renderToggle();

  function changeScale(delta) {
    var current = parseFloat(getComputedStyle(root).getPropertyValue('--font-scale')) || 1;
    var next = Math.min(1.5, Math.max(0.9, Math.round((current + delta) * 100) / 100));
    root.style.setProperty('--font-scale', next);
    store('fontScale', String(next));
  }
  $('font-up').addEventListener('click', function () { changeScale(0.1); });
  $('font-down').addEventListener('click', function () { changeScale(-0.1); });

  var copyBtn = $('copy-email');
  var status = $('copy-status');
  if (copyBtn) copyBtn.addEventListener('click', function () {
    var email = copyBtn.getAttribute('data-email');
    var done = function (msg) { status.textContent = msg; };
    if (navigator.clipboard) {
      navigator.clipboard.writeText(email).then(function () { done('Email copied: ' + email); },
        function () { done('Copy failed. Email: ' + email); });
    } else {
      done('Email: ' + email);
    }
  });

  var nav = document.querySelector('.nav');
  var menuBtn = $('menu-toggle');
  function setMenu(open) {
    nav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }
  menuBtn.addEventListener('click', function () { setMenu(!nav.classList.contains('open')); });
  document.querySelectorAll('.nav a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });

  // Shadow under the nav once the page scrolls.
  function onScroll() { nav.classList.toggle('scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  var reveals = document.querySelectorAll('.reveal');
  var links = document.querySelectorAll('.nav ul a');
  if (!('IntersectionObserver' in window)) {
    reveals.forEach(function (n) { n.classList.add('in'); });
    return;
  }

  // Fade sections in as they enter the viewport (CSS skips this for reduced motion).
  var revealer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); revealer.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px' });
  reveals.forEach(function (n) { revealer.observe(n); });

  // Highlight the nav link of the section in view.
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id); });
      }
    });
  }, { rootMargin: '-40% 0px -55% 0px' });
  document.querySelectorAll('main section[id]').forEach(function (s) { spy.observe(s); });
})();
