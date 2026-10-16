/* Edition and newsletter conversion analytics. No visitor identifiers or raw referrers are collected. */
(function () {
  'use strict';
  if (window.pnEditionAnalytics) return;
  window.pnEditionAnalytics = true;
  const config = document.currentScript.dataset;
  const pageType = config.pageType || 'other';
  const requested = pageType === 'homepage' ? new URLSearchParams(location.search).get('edition') : null;
  let edition = requested ? '' : (config.edition || '');
  let homepageReady = pageType !== 'homepage';
  let observeForms = function () {};
  const weekdays = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

  // Privacy-friendly first-touch attribution, kept only for this browser tab/session.
  // No cookies, visitor identifiers, email addresses, or raw referring URLs.
  function acquisition() {
    const sources = ['google','bing','duckduckgo','ecosia','facebook','instagram','threads',
      'linkedin','reddit','whatsapp','pinterest','youtube','buttondown','newsletter'];
    const channels = ['search','social','email','referral','direct','paid'];
    function recognized(value) {
      const text = String(value || '').toLowerCase().trim().replace(/^www\./, '');
      return sources.find(function (item) { return text === item || text.startsWith(item + '.'); }) || '';
    }
    const params = new URLSearchParams(location.search);
    const medium = String(params.get('utm_medium') || '').toLowerCase();
    let source = recognized(params.get('utm_source'));
    let channel = '';
    if (source) {
      if (['google','bing','duckduckgo','ecosia'].includes(source)) channel = 'search';
      else if (source === 'buttondown' || source === 'newsletter') channel = 'email';
      else channel = 'social';
    }
    if (['email','newsletter'].includes(medium)) channel = 'email';
    else if (['cpc','ppc','paid','paid_social','display'].includes(medium)) channel = 'paid';
    else if (medium === 'social') channel = 'social';
    else if (medium === 'organic') channel = channel || 'search';
    if (!channel) {
      try {
        const ref = document.referrer ? new URL(document.referrer) : null;
        const hostname = ref && ref.origin !== location.origin ? ref.hostname.toLowerCase() : '';
        if (hostname) {
          source = recognized(hostname);
          channel = source
            ? (['google','bing','duckduckgo','ecosia'].includes(source) ? 'search' :
              ['buttondown','newsletter'].includes(source) ? 'email' : 'social')
            : 'referral';
        } else channel = 'direct';
      } catch (_) { channel = 'direct'; }
    }
    const fresh = {traffic_channel: channel, traffic_source: source || 'other', entry_page: location.pathname || '/'};
    try {
      const stored = JSON.parse(sessionStorage.getItem('pn_acquisition_v1') || 'null');
      if (stored && channels.includes(stored.traffic_channel) &&
          (sources.includes(stored.traffic_source) || stored.traffic_source === 'other') &&
          /^\/(?!\/)[\w\/-]*$/.test(stored.entry_page)) return stored;
      sessionStorage.setItem('pn_acquisition_v1', JSON.stringify(fresh));
    } catch (_) { /* Session storage unavailable: use current page only. */ }
    return fresh;
  }
  const entry = acquisition();
  function safeCategory() {
    const value = String((window.sa_metadata || {}).category || '').trim();
    return ['Mens','Natuur & klimaat','Gezondheid','Energie & innovatie',
      'Wetenschap','Cultuur','Economie','Sport'].includes(value) ? value : 'overig';
  }

  function validDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return false;
    const date = new Date(value + 'T12:00:00Z');
    return !isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value;
  }
  function context() {
    const current = window.sa_metadata || {};
    const date = validDate(current.edition) ? current.edition : (validDate(edition) ? edition : 'none');
    return {
      edition: date,
      edition_weekday: date === 'none' ? 'none' : weekdays[new Date(date + 'T12:00:00Z').getUTCDay()],
      page_type: current.page_type || (requested ? 'edition' : pageType),
      measurement_version: 'edition-v1',
      funnel_version: 'newsletter-v1',
      traffic_channel: entry.traffic_channel,
      traffic_source: entry.traffic_source,
      entry_page: entry.entry_page,
      current_page: location.pathname
    };
  }
  window.pnAnalyticsMetadata = context;
  window.pnSetEdition = function (value) {
    edition = validDate(value) ? value : (!requested && pageType === 'homepage' ? config.edition || '' : '');
    homepageReady = true;
    window.sa_metadata = Object.assign({}, window.sa_metadata, {edition: edition || 'none', page_type: requested ? 'edition' : pageType});
    refreshForms();
    resetReading();
    announceView();
    observeForms();
  };
  window.sa_metadata = Object.assign({}, window.sa_metadata, context());
  window.sa_event = window.sa_event || function () {
    const args = [].slice.call(arguments);
    (window.sa_event.q = window.sa_event.q || []).push(args);
  };
  function track(name, extra) {
    window.sa_event(name, Object.assign({}, context(), extra || {}));
  }
  function placement(form) {
    if (form.dataset.newsletterPlacement) return form.dataset.newsletterPlacement;
    return form.closest('.article-growth') ? (pageType === 'special' ? 'special_end' : 'article_end') : (pageType === 'homepage' ? 'homepage' : pageType);
  }
  function newsletterForms() {
    return Array.from(document.querySelectorAll('form[action*="buttondown.com"][action*="embed-subscribe"]'));
  }
  function refreshForms() {
    newsletterForms().forEach(function (form) {
      const fields = {
        signup_edition: context().edition,
        signup_page_type: context().page_type,
        signup_source: placement(form),
        signup_traffic_channel: entry.traffic_channel,
        signup_traffic_source: entry.traffic_source,
        signup_entry_page: entry.entry_page,
        signup_page_path: location.pathname,
        signup_category: safeCategory()
      };
      Object.keys(fields).forEach(function (key) {
        const name = 'metadata__' + key;
        let field = form.querySelector('input[name="' + name + '"]');
        if (!field) {
          field = document.createElement('input'); field.type = 'hidden'; field.name = name; form.appendChild(field);
        }
        field.value = fields[key];
      });
    });
  }
  const views = new Set();
  function announceView() {
    const c = context();
    if (!homepageReady || !['homepage', 'edition', 'article'].includes(c.page_type) || c.edition === 'none') return;
    const key = c.page_type + ':' + c.edition;
    if (!views.has(key)) { views.add(key); track('edition_view'); }
  }
  let visibleMs = 0, previousTime = performance.now(), depth = 0, readSent = false;
  function resetReading() { visibleMs = 0; previousTime = performance.now(); depth = 0; readSent = false; }
  function readingTick() {
    const now = performance.now();
    if (document.visibilityState === 'visible') visibleMs += Math.min(now - previousTime, 2000);
    previousTime = now;
    const content = pageType === 'article' ? document.querySelector('main .article-body, main') : document.querySelector('#today-view, main');
    if (!content) return;
    const rect = content.getBoundingClientRect();
    const progress = Math.max(0, Math.min(1, (window.innerHeight - rect.top) / Math.max(1, rect.height)));
    depth = Math.max(depth, Math.round(progress * 100));
    const c = context();
    if (!readSent && c.edition !== 'none' && ['homepage','edition','article'].includes(c.page_type) && visibleMs >= 30000 && depth >= 50) {
      readSent = true; track('edition_engaged', {active_seconds: Math.floor(visibleMs / 1000), content_depth: depth});
    }
  }
  document.addEventListener('visibilitychange', function () { previousTime = performance.now(); });
  function start() {
    refreshForms(); announceView();
    if (location.pathname.replace(/\/+$/, '') === '/nieuwsbrief') {
      track('newsletter_landing_view', {landing_type: 'dedicated'});
    }
    const seen = new WeakMap();
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          const current = context().edition;
          if (homepageReady && entry.isIntersecting && seen.get(entry.target) !== current) {
            seen.set(entry.target, current);
            track('newsletter_view', {placement: placement(entry.target)});
          }
        });
      }, {threshold: 0.5});
      observeForms = function () { newsletterForms().forEach(function (form) { observer.unobserve(form); observer.observe(form); }); };
      observeForms();
    }
    document.addEventListener('submit', function (event) {
      const form = event.target;
      if (!newsletterForms().includes(form) || event.defaultPrevented || !form.checkValidity()) return;
      refreshForms();
      track('newsletter_form_submit', {
        placement: placement(form), signup_status: 'submitted_unconfirmed',
        content_category: safeCategory()
      });
    });
    document.addEventListener('click', function (event) {
      const cta = event.target.closest('[data-newsletter-cta], form[action*="buttondown.com"] button[type="submit"], form[action*="buttondown.com"] input[type="submit"]');
      if (!cta) return;
      const form = cta.closest('form');
      track('newsletter_cta_click', {
        placement: cta.dataset.newsletterCta || (form ? placement(form) : 'other'),
        content_category: safeCategory()
      });
    });
    // No confirmed event: a public thank-you URL cannot prove Buttondown activation.
    setInterval(readingTick, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true}); else start();
})();
