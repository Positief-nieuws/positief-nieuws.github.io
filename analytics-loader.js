/* Production analytics policy. See docs/analytics-testing.md. */
(function () {
  'use strict';
  if (window.pnAnalyticsPolicy) return;
  const key = 'pn_internal_analytics_v1';
  const params = new URLSearchParams(location.search);
  const mode = params.get('pn_internal');
  let internal = mode === '1';
  let persisted = false;
  try {
    if (mode === '1') localStorage.setItem(key, '1');
    else if (mode === '0') localStorage.removeItem(key);
    persisted = localStorage.getItem(key) === '1';
  } catch (_) { /* Explicit URL opt-out still protects this page. */ }
  if (mode === '1' || mode === '0') {
    params.delete('pn_internal');
    // Do not pass the exclusion link on when copying/sharing this page.
    try { history.replaceState(history.state, '', location.pathname +
      (params.toString() ? '?' + params.toString() : '') + location.hash); } catch (_) {}
  }
  internal = internal || persisted;
  const production = location.protocol === 'https:' &&
    ['positief-nieuws.nl', 'www.positief-nieuws.nl'].includes(location.hostname) &&
    !location.port;
  const allowed = production && !internal;
  window.pnAnalyticsPolicy = Object.freeze({allowed, internal, persisted, production});
  if (document.documentElement) document.documentElement.setAttribute('data-pn-analytics',
    allowed ? 'production' : internal ? (persisted ? 'internal' : 'internal-temporary') : 'preview');
  if (!allowed) {
    // Drop all queued and future custom events, while leaving forms and sharing intact.
    window.sa_event = function () {};
  }
  let loaded = false;
  window.pnLoadAnalytics = function () {
    if (!allowed || loaded) return;
    loaded = true;
    const script = document.createElement('script');
    script.async = true;
    script.setAttribute('data-hostname', 'positief-nieuws.nl');
    script.setAttribute('data-metadata-collector', 'pnAnalyticsMetadata');
    script.src = 'https://scripts.simpleanalyticscdn.com/latest.js';
    script.addEventListener('load', function () {
      const auto = document.createElement('script');
      auto.async = true;
      auto.setAttribute('data-full-urls', 'true');
      auto.src = 'https://scripts.simpleanalyticscdn.com/auto-events.js';
      (document.body || document.head).appendChild(auto);
    });
    (document.body || document.head).appendChild(script);
  };
})();
