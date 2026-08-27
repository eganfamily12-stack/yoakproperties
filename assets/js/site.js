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


  /* Open houses expire. Each scheduled time is emitted with the date it applies
     to and a fallback block; once that time has passed, swap the fallback in.
     The build does the same substitution server-side, so this only matters for
     visitors who arrive after the site was last built - which, for a static
     site updated by hand, is most of them. Without it the page would keep
     advertising an open house that happened weeks ago. */
  function expireOpenHouses() {
    var now = new Date();

    function stale(el, attr) {
      var when = parseLocal(el.getAttribute(attr));
      if (!when) return false;
      // an open house stays listed until the end of the day it falls on
      var endOfDay = new Date(when.getFullYear(), when.getMonth(), when.getDate(), 23, 59, 59);
      return now > endOfDay;
    }

    // Listing cards: substitute the "times on Zillow" fallback for the date.
    var swap = document.querySelectorAll('[data-openhouse]');
    for (var i = 0; i < swap.length; i++) {
      var el = swap[i];
      if (!stale(el, 'data-openhouse')) continue;
      var tpl = el.querySelector('[data-openhouse-fallback]');
      if (!tpl) continue;
      el.innerHTML = tpl.innerHTML;
      el.removeAttribute('data-openhouse');
    }

    // Home page teaser cards: the card exists only to advertise the date, so
    // drop it rather than leaving an empty shell behind.
    var drop = document.querySelectorAll('[data-openhouse-remove]');
    for (var j = 0; j < drop.length; j++) {
      if (stale(drop[j], 'data-openhouse-remove')) drop[j].remove();
    }

    // If that emptied a teaser group, hide its whole section - a bare heading
    // over nothing looks broken.
    var groups = document.querySelectorAll('[data-openhouse-group]');
    for (var k = 0; k < groups.length; k++) {
      if (groups[k].children.length) continue;
      var section = groups[k].closest('section') || groups[k];
      section.style.display = 'none';
    }
  }

  /* "2026-08-29T10:00" parsed in the visitor's own timezone. Passing this
     string to new Date() directly is treated as UTC by some engines, which
     would shift the cutoff by hours. */
  function parseLocal(iso) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(iso || '');
    if (!m) return null;
    return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
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
    document.addEventListener('DOMContentLoaded', function () { initNav(); expireOpenHouses(); initTocHighlight(); });
  } else {
    initNav();
    expireOpenHouses();
    initTocHighlight();
  }
})();
