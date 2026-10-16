const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source=fs.readFileSync('social-sharing.js','utf8');
function fixture(kind='article',clipboardFails=false,nativeResult='ok') {
 const events=[],handlers={},calls=[];
 const status={textContent:''}; const input={value:'',focus(){},select(){}};
 const fallback={hidden:true,querySelector:()=>input};
 const native={hidden:true,addEventListener:(e,f)=>{handlers.native=f;}};
 const copy={addEventListener:(e,f)=>{handlers.copy=f;}};
 const whatsapp={dataset:{shareChannel:'whatsapp'},href:'',addEventListener:(e,f)=>{handlers.whatsapp=f;}};
 const block={dataset:{shareType:kind},querySelector:(s)=>s==='[role="status"]'?status:s.includes('fallback')?fallback:s.includes('native')?native:copy,querySelectorAll:()=>[whatsapp]};
 const document={readyState:'complete',querySelectorAll:()=>[block],querySelector:(s)=>s.includes('canonical')?{href:'https://positief-nieuws.nl/voorbeeld/'}:{content:'Titel & nuance'}};
 const window={sa_metadata:{page_type:kind,category:'Mens'},sa_event:(name,meta)=>events.push({name,meta})};
 const navigator={clipboard:{writeText:async url=>{calls.push(url);if(clipboardFails)throw Error('denied');}},share:async d=>{calls.push(d);if(nativeResult!=='ok')throw {name:nativeResult};}};
 const context={window,document,navigator,location:{pathname:'/voorbeeld/'},URL,encodeURIComponent};
 vm.runInNewContext(source,context);
 return {events,handlers,calls,status,fallback,input,context,whatsapp};
}
(async()=>{
 for (const kind of ['article','special','newsletter','edition']) {
  const f=fixture(kind);await f.handlers.copy();
  const event=kind==='edition'?'share_edition':kind+'_share_click';
  assert.equal(f.events.filter(x=>x.name===event).length,1);
  assert.equal(f.events.filter(x=>x.name===kind+'_link_copy').length,1);
  assert.equal(f.events.at(-1).meta.share_status,'copied');
  assert.equal(f.events.at(-1).meta.page_path,'/voorbeeld/');
  assert.match(f.status.textContent,/Link gekopieerd/);
  assert.equal(f.calls[0],'https://positief-nieuws.nl/voorbeeld/');
  f.handlers.whatsapp();assert.match(f.whatsapp.href,/Titel%20%26%20nuance/);
  assert.equal(f.events.at(-1).meta.share_method,'whatsapp');
  vm.runInNewContext(source,f.context);assert.equal(f.events.length,3);
 }
 const failure=fixture('article',true);await failure.handlers.copy();
 assert.equal(failure.events.length,1);assert.equal(failure.fallback.hidden,false);
 assert.equal(failure.input.value,'https://positief-nieuws.nl/voorbeeld/');
 const cancel=fixture('article',false,'AbortError');await cancel.handlers.native();
 assert.equal(cancel.events.length,2);assert.equal(cancel.events[1].name,'share_menu_open');
 assert.equal(cancel.events[1].meta.share_status,'requested');assert.equal(cancel.status.textContent,'');
 assert.equal(cancel.calls.length,1); // No automatic WhatsApp navigation on cancel.
 const denied=fixture('article',false,'NotAllowedError');await denied.handlers.native();
 assert.match(denied.status.textContent,/Delen lukte niet/);
 console.log('PASS: clicks, successful copy, denied clipboard fallback, native request/cancel/error, clean URL, one handler and no delivery claims.');
})().catch(e=>{console.error(e);process.exit(1);});
