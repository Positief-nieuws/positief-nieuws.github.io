/* Run with node tests/test_newsletter_analytics.js. No network or dependencies. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('edition-analytics.js', 'utf8');
function scenario(pageType, category, topic, pathname) {
  const events = [], listeners = {}, fields = new Map();
  const form = {
    dataset: {newsletterPlacement: pageType === 'topic' ? 'topic_inline' : 'article_end'},
    valid: true, checkValidity() {return this.valid;},
    querySelector(selector) {return fields.get(selector.match(/name="([^"]+)"/)[1]);},
    appendChild(field) {fields.set(field.name, field);}
  };
  const window = {sa_metadata: {page_type:pageType,category,topic},sa_event:(name,metadata)=>events.push({name,metadata})};
  const document = {currentScript:{dataset:{pageType}},readyState:'complete',referrer:'',
    querySelectorAll:()=>pageType === 'newsletter' ? [] : [form],
    addEventListener:(name,callback)=>{listeners[name]=callback;},createElement:()=>({})};
  let observer;
  const context = {window,document,location:{search:'',pathname,origin:'https://positief-nieuws.nl'},
    URL,URLSearchParams,sessionStorage:{getItem:()=>null,setItem:()=>{}},performance:{now:()=>0},setInterval:()=>{},
    IntersectionObserver:class {constructor(callback){observer=callback;}observe(){}unobserve(){}}};
  window.IntersectionObserver=context.IntersectionObserver;
  vm.runInNewContext(source,context);
  return {events,listeners,fields,form,view:()=>observer([{isIntersecting:true,target:form}])};
}
const topics = {'mens':'Mens','natuur-en-klimaat':'Natuur & klimaat','gezondheid':'Gezondheid',
  'energie-en-innovatie':'Energie & innovatie','wetenschap':'Wetenschap','cultuur':'Cultuur','economie':'Economie','sport':'Sport'};
for (const [slug,label] of Object.entries(topics)) {
  const t = scenario('topic',undefined,slug,`/${slug}/`);
  t.view();t.view();
  assert.equal(t.events.filter(e=>e.name==='newsletter_view').length,1);
  assert.equal(t.events[0].metadata.content_category,label);
  assert.equal(t.events[0].metadata.placement,'topic_inline');
  assert.equal(t.fields.get('metadata__signup_category').value,label);
  t.form.valid=false;t.listeners.submit({target:t.form});
  assert.equal(t.events.filter(e=>e.name==='newsletter_form_submit').length,0);
  t.form.valid=true;t.listeners.submit({target:t.form});
  const submission=t.events.find(e=>e.name==='newsletter_form_submit');
  assert.equal(submission.metadata.signup_status,'submitted_unconfirmed');
  assert.equal(submission.metadata.content_category,label);
}
const article=scenario('article','Gezondheid',undefined,'/artikelen/voorbeeld/');article.view();
const cta={dataset:{newsletterCta:'article_intro'},closest:()=>null};
article.listeners.click({target:{closest:()=>cta}});
assert.equal(article.events.at(-1).name,'newsletter_cta_click');
assert.equal(article.events.at(-1).metadata.placement,'article_intro');
assert.equal(article.events.at(-1).metadata.content_category,'Gezondheid');
assert.equal(article.events[0].metadata.placement,'article_end');
const landing=scenario('newsletter',undefined,undefined,'/nieuwsbrief/');
assert.equal(landing.events[0].name,'newsletter_landing_view');
const home=scenario('homepage',undefined,undefined,'/');
home.view();assert.equal(home.events.filter(e=>e.name==='newsletter_view').length,0);
console.log('PASS: all 8 topic categories, view deduplication, invalid/valid submits, article click placement, landing event, homepage readiness.');

const duplicate = scenario('article','Gezondheid',undefined,'/artikelen/voorbeeld/');
let prevented = 0;
const event = {target:duplicate.form, preventDefault(){prevented++;}};
duplicate.listeners.submit(event); duplicate.listeners.submit(event);
assert.equal(prevented, 1);
assert.equal(duplicate.events.filter(e=>e.name==='newsletter_form_submit').length, 1);
console.log('PASS: repeated submit produces one native navigation and one submit event.');
