/* PN feedback. No external request until the visitor opens the form. */
(function () {
  'use strict';
  // Activation requires a published, tested Tally form. No credentials belong here.
  const formId = '';
  if (!/^[a-zA-Z0-9]+$/.test(formId) || window.pnFeedback) return;
  window.pnFeedback = true;
  function start() {
    if (!document.querySelector('.site-header')) return;
    const css = document.createElement('link');
    css.rel = 'stylesheet'; css.href = '/feedback.css?v=1'; document.head.append(css);
    const dialog = document.createElement('dialog');
    dialog.className = 'pn-feedback-dialog'; dialog.setAttribute('aria-labelledby', 'pn-feedback-title');
    dialog.innerHTML = '<div class="pn-feedback-heading"><h2 id="pn-feedback-title">Laat van je horen</h2><button type="button" class="pn-feedback-close" aria-label="Formulier sluiten">Sluiten ×</button></div><p class="pn-feedback-intro">Een tip, idee of foutje? Ik hoor het graag.</p><div class="pn-feedback-frame"></div><p class="pn-feedback-fallback">Lukt het formulier niet? <a href="mailto:redactie@positief-nieuws.nl">Mail de redactie</a>.</p>';
    document.body.append(dialog);
    const holder = dialog.querySelector('.pn-feedback-frame');
    let frame, opener, context, submitted = false;
    const seen = new Set(); // In memory only; never sent to analytics.
    function track(name) {
      if (window.pnAnalyticsPolicy && window.pnAnalyticsPolicy.allowed && window.sa_event)
        window.sa_event(name, {feedback_page: context.page, feedback_placement: context.placement});
    }
    function open(button) {
      if (dialog.open) return;
      opener = button;
      context = {page: location.pathname, placement: button.dataset.feedbackPlacement || 'floating'};
      submitted = false;
      frame = document.createElement('iframe');
      frame.title = 'Feedback of nieuwstip voor Positief Nieuws'; frame.referrerPolicy = 'no-referrer';
      // Deliberately exclude query parameters, fragments and page titles.
      const url = new URL('https://tally.so/embed/' + formId);
      url.search = new URLSearchParams({hideTitle:'1', transparentBackground:'1', alignLeft:'1', originPage:context.page}).toString();
      frame.src = url.href; holder.replaceChildren(frame);
      dialog.showModal(); document.documentElement.classList.add('pn-feedback-open');
      dialog.querySelector('button').focus(); track('feedback_open');
    }
    dialog.querySelector('button').addEventListener('click', () => dialog.close());
    dialog.addEventListener('close', () => {
      document.documentElement.classList.remove('pn-feedback-open');
      holder.replaceChildren(); frame = null;
      if (opener && opener.isConnected) opener.focus();
    });
    window.addEventListener('message', event => {
      if (!dialog.open || !frame || event.origin !== 'https://tally.so' || event.source !== frame.contentWindow) return;
      let data;
      try { data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data; } catch (_) { return; }
      if (!data || data.event !== 'Tally.FormSubmitted' || !data.payload || data.payload.formId !== formId) return;
      const id = data.payload.id;
      if (submitted || typeof id !== 'string' || !id || seen.has(id)) return;
      submitted = true; seen.add(id);
      // Never forward payload, answers, email, respondent ID or submission ID.
      track('feedback_submit');
    });
    function button(label, placement) {
      const el = document.createElement('button'); el.type = 'button';
      el.className = 'pn-feedback-button'; el.dataset.feedbackPlacement = placement;
      el.setAttribute('aria-haspopup', 'dialog');
      el.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 4h16v12H9l-5 4V4Z"/></svg><span></span>';
      el.querySelector('span').textContent = label;
      el.addEventListener('click', () => open(el)); return el;
    }
    const floating = button('Feedback of tip?', 'floating');
    floating.classList.add('pn-feedback-floating'); document.body.append(floating);
    const main = document.querySelector('main');
    if (main && /^\/(artikelen|specials)\/.+/.test(location.pathname)) {
      const invite = document.createElement('aside'); invite.className = 'pn-feedback-invite';
      const p = document.createElement('p');
      p.textContent = 'Een idee, nieuwstip of suggestie? Laat het ons weten. Samen maken we Positief Nieuws beter.';
      invite.append(p, button('Deel je reactie', 'story')); main.append(invite);
    }
    if (main && /^\/(contact|tip)\//.test(location.pathname)) {
      const box = document.createElement('section'); box.className = 'pn-feedback-invite';
      const p = document.createElement('p'); p.textContent = 'Stuur eenvoudig je feedback, nieuwstip, idee of foutmelding. Je e-mailadres is niet verplicht.';
      box.append(p, button('Feedback of tip insturen', 'contact'));
      const intro = main.querySelector('.intro');
      if (intro) intro.after(box); else main.append(box);
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true}); else start();
})();
