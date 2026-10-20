// From frontend: T05_CHROMIUM_EXECUTABLE=/path/to/chromium node tests/t05-data.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5197';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t06-verification');
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
  const expected=['آزمون شبیه‌ساز کنکور','آزمون مبحثی','امتحان نهایی دوازدهم','کلاس خصوصی','خرید و فروش منابع و کتاب','مشاوره و برنامه‌ریزی','انتخاب رشته هوشمند','تجارب رتبه‌های برتر و رفع اشکال درسی','دوره‌های آموزشی و نکته و تست'];
  for(const [width,lang,theme] of [[1280,'fa','light'],[390,'fa','light'],[1280,'en','dark'],[390,'en','dark']]){
   const v=await fresh('student',{lang,theme});await v.p.setViewportSize({width,height:width===1280?1978:844});await v.p.locator('.student-service-card').first().waitFor();await v.p.evaluate(()=>document.fonts.ready);
   assert.equal(await v.p.locator('.student-service-card').count(),9);
   assert.equal(await v.p.locator('.management-sidebar').count(),0);
   assert.equal(await v.p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   assert.equal(await v.p.locator('.student-community-tabs button:disabled').count(),3);
   assert.equal(await v.p.locator('.post-stats button,.post-attachment a').count(),0);
   assert.equal(v.requests.filter(r=>r.path.endsWith('/student/dashboard')).length,1);
   if(width===1280&&lang==='fa'){
    assert.deepEqual(await v.p.locator('.student-service-card h3').allTextContents(),expected);
    const cards=await v.p.locator('.student-service-card').evaluateAll(es=>es.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};}));
    assert.equal(cards[0].y,cards[1].y);assert.equal(cards[1].y,cards[2].y);assert.ok(cards[0].x>cards[1].x&&cards[1].x>cards[2].x);
    assert.equal(await v.p.evaluate(()=>document.fonts.check('14px "Gradian Portal"')),true);
    fs.writeFileSync(path.join(output,'geometry.json'),JSON.stringify(cards,null,2));
   }
   await v.p.screenshot({path:path.join(output,`student-${width}-${lang}-${theme}.png`),fullPage:true});pass(`student ${width} ${lang} ${theme}: grid, no sidebar/overflow, disabled unsupported interactions`);await v.ctx.close();
  }
  for(const role of ['instructor','counsellor','admin']){
   const v=await fresh(role,{lang:'fa'});await v.p.getByText('Fresh API name',{exact:true}).waitFor();assert.equal(await v.p.locator('.management-empty-canvas').count(),1);assert.equal(await v.p.locator('.student-dashboard-page').count(),0);pass('management canvas preserved: '+role);await v.ctx.close();
  }
  assert.deepEqual(errors,[]);pass('no browser JavaScript errors');
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({status:'passed',scenarios:results,errors},null,2));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
