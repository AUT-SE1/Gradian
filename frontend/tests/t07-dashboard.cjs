// From frontend: T05_CHROMIUM_EXECUTABLE=/path/to/chromium node tests/t05-data.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5197';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t07-verification');
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
  await p.addInitScript(({s,lang,theme})=>{localStorage.setItem('gradian.auth.session',JSON.stringify(s));localStorage.setItem('language',lang);localStorage.setItem('theme',theme);},{s:session(role),lang:options.lang||'en',theme:options.theme||'light'});
  await p.route('https://fonts.googleapis.com/**',r=>r.abort());await p.route('https://fonts.gstatic.com/**',r=>r.abort());
  await p.route(base+'/api/**',async r=>{
   const u=new URL(r.request().url());requests.push({path:u.pathname,search:u.search,auth:r.request().headers().authorization,method:r.request().method()});
   if(config.delay)await new Promise(resolve=>setTimeout(resolve,config.delay));
   let status=config.status,data={};
   if(u.pathname.endsWith('/panel'))data=config.malformed?{}:{panel:roleMap[role],home_path:'/'+roleMap[role],header:{full_name:'Fresh API name',avatar_url:config.avatar||'',consultant_type:role==='counsellor'?(config.consultantType||'top_ranker'):null,field_of_study:role==='student'?'mathematics':null,field_of_study_label:role==='student'?'ریاضی و فیزیک':null},countdown:{date:'2027-06-20',state:config.countdownState||'upcoming',days_remaining:config.countdownState?0:42,label:config.countdownState==='past'?'کنکور برگزار شده است':config.countdownState==='today'?'امروز روز کنکور است':'۴۲ روز تا کنکور'}};
   else if(u.pathname.endsWith('/panel/services')){let items=config.empty?[]:keys[role].map((k,i)=>service(role,k,i!==1));if(config.servicePagination){items=u.searchParams.get('offset')==='0'?items.slice(0,1):items.slice(1);data=envelope(items,u.searchParams.get('offset')==='0');}else data=envelope(items);}
   else if(u.pathname.endsWith('/notifications')){status=config.notificationStatus;const offset=Number(u.searchParams.get('offset'));const items=config.empty?[]:[{id:offset+1,title:offset?'Second page':'First notice',body:'<script>literal text</script>',created_at:'2026-10-19T10:00:00Z',is_read:false}];data={...envelope(items,!offset&&!config.empty),count:config.empty?0:51,previous:offset?'https://untrusted.example/previous':null,unread_count:config.empty?0:2};}
   else if(u.pathname.endsWith('/student/dashboard')){status=config.dashboardStatus??200;if(config.dashboardDelay)await new Promise(resolve=>setTimeout(resolve,config.dashboardDelay));data=structuredClone(config.dashboard??require('./fixtures/student-dashboard.json'));}
   else if(u.pathname.endsWith('/auth/config')){status=503;}
   await r.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await p.route(base+'/test-avatar.svg',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="blue"/></svg>'}));
  await p.goto(base+'/tests/fixtures/t05-data.html');await p.waitForFunction(()=>window.t05);await p.evaluate(role=>{history.pushState(null,'','/'+role);dispatchEvent(new PopStateEvent('popstate'));},role);
  return {p,ctx,config,requests};
 }
 try {
  await new Promise(r=>setTimeout(r,800));
  const fixture=require('./fixtures/student-dashboard.json');
  const wait=async v=>v.p.locator('.student-welcome-copy h1').getByText(fixture.welcome.message,{exact:true}).waitFor();
  const ok=await fresh('student',{lang:'fa'});await wait(ok);
  assert.equal(await ok.p.locator('.student-welcome-copy p').innerText(),fixture.welcome.tip);
  assert.match(await ok.p.locator('.student-user-summary small').innerText(),/ریاضی/);
  assert.match(await ok.p.locator('.student-welcome-widgets').innerText(),/۷ روز/);
  assert.match(await ok.p.locator('.student-welcome-widgets').innerText(),/۲۷ روز/);
  assert.equal(await ok.p.locator('.student-post-card h3').innerText(),fixture.experience_feed[0].title);
  assert.match(await ok.p.locator('.post-stats').innerText(),/۲۳/);
  assert.equal(await ok.p.locator('.student-post-card script,.post-stats button').count(),0);
  assert.equal(await ok.p.locator('.student-service-card').count(),9);
  assert.equal(await ok.p.locator('.student-community-tabs button:disabled').count(),3);
  assert.equal(ok.requests.filter(r=>r.path.endsWith('/student/dashboard')).length,1);
  assert.ok(ok.requests.filter(r=>r.path.endsWith('/student/dashboard')).every(r=>r.auth==='Bearer test-A'&&r.method==='GET'));
  await ok.p.screenshot({path:path.join(output,'student-1280-fa-light.png'),fullPage:true});
  pass('authenticated student data, identity, dashboard countdown, localized streak/feed counts, literal content, registry, readonly controls');
  const cached=await ok.p.evaluate(()=>window.t05.client.getQueryCache().getAll().find(q=>q.queryKey[3]==='student-dashboard')?.queryKey);
  assert.deepEqual(cached,['portal','A','student','student-dashboard']);
  await ok.p.evaluate(()=>window.t05.auth.setSession({accessToken:'test-B',expiresAt:Date.now()+3600000,user:{id:'B',displayName:'B',primaryRole:'student'}}));
  await ok.p.waitForFunction(()=>window.t05.client.getQueryCache().getAll().some(q=>q.queryKey[1]==='B'&&q.queryKey[3]==='student-dashboard'&&q.state.status==='success'));
  assert.equal(await ok.p.evaluate(()=>window.t05.client.getQueryCache().getAll().some(q=>q.queryKey[1]==='A')),false);
  await ok.p.evaluate(()=>window.t05.auth.setSession(null));await ok.p.waitForFunction(()=>window.t05.auth.session===null);
  assert.equal(await ok.p.evaluate(()=>window.t05.client.getQueryCache().getAll().some(q=>q.queryKey[0]==='portal')),false);
  pass('dashboard cache scoped to identity and cleared on account change/logout');await ok.ctx.close();
  const loading=await fresh('student',{dashboardDelay:1200});await loading.p.locator('.student-dashboard-page').getByText('Loading…',{exact:true}).first().waitFor();assert.equal(await loading.p.locator('.student-post-card').count(),0);await wait(loading);pass('loading without sample posts');await loading.ctx.close();
  for(const block of ['welcome','study_streak','experience_feed','countdown','all']) {
   const data=structuredClone(fixture);if(block==='all')Object.keys(data).forEach(k=>data[k]=null);else data[block]=null;
   const v=await fresh('student',{dashboard:data});await v.p.waitForFunction(()=>window.t05.client.getQueryCache().getAll().some(q=>q.queryKey[3]==='student-dashboard'&&q.state.status==='success'));
   assert.equal(await v.p.locator('.student-service-card').count(),9);
   if(block==='experience_feed'||block==='all')assert.equal(await v.p.locator('.student-post-card').count(),0);
   if(block==='study_streak'||block==='all')assert.match(await v.p.locator('.student-welcome-widgets').innerText(),/No data available/);
   pass('nullable block without crash: '+block);await v.ctx.close();
  }
  const zero=structuredClone(fixture);zero.study_streak.current_days=0;zero.experience_feed=[];
  const z=await fresh('student',{dashboard:zero});await wait(z);assert.match(await z.p.locator('.student-welcome-widgets').innerText(),/0 day/);await z.p.locator('.student-community-section').getByText('No items.',{exact:true}).waitFor();pass('zero streak and empty feed');await z.ctx.close();
  for(const status of [500,403]) {
   const v=await fresh('student',{dashboardStatus:status});await v.p.locator('.student-dashboard-page [role=alert]').waitFor();assert.equal(await v.p.locator('.student-post-card').count(),0);
   v.config.dashboardStatus=200;await v.p.locator('.student-dashboard-page').getByRole('button',{name:'Retry',exact:true}).click();await wait(v);pass('dashboard error '+status+' and retry');await v.ctx.close();
  }
  const bad=structuredClone(fixture);bad.study_streak.current_days='7';
  const malformed=await fresh('student',{dashboard:bad});await malformed.p.locator('.student-dashboard-page [role=alert]').waitFor();assert.equal(await malformed.p.locator('.student-post-card').count(),0);pass('malformed contract fails visibly without sample fallback');await malformed.ctx.close();
  for(const state of ['today','past']){const d=structuredClone(fixture);d.countdown={...d.countdown,state,days_remaining:0};const v=await fresh('student',{dashboard:d});await wait(v);assert.match(await v.p.locator('.student-welcome-widgets').innerText(),state==='today'?/exam is today/:/exam has taken place/);pass('dashboard countdown '+state);await v.ctx.close();}
  for(const role of ['instructor','counsellor','admin']){const v=await fresh(role);await v.p.getByText('Fresh API name',{exact:true}).waitFor();assert.equal(v.requests.filter(r=>r.path.endsWith('/student/dashboard')).length,0);assert.equal(await v.p.locator('.management-empty-canvas').count(),1);pass('no student request for '+role);await v.ctx.close();}
  for(const [lang,theme,width] of [['fa','light',390],['en','dark',1280],['en','dark',390]]){const v=await fresh('student',{lang,theme});await v.p.setViewportSize({width,height:width===1280?1978:844});await wait(v);assert.equal(await v.p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.equal(await v.p.locator('.management-sidebar').count(),0);await v.p.screenshot({path:path.join(output,`student-${width}-${lang}-${theme}.png`),fullPage:true});pass(`layout ${width} ${lang} ${theme}`);await v.ctx.close();}
  const unauthorized=await fresh('student',{dashboardStatus:401});await unauthorized.p.waitForFunction(()=>window.t05.auth.session===null);assert.equal(await unauthorized.p.locator('.student-dashboard-page').count(),0);pass('dashboard 401 clears session');await unauthorized.ctx.close();
  assert.deepEqual(errors,[]);pass('no browser runtime errors');
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({status:'passed',scenarios:results,errors},null,2));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
