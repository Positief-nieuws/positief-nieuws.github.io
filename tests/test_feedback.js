/* Trust boundary and analytics checks, no network or real submissions. */
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('feedback.js','utf8');
function run(allowed = true, enabled = true) {
  const nodes=[], events=[], listeners={};
  class Element {
    constructor(tag) {this.tag=tag;this.dataset={};this.handlers={};this.children=[];this.isConnected=true;this.classList={add(){},remove(){}};if(tag==='iframe')this.contentWindow={};nodes.push(this);}
    setAttribute() {} append(...items){this.children.push(...items);} appendChild(el){this.append(el);}
    replaceChildren(...items){this.children=items;} after(el){this.append(el);}
    set innerHTML(s){this.html=s;this.span=new Element('span'); if(this.tag==='dialog'){this.closeButton=new Element('button');this.holder=new Element('div');}}
    querySelector(s){return s==='button'?this.closeButton:s==='.pn-feedback-frame'?this.holder:this.span;}
    addEventListener(k,f){this.handlers[k]=f;} focus(){this.focused=true;}
    showModal(){this.open=true;} close(){this.open=false;this.handlers.close();}
  }
  const main=new Element('main'); main.querySelector=()=>null;
  const document={readyState:'complete',createElement:t=>new Element(t),head:new Element('head'),body:new Element('body'),documentElement:new Element('html'),querySelector:s=>s==='main'?main:{}};
  const window={pnAnalyticsPolicy:{allowed},sa_event:(name,meta)=>events.push({name,meta}),addEventListener:(k,f)=>listeners[k]=f};
  vm.runInNewContext(source.replace(/const formId = '[^']*';/, enabled ? "const formId = 'TESTFORM';" : "const formId = '';"),{window,document,location:{pathname:'/artikelen/test/',search:'?email=private@example.com',hash:'#private'},URL,URLSearchParams});
  return {nodes,events,listeners,window};
}
assert.equal(run(true,false).window.pnFeedback,undefined,'disabled until configured');
for(const allowed of [true,false]) {
  const t=run(allowed), button=t.nodes.find(n=>n.dataset.feedbackPlacement==='floating');
  button.handlers.click();button.handlers.click();
  const frame=t.nodes.find(n=>n.tag==='iframe'), dialog=t.nodes.find(n=>n.tag==='dialog');
  assert.equal(t.nodes.filter(n=>n.tag==='iframe').length,1,'one frame per opening');
  const url=new URL(frame.src); assert.equal(url.searchParams.get('originPage'),'/artikelen/test/');
  assert.ok(!frame.src.includes('private'));
  const payload={event:'Tally.FormSubmitted',payload:{id:'test-only',formId:'TESTFORM',fields:[{answer:'secret text'}]}};
  const message=(origin,src,data)=>t.listeners.message({origin,source:src,data});
  message('https://evil.example',frame.contentWindow,JSON.stringify(payload));
  message('https://tally.so',{},JSON.stringify(payload));
  message('https://tally.so',frame.contentWindow,'bad json');
  message('https://tally.so',frame.contentWindow,JSON.stringify({...payload,payload:{id:'x',formId:'OTHER'}}));
  assert.equal(t.events.filter(e=>e.name==='feedback_submit').length,0);
  message('https://tally.so',frame.contentWindow,JSON.stringify(payload));
  message('https://tally.so',frame.contentWindow,JSON.stringify(payload));
  assert.deepEqual(t.events.map(e=>e.name),allowed?['feedback_open','feedback_submit']:[]);
  assert.ok(!JSON.stringify(t.events).includes('secret'));
  dialog.close();assert.equal(button.focused,true);
  message('https://tally.so',frame.contentWindow,JSON.stringify(payload));
  assert.equal(t.events.length,allowed?2:0);
}
console.log('PASS: disabled configuration, deduplicated opens/submits, origin/source/form checks, no PII, exclusions, focus restoration.');
