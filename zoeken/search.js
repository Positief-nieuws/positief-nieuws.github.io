(() => {
  'use strict';
  const input = document.querySelector('#search-input');
  const form = document.querySelector('#search-form');
  const status = document.querySelector('#search-status');
  const results = document.querySelector('#search-results');
  const more = document.querySelector('#search-more');
  const category = document.querySelector('#search-category');
  const region = document.querySelector('#search-region');
  const kind = document.querySelector('#search-type');
  const params = new URLSearchParams(location.search);
  input.value = params.get('q') || '';
  let index = [], matches = [], visible = 15;
  const normalize = text => String(text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('nl').replace(/[^a-z0-9]+/g, ' ').trim();
  const clean = value => String(value || '').trim();
  const element = (tag, css, value) => {
    const el = document.createElement(tag);
    if (css) el.className = css;
    if (value !== undefined) el.textContent = value;
    return el;
  };
  const createCard = item => {
    const card = element('article', 'result');
    if (item.image && item.type === 'artikel') {
      const photo = element('img', 'result-thumb');
      photo.src = item.image;
      photo.alt = '';
      photo.loading = 'lazy';
      card.append(photo);
    }
    const main = element('div', 'result-main');
    const pieces = [item.type === 'artikel' ? 'Nieuwsartikel' : item.type === 'special' ? 'Special' : 'Informatiepagina'];
    if (item.category) pieces.push(item.category);
    if (item.date) pieces.push(item.date.split('-').reverse().join('-'));
    main.append(element('div', 'result-meta', pieces.join(' · ')));
    const heading = element('h2');
    const link = element('a', '', item.title);
    link.href = item.url;
    heading.append(link);
    main.append(heading);
    const phrase = clean(item.teaser || item.body).slice(0, 240);
    if (phrase) main.append(element('p', '', phrase));
    card.append(main);
    return card;
  };
  const score = (item, words) => {
    const fields = [item.title, item.teaser, item.body, item.category, item.source].map(normalize);
    if (!words.every(w => fields.some(f => f.includes(w)))) return 0;
    return words.reduce((total, w) => total
      + (fields[0].includes(w) ? 12 : 0)
      + (fields[1].includes(w) ? 5 : 0)
      + (fields[2].includes(w) ? 2 : 0)
      + (fields[3].includes(w) ? 4 : 0)
      + (fields[4].includes(w) ? 2 : 0), 0);
  };
  function show() {
    results.replaceChildren();
    for (const item of matches.slice(0, visible)) results.append(createCard(item));
    more.hidden = matches.length <= visible;
    if (!matches.length) {
      const empty = element('div', 'search-empty');
      empty.append(element('h2', '', 'Geen resultaten gevonden'));
      empty.append(element('p', '', 'Probeer een ander zoekwoord of zet de filters op Alle.'));
      results.append(empty);
    }
    const query = clean(input.value);
    status.textContent = matches.length + (matches.length === 1 ? ' resultaat' : ' resultaten') + (query ? ' voor "' + query.slice(0, 90) + '"' : ' op de site');
  }
  function search() {
    const raw = clean(input.value);
    const words = normalize(raw).split(' ').filter(Boolean);
    const type = kind.value;
    const cat = category.value;
    const reg = region.value;
    visible = 15;
    matches = index.filter(item =>
      (!type || item.type === type) &&
      (!cat || item.category === cat) &&
      (!reg || item.region === reg)
    ).map(item => ({...item, score: words.length ? score(item, words) : 1}))
     .filter(item => item.score > 0);
    matches.sort((a,b) => (b.score - a.score) || String(b.date).localeCompare(String(a.date)) || a.title.localeCompare(b.title, 'nl'));
    show();
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    const q = clean(input.value);
    const next = new URL(location.href);
    if (q) next.searchParams.set('q', q);
    else next.searchParams.delete('q');
    history.replaceState(null, '', next);
    search();
  });
  let debounce;
  input.addEventListener('input', () => { clearTimeout(debounce); debounce = setTimeout(() => {
    const next = new URL(location.href);
    if (clean(input.value)) next.searchParams.set('q', clean(input.value));
    else next.searchParams.delete('q');
    history.replaceState(null, '', next);
    search();
  }, 180); });
  [category, kind, region].forEach(node => node.addEventListener('change', search));
  more.addEventListener('click', () => {visible += 15; show();});
  fetch('/zoeken/index.json', {cache:'no-store'})
    .then(response => {if (!response.ok) throw Error('HTTP ' + response.status); return response.json();})
    .then(data => {
      if (!data || !Array.isArray(data.items)) throw Error('Ongeldige zoekindex');
      index = data.items.filter(item => item && item.title && item.url && /^\/(?!\/)/.test(item.url));
      const options = [...new Set(index.map(item => clean(item.category)).filter(Boolean))].sort((a,b) => a.localeCompare(b,'nl'));
      for (const value of options) {const option = document.createElement('option'); option.value = value; option.textContent = value; category.append(option);}
      search();
    })
    .catch(error => {status.textContent = 'Zoeken is tijdelijk niet beschikbaar. Probeer het later opnieuw.'; console.error('Zoekindex:', error);});
})();