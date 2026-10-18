/* No network: test production loading and exclusion across independent page loads. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('analytics-loader.js', 'utf8');
function page(url, storage = new Map(), denied = false) {
  const location = new URL(url), scripts = [], changes = [];
  const document = {createElement: () => ({attrs:{}, setAttribute(k,v){this.attrs[k]=v;},
    addEventListener(k,v){this[k]=v;}}), head:{appendChild:s=>scripts.push(s)}};
  document.body=document.head;
  const window={sa_event:Object.assign(()=>{}, {q:[['old_event']]})};
  const context={window,document,location,URLSearchParams,
    localStorage:{getItem:k=>{if(denied)throw Error();return storage.get(k);},
      setItem:(k,v)=>{if(denied)throw Error();storage.set(k,v);},
      removeItem:k=>{if(denied)throw Error();storage.delete(k);}},
    history:{state:null,replaceState:(_,__,url)=>changes.push(url)}};
  vm.runInNewContext(source,context);
  window.pnLoadAnalytics();window.pnLoadAnalytics();
  return {window,scripts,changes,context};
}
const regular=page('https://positief-nieuws.nl/');
assert.equal(regular.scripts.length,1);
assert.equal(regular.scripts[0].attrs['data-hostname'],'positief-nieuws.nl');
regular.scripts[0].load();assert.equal(regular.scripts.length,2);
assert.match(regular.scripts[1].src,/auto-events/);
vm.runInNewContext(source,regular.context);regular.window.pnLoadAnalytics();
assert.equal(regular.scripts.length,2);
for(const url of ['http://localhost:8000/','http://127.0.0.1:8000/','file:///tmp/index.html',
 'https://preview.example/','https://positief-nieuws.github.io/','https://positief-nieuws.nl:8000/',
 'http://positief-nieuws.nl/']) {
 const t=page(url);assert.equal(t.scripts.length,0,url);assert.equal(t.window.sa_event.q,undefined);
}
const storage=new Map();
const excluded=page('https://positief-nieuws.nl/?pn_internal=1&utm_campaign=excluded#test',storage);
assert.equal(excluded.scripts.length,0);assert.equal(excluded.window.pnAnalyticsPolicy.persisted,true);
assert.deepEqual(excluded.changes,['/?utm_campaign=excluded#test']);
for(const path of ['/','/over/','/nieuwsbrief/','/zoeken/','/mens/','/']) {
 const t=page('https://positief-nieuws.nl'+path,storage);
 assert.equal(t.scripts.length,0);assert.equal(t.window.sa_event.q,undefined);
 for(const event of ['newsletter_view','newsletter_cta_click','newsletter_form_submit','newsletter_landing_view','article_share_click','contact_click']) t.window.sa_event(event);
 assert.equal(t.window.sa_event.q,undefined);
}
assert.equal(page('https://positief-nieuws.nl/?pn_internal=0',storage).scripts.length,1);
assert.equal(page('https://positief-nieuws.nl/',storage).scripts.length,1);
const denied=page('https://positief-nieuws.nl/?pn_internal=1',new Map(),true);
assert.equal(denied.scripts.length,0);assert.equal(denied.window.pnAnalyticsPolicy.persisted,false);
assert.equal(page('https://positief-nieuws.nl/',new Map(),true).scripts.length,1);
console.log('PASS: regular/deduplicated pageview loader, auto events, 7 preview origins, persistent 5-page exclusion/reload, every custom event dropped, reset and blocked storage.');
