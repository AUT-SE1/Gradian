// From frontend: T05_CHROMIUM_EXECUTABLE=/path/to/chromium node tests/t05-data.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5197';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t09-verification');
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
  const v=await fresh('instructor',{lang:'fa'});
  // Enable every registered instructor service; unavailable is checked separately below.
  await v.p.route(base+'/api/v1/panel/services**',r=>r.fulfill({contentType:'application/json',body:JSON.stringify(envelope(keys.instructor.map(k=>service('instructor',k))))}));
  await v.p.evaluate(()=>window.t05.client.invalidateQueries({queryKey:['portal','A','instructor','services']}));
  await v.p.getByText('Fresh API name',{exact:true}).waitFor();
  await v.p.locator('.management-nav a').first().waitFor();
  assert.equal(await v.p.locator('.management-nav a').count(),5);
  assert.deepEqual(await v.p.locator('.management-nav a').allTextContents(),['داشبورد پیشرفت تحصیلی','مدیریت آزمون و سوال','ایجاد دوره آموزشی','کلاس خصوصی','هاب منابع و جزوات کنکور']);
  assert.equal(await v.p.locator('.management-empty-canvas').count(),1);
  assert.equal(await v.p.locator('.management-nav a.active').count(),0);
  assert.equal(await v.p.locator('.management-user-summary small').innerText(),'استاد');
  assert.equal(v.requests.some(r=>r.path.endsWith('/student/dashboard')),false);
  assert.equal(await v.p.locator('.sidebar-countdown-widget small').innerText(),'۴۲ روز تا کنکور');
  assert.equal(await v.p.locator('.profile-complete-nav').innerText(),'تکمیل پروفایل حرفه‌ای\n←');
  assert.ok(v.requests.every(r=>r.auth==='Bearer test-A'));
  const geometry=await v.p.evaluate(()=>{
   const rect=s=>{const r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};
   return {sidebar:rect('.management-sidebar'),header:rect('.management-header'),countdown:rect('.sidebar-countdown-widget'),overflow:document.documentElement.scrollWidth>innerWidth};
  });
  assert.equal(geometry.sidebar.width,288);assert.equal(geometry.header.height,64);assert.equal(geometry.overflow,false);assert.ok(geometry.countdown.y>840);
  await v.p.screenshot({path:path.join(output,'instructor-1280.png'),fullPage:true});
  pass('1280×927 reference geometry, menu order, empty home, API role and no student query');
  for(const suffix of ['progress','questions','courses','private-class','resources']){
   await v.p.locator('.management-nav a[href="/instructor/'+suffix+'"]').click();
   await v.p.locator('.management-service-open').waitFor();assert.equal(new URL(v.p.url()).pathname,'/instructor/'+suffix);
   assert.equal(await v.p.locator('.management-nav a.active').count(),1);
   assert.equal(await v.p.locator('.management-service-open').getAttribute('href'),'https://service.example/app');
   // Reload the real URL: Vite serves the production entry with the same mocked contracts.
   await v.p.reload();await v.p.locator('.management-service-open').waitFor();
   assert.equal(await v.p.locator('.management-nav a[aria-current="page"]').getAttribute('href'),'/instructor/'+suffix);
  }
  pass('all five services navigate, active state is unique, direct refresh works');
  await v.p.locator('.profile-complete-nav').click();await v.p.locator('.management-service-card').waitFor();assert.equal(new URL(v.p.url()).pathname,'/instructor/profile');
  await v.p.locator('.management-logo').click();await v.p.locator('.management-empty-canvas').waitFor();
  pass('profile route and logo return home');await v.ctx.close();
  const unavailable=await fresh('instructor',{lang:'fa'});await unavailable.p.getByText('Fresh API name',{exact:true}).waitFor();await unavailable.p.locator('.management-nav a').first().waitFor();await unavailable.p.locator('.management-nav-disabled').waitFor();assert.match(await unavailable.p.locator('.management-nav-disabled').innerText(),/فعلاً در دسترس نیست/);assert.equal(await unavailable.p.locator('.management-nav a[href="/instructor/progress"]').count(),0);
  await unavailable.p.evaluate(()=>{history.pushState(null,'','/instructor/progress');dispatchEvent(new PopStateEvent('popstate'))});await unavailable.p.locator('.management-service-card').getByRole('status').waitFor();assert.equal(await unavailable.p.locator('.management-service-open').count(),0);pass('unavailable service is disabled, direct route shows explicit status without outbound link');await unavailable.ctx.close();
  for(const lang of ['fa','en']){const v=await fresh('instructor',{lang,theme:'dark'});await v.p.getByText('Fresh API name',{exact:true}).waitFor();await v.p.setViewportSize({width:390,height:844});assert.equal(await v.p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await v.p.locator('.mobile-menu-button').click();assert.equal(await v.p.locator('.management-sidebar').getAttribute('aria-modal'),'true');await v.p.keyboard.press('Escape');assert.equal(await v.p.locator('.mobile-menu-button').getAttribute('aria-expanded'),'false');await v.p.locator('.mobile-menu-button').click();await v.p.locator('.management-nav a').first().click();await v.p.locator('.management-service-card').waitFor();assert.equal(await v.p.locator('.mobile-menu-button').getAttribute('aria-expanded'),'false');pass('mobile drawer, Escape, navigation, dark '+lang+' without overflow');await v.ctx.close();}
  assert.deepEqual(errors,[]);pass('no browser JavaScript errors');
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({status:'passed',geometry,scenarios:results,errors},null,2));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
