/* Yoak Properties — site behaviour.
   The mockups shipped a mobile menu button with no panel and no script,
   which left phone visitors with no navigation at all. This wires it up. */
(function () {
  'use strict';

  function initNav() {
    var toggle = document.getElementById('nav-toggle');
    var panel = document.getElementById('mobile-nav');
    if (!toggle || !panel) return;

    var iconOpen = toggle.querySelector('[data-icon="open"]');
    var iconClose = toggle.querySelector('[data-icon="close"]');

    function setOpen(open) {
      panel.classList.toggle('hidden', !open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      if (iconOpen) iconOpen.classList.toggle('hidden', open);
      if (iconClose) iconClose.classList.toggle('hidden', !open);
    }

    toggle.addEventListener('click', function () {
      setOpen(panel.classList.contains('hidden'));
    });

    // Close on Escape, and return focus to the button.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.classList.contains('hidden')) {
        setOpen(false);
        toggle.focus();
      }
    });

    // Close when a link inside is followed.
    panel.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });

    // If the viewport grows past the mobile breakpoint while the panel is
    // open, hide it so it can't linger over the desktop layout.
    var mq = window.matchMedia('(min-width: 768px)');
    var onChange = function (e) { if (e.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener('change', onChange);
    else if (mq.addListener) mq.addListener(onChange);

    setOpen(false);
  }

  /* Mark the in-page "Contents" link matching the section currently on
     screen (privacy / terms). No-ops on pages without one. */
  function initTocHighlight() {
    var links = Array.prototype.slice.call(
      document.querySelectorAll('[data-toc] a[href^="#"]')
    );
    if (!links.length || !('IntersectionObserver' in window)) return;

    var byId = {};
    var targets = [];
    links.forEach(function (a) {
      var el = document.getElementById(a.getAttribute('href').slice(1));
      if (el) { byId[el.id] = a; targets.push(el); }
    });

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var a = byId[entry.target.id];
        if (!a) return;
        a.classList.toggle('text-heritage-gold', entry.isIntersecting);
        a.classList.toggle('font-bold', entry.isIntersecting);
      });
    }, { rootMargin: '-96px 0px -60% 0px' });

    targets.forEach(function (t) { observer.observe(t); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initNav(); initTocHighlight(); });
  } else {
    initNav();
    initTocHighlight();
  }
})();
