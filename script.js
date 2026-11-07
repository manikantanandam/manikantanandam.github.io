(function () {
  var cfg = window.SITE_CONFIG || {};
  var c = cfg.contact || {};
  var social = cfg.social || {};

  function $(id) { return document.getElementById(id); }
  // Build elements with textContent only, so config values are never parsed as HTML.
  function el(tag, props, children) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      if (k === 'text') n.textContent = props[k]; else n.setAttribute(k, props[k]);
    });
    (children || []).forEach(function (ch) { n.appendChild(ch); });
    return n;
  }
  function link(text, href, cls, external) {
    var a = el('a', { text: text, href: href, 'class': 'btn ' + (cls || '') });
    if (external) { a.target = '_blank'; a.rel = 'noopener'; }
    return a;
  }
  function list(items) {
    return el('ul', {}, (items || []).map(function (i) { return el('li', { text: i }); }));
  }

  var waUrl = c.whatsapp
    ? 'https://wa.me/' + c.whatsapp + '?text=' + encodeURIComponent(c.whatsappMessage || '')
    : '';

  document.title = cfg.name + ' | ' + cfg.title;
  document.querySelector('meta[name="description"]').content = 'Portfolio of ' + cfg.name + ', ' + cfg.title + '.';
  document.querySelector('meta[property="og:title"]').content = document.title;
  $('brand').textContent = cfg.initials || cfg.name;
  $('photo').src = cfg.photo;
  $('photo').alt = 'Portrait of ' + cfg.name;
  $('hero-name').textContent = "Hi, I'm " + cfg.name;
  $('hero-title').textContent = cfg.title;
  $('hero-intro').textContent = cfg.intro;

  var heroCta = $('hero-cta');
  if (waUrl) heroCta.appendChild(link('💬 Chat on WhatsApp', waUrl, 'btn-whatsapp', true));
  if (cfg.resume) {
    var dl = link('⬇ Download Resume', cfg.resume);
    dl.setAttribute('download', '');
    heroCta.appendChild(dl);
  }
  if (social.github) heroCta.appendChild(link('GitHub', social.github, 'btn-ghost', true));
  if (social.linkedin) heroCta.appendChild(link('LinkedIn', social.linkedin, 'btn-ghost', true));

  (cfg.about || []).forEach(function (p) { $('about-body').appendChild(el('p', { text: p })); });

  (cfg.skills || []).forEach(function (s) {
    $('skills-body').appendChild(el('div', { 'class': 'card' }, [el('h3', { text: s.title }), list(s.items)]));
  });

  (cfg.experience || []).forEach(function (e) {
    var h = el('h3', { text: e.role + ', ' + e.company + ' ' }, [el('span', { 'class': 'muted', text: '· ' + e.period })]);
    $('experience-body').appendChild(el('article', { 'class': 'card' }, [h, list(e.points)]));
  });

  (cfg.projects || []).forEach(function (p) {
    var kids = [el('h3', { text: p.name }), el('p', { text: p.description }),
      el('p', { 'class': 'tags' }, (p.tags || []).map(function (t) { return el('span', { text: t }); }))];
    if (p.link) kids.push(el('a', { text: 'View project →', href: p.link, target: '_blank', rel: 'noopener' }));
    $('projects-body').appendChild(el('article', { 'class': 'card' }, kids));
  });

  var contactCta = $('contact-cta');
  if (waUrl) contactCta.appendChild(link('💬 Chat on WhatsApp', waUrl, 'btn-whatsapp', true));
  if (c.email) {
    contactCta.appendChild(link('✉ Email me', 'mailto:' + c.email + '?subject=' + encodeURIComponent(c.emailSubject || ''), ''));
    contactCta.appendChild(el('button', { type: 'button', 'class': 'btn btn-ghost', id: 'copy-email', 'data-email': c.email, text: 'Copy email' }));
  }
  if (c.phone) contactCta.appendChild(link('📞 Call', 'tel:' + c.phone, 'btn-ghost'));

  $('footer').textContent = '© ' + new Date().getFullYear() + ' ' + cfg.name;
  if (waUrl) { $('fab').href = waUrl; $('fab').hidden = false; }

  var root = document.documentElement;
  var toggle = $('theme-toggle');

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* storage unavailable */ }
  }

  function renderToggle() {
    var dark = root.getAttribute('data-theme') === 'dark';
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    toggle.textContent = dark ? '☀️ Light' : '🌙 Dark';
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
  document.getElementById('font-up').addEventListener('click', function () { changeScale(0.1); });
  document.getElementById('font-down').addEventListener('click', function () { changeScale(-0.1); });

  var copyBtn = document.getElementById('copy-email');
  var status = document.getElementById('copy-status');
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

  // Highlight the nav link of the section in view.
  var links = document.querySelectorAll('.nav ul a');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id); });
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    document.querySelectorAll('main section[id]').forEach(function (s) { io.observe(s); });
  }
})();
