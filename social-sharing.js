/* Sharing reports intent, clipboard success and native-menu requests, never delivery. */
(function () {
  'use strict';
  if (window.pnSocialSharing) return;
  window.pnSocialSharing = true;
  function start() {
    document.querySelectorAll('.article-share, .pn-share').forEach(function (block) {
      if (block.dataset.shareBound) return;
      block.dataset.shareBound = 'true';
      const kind = block.dataset.shareType || ((window.sa_metadata || {}).page_type === 'special' ? 'special' : 'article');
      const status = block.querySelector('[role="status"]');
      const fallback = block.querySelector('.article-copy-fallback, .pn-share-fallback');
      const native = block.querySelector('#article-native-share, [data-share-action="native"]');
      const copy = block.querySelector('#article-copy-link, [data-share-action="copy"]');
      function data() {
        const canonical = document.querySelector('link[rel="canonical"]').href;
        let url = canonical;
        let title = document.querySelector('meta[property="og:title"]').content;
        if (kind === 'edition' && block.dataset.shareHome === 'true') {
          const date = String((window.sa_metadata || {}).edition || '');
          if (/^\d{4}-\d{2}-\d{2}$/.test(date)) {
            url = new URL('/edities/' + date + '/', canonical).href;
            title = 'Positief nieuws · ' + date;
          }
        }
        return {url: url, title: title};
      }
      function track(name, method, extra) {
        const d = data(), current = window.sa_metadata || {};
        const metadata = Object.assign({}, window.pnAnalyticsMetadata ? window.pnAnalyticsMetadata() : {}, {
          page_type: current.page_type || (kind === 'edition' ? 'edition' : kind),
          page_path: location.pathname, article_title: d.title,
          article_category: current.category || 'overig',
          article_url: d.url, placement: kind === 'article' ? 'article_end' : kind === 'special' ? 'special_end' : kind,
          channel: method, share_method: method
        }, extra || {});
        if (window.sa_event) window.sa_event(name, metadata);
      }
      function clicked(method) {
        const event = kind === 'article' ? 'article_share_click' : kind === 'special' ? 'special_share_click' : kind === 'newsletter' ? 'newsletter_share_click' : 'share_edition';
        track(event, method, {share_status: 'clicked'});
      }
      function links() {
        const d = data();
        block.querySelectorAll('[data-share-channel="whatsapp"]').forEach(function (link) {
          link.href = 'https://wa.me/?text=' + encodeURIComponent(d.title + '\n\n' + d.url);
        });
      }
      links();
      block.querySelectorAll('[data-share-channel]').forEach(function (link) {
        link.addEventListener('click', function () {links(); clicked(link.dataset.shareChannel);});
      });
      if (native && navigator.share) {
        native.hidden = false;
        native.addEventListener('click', async function () {
          clicked('native');
          try {
            const request = navigator.share({title: data().title, text: data().title, url: data().url});
            track('share_menu_open', 'native', {share_status: 'requested'});
            await request;
          } catch (error) {
            if (error.name !== 'AbortError' && status) status.textContent = 'Delen lukte niet. Gebruik WhatsApp of kopieer de link.';
          }
        });
      }
      if (copy) copy.addEventListener('click', async function () {
        clicked('copy');
        try {
          await navigator.clipboard.writeText(data().url);
          if (status) status.textContent = 'Link gekopieerd. Klaar om door te sturen.';
          track(kind === 'article' ? 'article_link_copy' : kind + '_link_copy', 'copy', {share_status: 'copied'});
        } catch (_) {
          if (fallback) {
            fallback.hidden = false;
            const input = fallback.querySelector('input');
            input.value = data().url; input.focus(); input.select();
          }
          if (status) status.textContent = 'Selecteer en kopieer de link hieronder.';
        }
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
