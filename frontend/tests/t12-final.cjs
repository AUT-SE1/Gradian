// From frontend: NODE_PATH=<Playwright modules> T05_CHROMIUM_EXECUTABLE=<Chromium> node tests/t12-final.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const path=require('node:path');
const base='http://127.0.0.1:5196';
const results=[],errors=[];
const output=path.resolve(__dirname,'../../docs/t12-verification');
fs.mkdirSync(output,{recursive:true});
const session=(role='student',id='A')=>({accessToken:'test-'+id,expiresAt:Date.now()+3600000,user:{id,displayName:'Stale name',primaryRole:role}});
const roleMap={student:'student',instructor:'professor',counsellor:'consultant',admin:'admin'};
const keys={student:['simulated-exam','topic-exam','final-exam-12th','private-class','marketplace','counseling-planning','major-selection','top-ranker-experiences','courses','experience-exchange'],instructor:['profile','progress-dashboard','exam-question-management','create-course','private-class','resources-hub'],counsellor:['profile','student-reports','add-experiences','resolve-problems','counseling-sessions','resources-hub'],admin:['exam-bank','counseling-sessions','store-management']};
const service=(role,key,available=true)=>({key:roleMap[role]+'.'+key,title_fa:'خدمت آزمایشی',title_en:'Test service',description:'',button_label:'',icon:'book',order:1,status:available?'available':'unavailable',mode:'redirect',url:available?'https://service.example/app':null});
const envelope=(items,more=false)=>({count:items.length,next:more?'https://untrusted.example/next':null,previous:null,results:items});
const pass=name=>{results.push(name);console.log('PASS '+name);};
(async()=>{
 const server=spawn(process.execPath,['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5196','--strictPort'],{stdio:'ignore',cwd:path.resolve(__dirname,'..')});
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
  await p.goto(base+'/'+role);
  return {p,ctx,config,requests};
 }
 try {
  await new Promise(r=>setTimeout(r,800));
  const matrix=[];
  for (const role of Object.keys(roleMap)) for (const lang of ['fa','en']) for (const theme of ['light','dark']) {
   const v=await fresh(role,{lang,theme,allAvailable:true});
   await v.p.getByText('Fresh API name',{exact:true}).waitFor();
   await v.p.locator(role==='student'?'.student-service-card':'.management-nav a').first().waitFor();
   await v.p.evaluate(()=>document.fonts.ready);
   assert.equal(await v.p.locator('html').getAttribute('dir'),lang==='fa'?'rtl':'ltr');
   assert.equal(await v.p.locator('html').getAttribute('data-theme'),theme);
   assert.equal(v.requests.some(r=>r.path.endsWith('/student/dashboard')),role==='student');
   assert.ok(v.requests.every(r=>r.auth==='Bearer test-A'));
   for(const width of [1280,390,320]){
    await v.p.setViewportSize({width,height:width===1280?(role==='student'?1978:role==='admin'?978:role==='instructor'?927:800):844});
    await v.p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    const geometry=await v.p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,sidebar:document.querySelector('.management-sidebar')?.getBoundingClientRect().width,header:document.querySelector('.management-header')?.getBoundingClientRect().height}));
    assert.ok(geometry.scroll<=width,JSON.stringify({role,lang,theme,...geometry}));
    if(role==='student') {assert.equal(await v.p.locator('.management-sidebar').count(),0);if(width===1280)assert.equal(await v.p.locator('.student-service-card').count(),9);}
    else if(width===1280){assert.equal(geometry.sidebar,288);assert.equal(geometry.header,64);assert.equal(await v.p.locator('.management-empty-canvas').count(),1);}
    else {
     await v.p.locator('.mobile-menu-button').click();
     assert.equal(await v.p.locator('.management-sidebar').getAttribute('aria-modal'),'true');
     await v.p.keyboard.press('Escape');
     assert.equal(await v.p.locator('.mobile-menu-button').getAttribute('aria-expanded'),'false');
    }
    const file=`${role}-${lang}-${theme}-${width}.png`;
    if(width!==320)await v.p.screenshot({path:path.join(output,file),fullPage:true});
    matrix.push({role,lang,theme,width,geometry,screenshot:width===320?null:file});
   }
   pass(`${role} ${lang} ${theme}: desktop, 390 and 320; direction, theme, role data, overflow and drawer`);
   await v.p.setViewportSize({width:1280,height:978});
   const suffix={student:'exams',instructor:'questions',counsellor:'sessions',admin:'products'}[role];
   await v.p.goto(base+'/'+role+'/'+suffix);await v.p.locator('.management-service-open,.student-service-open').first().waitFor();
   await v.p.reload();await v.p.locator('.management-service-open,.student-service-open').first().waitFor();
   assert.equal(new URL(v.p.url()).pathname,'/'+role+'/'+suffix);
   await v.ctx.close();
  }
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({status:'passed',source:'real application entry; intercepted API contracts, not live backend',results,matrix,errors},null,2));
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1});
