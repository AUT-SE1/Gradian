// From frontend: T05_CHROMIUM_EXECUTABLE=/path/to/chromium node tests/t05-data.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5197';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t11-verification');
fs.mkdirSync(output,{recursive:true});
const session=(role='student',id='A')=>({accessToken:'test-'+id,expiresAt:Date.now()+3600000,user:{id,displayName:'Stale name',primaryRole:role}});
const roleMap={student:'student',instructor:'professor',counsellor:'consultant',admin:'admin'};
const keys={student:['simulated-exam','topic-exam','final-exam-12th','private-class','marketplace','counseling-planning','major-selection','top-ranker-experiences','courses','experience-exchange'],instructor:['profile','progress-dashboard','exam-question-management','create-course','private-class','resources-hub'],counsellor:['profile','student-reports','add-experiences','resolve-problems','counseling-sessions','resources-hub'],admin:['exam-bank','counseling-sessions','store-management']};
const service=(role,key,available=true)=>({key:roleMap[role]+'.'+key,title_fa:'خدمت آزمایشی',title_en:'Test service',description:'',button_label:'',icon:'book',order:1,status:available?'available':'unavailable',mode:'redirect',url:available?'https://service.example/app':null});
const envelope=(items,more=false)=>({count:items.length,next:more?'https://untrusted.example/next':null,previous:null,results:items});
const pass=name=>{results.push(name);console.log('PASS '+name);};
(async()=>{
 const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5197','--strictPort'],{stdio:'ignore',cwd:path.resolve(__dirname,'..')});
 const browser=await chromium.launch({headless:true,executablePath:process.env.T05_CHROMIUM_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage']});
 async function fresh(role='student',options={}){
  const ctx=await browser.newContext({viewport:{width:1280,height:role==='instructor'?927:role==='admin'?978:role==='student'?1978:800}});const p=await ctx.newPage();const requests=[];
  const config={status:200,empty:false,delay:0,notificationStatus:200,...options};
  p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(({s,lang,theme})=>{if(window.top!==window)return;localStorage.setItem('gradian.auth.session',JSON.stringify(s));localStorage.setItem('language',lang);localStorage.setItem('theme',theme);},{s:session(role),lang:options.lang||'en',theme:options.theme||'light'});
  await p.route('https://fonts.googleapis.com/**',r=>r.abort());await p.route('https://fonts.gstatic.com/**',r=>r.abort());
  await p.route(base+'/api/**',async r=>{
   const u=new URL(r.request().url());requests.push({path:u.pathname,search:u.search,auth:r.request().headers().authorization,method:r.request().method()});
   if(config.delay)await new Promise(resolve=>setTimeout(resolve,config.delay));
   let status=config.status,data={};
   if(u.pathname.endsWith('/panel'))data=config.malformed?{}:{panel:roleMap[role],home_path:'/'+roleMap[role],header:{full_name:'Fresh API name',avatar_url:config.avatar||'',consultant_type:role==='counsellor'?(config.consultantType||'top_ranker'):null,field_of_study:role==='student'?'mathematics':null,field_of_study_label:role==='student'?'ریاضی و فیزیک':null},countdown:{date:'2027-06-20',state:config.countdownState||'upcoming',days_remaining:config.countdownState?0:42,label:config.countdownState==='past'?'کنکور برگزار شده است':config.countdownState==='today'?'امروز روز کنکور است':'۴۲ روز تا کنکور'}};
   else if(u.pathname.endsWith('/panel/services')){let items=config.empty?[]:keys[role].map((k,i)=>({...service(role,k,config.allAvailable || i!==1),mode:config.mode||'redirect',...(config.url?{url:config.url}:{})}));if(config.servicePagination){items=u.searchParams.get('offset')==='0'?items.slice(0,1):items.slice(1);data=envelope(items,u.searchParams.get('offset')==='0');}else data=envelope(items);}
   else if(u.pathname.endsWith('/notifications')){status=config.notificationStatus;const offset=Number(u.searchParams.get('offset'));const items=config.empty?[]:[{id:offset+1,title:offset?'Second page':'First notice',body:'<script>literal text</script>',created_at:'2026-10-19T10:00:00Z',is_read:false}];data={...envelope(items,!offset&&!config.empty),count:config.empty?0:51,previous:offset?'https://untrusted.example/previous':null,unread_count:config.empty?0:2};}
   else if(u.pathname.endsWith('/student/dashboard'))data=require('./fixtures/student-dashboard.json');
   else if(u.pathname.endsWith('/auth/config')){status=503;}
   await r.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await p.route(base+'/test-avatar.svg',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="blue"/></svg>'}));
  await p.goto(base+'/tests/fixtures/t05-data.html');await p.waitForFunction(()=>window.t05);await p.evaluate(role=>{history.pushState(null,'','/'+role);dispatchEvent(new PopStateEvent('popstate'));},role);
  return {p,ctx,config,requests};
 }
 try {
  await new Promise(r=>setTimeout(r,800));
  for (const role of Object.keys(roleMap)) {
   const v=await fresh(role,{allAvailable:true});
   await v.p.getByText('Fresh API name',{exact:true}).waitFor();
   const suffix={student:'exams',instructor:'questions',counsellor:'sessions',admin:'products'}[role];
   const go=async()=>v.p.evaluate(path=>{history.pushState(null,'',path);dispatchEvent(new PopStateEvent('popstate'));},'/'+role+'/'+suffix);
   await go();const open=v.p.locator(role==='student'?'.student-service-open':'.management-service-open');
   await open.waitFor();assert.equal(await open.getAttribute('href'),'https://service.example/app');
   assert.equal(await open.getAttribute('referrerpolicy'),'no-referrer');
   assert.equal(await v.p.locator('iframe').count(),0);await v.p.getByText('Connected',{exact:true}).waitFor();
   await v.p.route('https://service.example/**',r=>r.fulfill({contentType:'text/html',body:'<h1>Embedded test service</h1>'}));
   v.config.mode='embed';await v.p.evaluate(()=>window.t05.client.invalidateQueries({queryKey:['portal']}));
   const frame=v.p.locator('iframe');await frame.waitFor();
   assert.equal(await frame.getAttribute('src'),'https://service.example/app');
   assert.equal(await frame.getAttribute('sandbox'),'allow-scripts allow-forms allow-popups allow-same-origin');
   await v.p.frameLocator('iframe').getByText('Embedded test service').waitFor();
   assert.equal(await open.innerText(),'Open service separately ←');
   v.config.mode='redirect';await v.p.evaluate(()=>window.t05.client.invalidateQueries({queryKey:['portal']}));
   await frame.waitFor({state:'detached'});assert.equal(await open.getAttribute('href'),'https://service.example/app');
   assert.ok(v.requests.every(r=>r.auth==='Bearer test-A'));
   pass(role+': redirect URL, embedded content, separate-open fallback and mode refresh');await v.ctx.close();
  }
  const v=await fresh('student',{allAvailable:true,mode:'embed'});await v.p.locator('a.student-service-card').first().waitFor();
  assert.equal(await v.p.locator('a.student-service-card').first().getAttribute('href'),'/student/exams');
  assert.equal(await v.p.locator('a.student-community-cta').getAttribute('href'),'/student/community');
  await v.p.route('https://service.example/**',r=>r.fulfill({contentType:'text/html',body:'<h1>Embedded test service</h1>'}));
  await v.p.locator('a.student-service-card').first().click();await v.p.locator('iframe').waitFor();
  assert.equal(new URL(v.p.url()).pathname,'/student/exams');await v.p.reload();await v.p.locator('iframe').waitFor();
  pass('student card/community embed routes and direct refresh');await v.ctx.close();
  const r=await fresh('student',{allAvailable:true});await r.p.locator('a.student-service-card').first().waitFor();
  await r.p.route('https://service.example/**',route=>route.fulfill({contentType:'text/html',body:'<h1>Redirect destination</h1>'}));
  let remote; r.p.on('request',q=>{if(q.url().startsWith('https://service.example'))remote=q;});
  await r.p.locator('a.student-service-card').first().click();await r.p.getByText('Redirect destination').waitFor();
  assert.equal(r.p.url(),'https://service.example/app');assert.equal(remote.headers().authorization,undefined);assert.equal(remote.headers().referer,undefined);
  pass('redirect performs full-page navigation without bearer or referrer');await r.ctx.close();
  const u=await fresh('admin',{allAvailable:true});await u.p.getByText('Fresh API name',{exact:true}).waitFor();
  const result=await u.p.evaluate(async()=>{
   const {serviceHref}=await import('/src/features/portal/api/panelApi.ts');
   const base={status:'available',mode:'redirect'};
   const bad=['javascript:alert(1)','data:text/html,bad','ftp://service.example','/relative','//service.example','https://user:pass@service.example','https://service.example?access_token=secret','https://service.example#access_token=secret','https://service.example#/?id_token=secret'];
   return {bad:bad.map(url=>serviceHref({...base,url})===undefined),good:serviceHref({...base,url:'https://service.example/app?lesson=2#topic'}),disabled:serviceHref({...base,status:'unavailable',url:'https://service.example'})===undefined};
  });assert.ok(result.bad.every(Boolean));assert.ok(result.disabled);assert.equal(result.good,'https://service.example/app?lesson=2#topic');
  pass('absolute HTTP(S), credential-free URLs; ordinary query/hash preserved');
  const fixture=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../backend/core/registry/fixtures/services.json'),'utf8'));
  const mappings=await u.p.evaluate(async()=> (await import('/src/features/portal/api/serviceRoutes.ts')).serviceKeys);
  assert.equal(Object.keys(mappings).length,fixture.length);for(const key of Object.values(mappings))assert.ok(fixture.some(s=>s.pk===key));
  pass('all 25 paths map to exact registry fixture keys');await u.ctx.close();
  for(const status of [403,500]){
   const e=await fresh('admin',{status});await e.p.getByText(status===403?'Access to this data is denied.':'Could not load data.',{exact:false}).first().waitFor();
   assert.equal(await e.p.locator('.management-nav a').count(),0);assert.equal(await e.p.locator('.management-nav-disabled').filter({hasText:'Currently unavailable'}).count(),0);
   e.config.status=200;await e.p.getByRole('button',{name:'Retry',exact:true}).first().click();await e.p.locator('.management-nav a').first().waitFor();pass(status+': distinct item state and retry');await e.ctx.close();
  }
  const missing=await fresh('instructor',{empty:true});await missing.p.getByText('Fresh API name',{exact:true}).waitFor();
  await missing.p.evaluate(()=>{history.pushState(null,'','/instructor/questions');dispatchEvent(new PopStateEvent('popstate'));});
  await missing.p.locator('.management-service-card').getByText('Currently unavailable',{exact:true}).waitFor();assert.equal(await missing.p.locator('.management-service-open,iframe').count(),0);
  pass('missing entry/direct route has no active destination');await missing.ctx.close();
  const slow=await fresh('admin',{delay:700});await slow.p.locator('.management-nav-disabled').first().waitFor();
  assert.ok((await slow.p.locator('.management-nav-disabled').first().innerText()).includes('Loading…'));
  assert.equal(await slow.p.locator('.management-nav-disabled').filter({hasText:'Currently unavailable'}).count(),0);
  pass('loading items are distinguished from unavailable');await slow.ctx.close();
  const same=await fresh('admin',{allAvailable:true,mode:'embed',url:base+'/embedded-test'});
  await same.p.route(base+'/embedded-test',route=>route.fulfill({contentType:'text/html',body:'<h1>Local embedded service</h1>'}));
  await same.p.getByText('Fresh API name',{exact:true}).waitFor();await same.p.locator('.management-nav a').first().click();
  await same.p.frameLocator('iframe').getByText('Local embedded service').waitFor();
  assert.equal(await same.p.locator('iframe').getAttribute('sandbox'),'allow-scripts allow-forms allow-popups');
  same.config.status=403;await same.p.evaluate(()=>window.t05.client.invalidateQueries({queryKey:['portal']}));
  await same.p.locator('iframe').waitFor({state:'detached'});assert.equal(await same.p.locator('.management-service-open').count(),0);
  pass('same-origin embed isolation and cached destinations removed after 403');await same.ctx.close();
  assert.deepEqual(errors,[]);
 }finally{await browser.close();server.kill();fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({results,errors},null,2));}
})().catch(e=>{console.error(e);process.exitCode=1});
