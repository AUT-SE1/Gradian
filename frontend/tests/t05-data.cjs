// From frontend: T05_CHROMIUM_EXECUTABLE=/path/to/chromium node tests/t05-data.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5197';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t05-verification');
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
   else if(u.pathname.endsWith('/student/dashboard'))data=require('./fixtures/student-dashboard.json');
   else if(u.pathname.endsWith('/auth/config')){status=503;}
   await r.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await p.route(base+'/test-avatar.svg',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="blue"/></svg>'}));
  await p.goto(base+'/tests/fixtures/t05-data.html');await p.waitForFunction(()=>window.t05);await p.evaluate(role=>{history.pushState(null,'','/'+role);dispatchEvent(new PopStateEvent('popstate'));},role);
  return {p,ctx,config,requests};
 }
 try{
  await new Promise(r=>setTimeout(r,800));
  for(const role of Object.keys(roleMap)){
   const v=await fresh(role,{lang:'fa'});await v.p.getByText('Fresh API name',{exact:true}).waitFor();
   assert.ok(v.requests.filter(r=>/panel|notifications/.test(r.path)).every(r=>r.auth==='Bearer test-A'));
   assert.equal(v.requests.filter(r=>r.path.endsWith('/panel')).length,1);
   assert.equal(v.requests.filter(r=>r.path.endsWith('/student/dashboard')).length,role==='student'?1:0);
   if(role==='student'){assert.equal(await v.p.locator('a.student-service-card').count(),8);assert.equal(await v.p.locator('article.student-service-card[aria-disabled]').count(),1);assert.match(await v.p.locator('.student-user-summary small').innerText(),/ریاضی/);}
   else{assert.ok(await v.p.locator('.management-nav-disabled').count());assert.match(await v.p.locator('.sidebar-countdown-widget').innerText(),/۴۲/);assert.equal(await v.p.locator('.management-empty-canvas').count(),1);}
   if(role==='counsellor')assert.equal(await v.p.locator('.management-user-summary small').innerText(),'رتبه برتر');
   await v.p.screenshot({path:path.join(output,role+'-1280.png'),fullPage:true});
   await v.p.locator('.portal-bell').click();await v.p.getByText('First notice',{exact:true}).waitFor();assert.equal(await v.p.locator('.portal-notification-list script').count(),0);
   await v.p.getByRole('button',{name:'صفحه بعد',exact:true}).click();await v.p.getByText('Second page',{exact:true}).waitFor();
   assert.ok(v.requests.some(r=>r.path.endsWith('/notifications')&&r.search.includes('offset=50')));assert.ok(v.requests.every(r=>r.method==='GET'));
   await v.p.keyboard.press('Escape');assert.equal(await v.p.locator('dialog[open]').count(),0);
   pass('real contract header/services/readonly paginated notifications: '+role);await v.ctx.close();
  }
  const loading=await fresh('student',{delay:700});await loading.p.getByText('Loading…').first().waitFor();assert.equal(await loading.p.locator('a.student-service-card').count(),0);await loading.p.getByText('Fresh API name',{exact:true}).waitFor();pass('loading has no fallback service links');await loading.ctx.close();
  const empty=await fresh('student',{empty:true});await empty.p.locator('.student-page-content').getByText('No items.').first().waitFor();assert.equal(await empty.p.locator('.student-service-card').count(),0);await empty.p.locator('.portal-bell').click();await empty.p.locator('dialog').getByText('No items.').waitFor();assert.equal(await empty.p.locator('.portal-unread-dot').count(),0);pass('empty services and notifications distinguished from error');await empty.ctx.close();
  for(const status of [500,403]){
   const v=await fresh('instructor',{status,notificationStatus:status});await v.p.getByText(status===403?'Access to this data is denied.':'Could not load data.',{exact:false}).first().waitFor({timeout:10000});assert.equal(await v.p.locator('.management-nav a').count(),0);v.config.status=200;v.config.notificationStatus=200;await v.p.getByRole('button',{name:'Retry',exact:true}).first().click();await v.p.locator('.management-header').getByRole('button',{name:'Retry',exact:true}).click();await v.p.getByText('Fresh API name',{exact:true}).waitFor();pass('explicit '+status+' error and retry recovery');await v.ctx.close();
  }
  const malformed=await fresh('admin',{malformed:true});await malformed.p.getByText('Could not load data.',{exact:false}).first().waitFor();assert.equal(await malformed.p.locator('.management-portal-shell').count(),1);pass('malformed response becomes visible error without crashing shell');await malformed.ctx.close();
  const pag=await fresh('student',{servicePagination:true});await pag.p.locator('a.student-service-card').first().waitFor();assert.equal(await pag.p.locator('.student-service-card').count(),9);assert.ok(pag.requests.some(r=>r.path.endsWith('/services')&&r.search.includes('offset=1')));pass('service pages aggregated without following remote next URLs');await pag.ctx.close();
  const direct=await fresh('instructor');await direct.p.getByText('Fresh API name',{exact:true}).waitFor();await direct.p.evaluate(()=>{history.pushState(null,'','/instructor/questions');dispatchEvent(new PopStateEvent('popstate'));});await direct.p.locator('.management-service-card').waitFor();assert.equal(await direct.p.locator('.management-service-open').count(),1);assert.equal(await direct.p.locator('.management-service-open').getAttribute('href'),'https://service.example/app');await direct.p.evaluate(()=>{history.pushState(null,'','/instructor/progress');dispatchEvent(new PopStateEvent('popstate'));});await direct.p.locator('.management-service-card').getByText('Currently unavailable',{exact:true}).waitFor();assert.equal(await direct.p.locator('.management-service-open').count(),0);pass('direct route uses exact registry key and disables unavailable service');await direct.ctx.close();
  for(const state of ['today','past']){const v=await fresh('counsellor',{countdownState:state,consultantType:'consultant'});await v.p.getByText('Fresh API name',{exact:true}).waitFor();assert.equal(await v.p.locator('.management-user-summary small').innerText(),'Consultant');assert.match(await v.p.locator('.sidebar-countdown-widget').innerText(),state==='today'?/exam is today/:/exam has taken place/);pass('countdown '+state+' and consultant subtype');await v.ctx.close();}
  for(const role of ['student','instructor']){const v=await fresh(role,{lang:'en',theme:'dark'});await v.p.getByText('Fresh API name',{exact:true}).waitFor();await v.p.setViewportSize({width:390,height:844});assert.equal(await v.p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);if(role==='instructor'){await v.p.locator('.mobile-menu-button').click();await v.p.keyboard.press('Escape');}await v.p.screenshot({path:path.join(output,role+'-mobile-dark-en.png'),fullPage:true});pass('mobile dark LTR no overflow: '+role);await v.ctx.close();}
  const notificationError=await fresh('admin',{notificationStatus:503});await notificationError.p.locator('.portal-bell').click();await notificationError.p.locator('dialog').getByText('Could not load data.',{exact:false}).waitFor();notificationError.config.notificationStatus=200;await notificationError.p.locator('dialog').getByRole('button',{name:'Retry',exact:true}).click();await notificationError.p.getByText('First notice',{exact:true}).waitFor();pass('notification error and retry inside dialog');await notificationError.ctx.close();
  const avatar=await fresh('student',{avatar:'/test-avatar.svg'});await avatar.p.route(base+'/test-avatar.svg',r=>r.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect width="32" height="32" fill="blue"/></svg>'}));await avatar.p.getByText('Fresh API name',{exact:true}).waitFor();await avatar.p.waitForFunction(()=>document.querySelector('.portal-user-avatar')?.naturalWidth>0);avatar.config.avatar='/missing-avatar.png';await avatar.p.evaluate(()=>window.t05.client.invalidateQueries({queryKey:['portal','A','student','panel']}));await avatar.p.waitForFunction(()=>!document.querySelector('.portal-user-avatar'));pass('real avatar loads and broken avatar hides without losing identity');await avatar.ctx.close();
  const cache=await fresh();await cache.p.getByText('Fresh API name',{exact:true}).waitFor();const cacheKeys=await cache.p.evaluate(()=>window.t05.client.getQueryCache().getAll().map(q=>q.queryKey));assert.ok(cacheKeys.filter(k=>k[0]==='portal').every(k=>k[1]==='A'&&k[2]==='student'));await cache.p.evaluate(()=>window.t05.auth.setSession(null));await cache.p.waitForFunction(()=>window.t05.auth.session===null);assert.equal(await cache.p.evaluate(()=>window.t05.client.getQueryCache().getAll().filter(q=>q.queryKey[0]==='portal').length),0);pass('identity-scoped keys and logout removes panel cache');await cache.ctx.close();
  const unauthorized=await fresh('admin',{status:401});await unauthorized.p.waitForFunction(()=>window.t05.auth.session===null);assert.equal(await unauthorized.p.locator('.management-portal-shell').count(),0);pass('authenticated 401 clears session and removes protected panel');await unauthorized.ctx.close();
  assert.deepEqual(errors,[]);pass('no browser JavaScript errors');
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({status:'passed',scenarios:results,errors},null,2));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
