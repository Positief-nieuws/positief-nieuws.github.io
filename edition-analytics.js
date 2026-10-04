/* Edition-level analytics. No visitor identifiers or form values are collected. */
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
      measurement_version: 'edition-v1'
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
    return form.closest('.article-growth') ? (pageType === 'special' ? 'special_end' : 'article_end') : (pageType === 'homepage' ? 'homepage' : pageType);
  }
  function newsletterForms() {
    return Array.from(document.querySelectorAll('form[action*="buttondown.com"][action*="embed-subscribe"]'));
  }
  function refreshForms() {
    newsletterForms().forEach(function (form) {
      const fields = {signup_edition: context().edition, signup_page_type: context().page_type, signup_source: placement(form)};
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
      if (!newsletterForms().includes(form) || event.defaultPrevented) return;
      refreshForms();
      track('newsletter_submit', {placement: placement(form), signup_status: 'submitted'});
    });
    setInterval(readingTick, 1000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true}); else start();
})();
