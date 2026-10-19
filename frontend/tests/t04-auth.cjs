// Run from frontend: node tests/t04-auth.cjs
// Requires a locally installed Playwright and its Chromium browser.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const crypto = require('node:crypto');
const frontend = path.resolve(__dirname, '..');
const port = process.env.T04_TEST_PORT || '5198';
const base = `http://127.0.0.1:${port}`;
const key = 'gradian.auth.session';
const results = [];
const errors = [];
const session = (role = 'student', id = 'A', token = 'token-A', expiresAt = Date.now() + 3600000) => ({accessToken:token,expiresAt,user:{id,displayName:`Test ${id}`,primaryRole:role}});
const pass = (name) => {results.push(name);process.stdout.write(`PASS ${name}\n`);};
(async () => {
 const server = spawn(process.execPath, ['node_modules/vite/bin/vite.js','--host','127.0.0.1','--port',port,'--strictPort'], {cwd:frontend,stdio:'ignore'});
 const browser = await chromium.launch({headless:true,executablePath:process.env.T04_CHROMIUM_EXECUTABLE || undefined,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--disable-gpu']}).catch(error=>{server.kill();throw error;});
 const cases = ['student','instructor','counsellor','admin'];
 async function fresh(value, {context,callbackRole='student',meStatus=200,testStatus=200,beginLogin=false,expiresIn=3600}={}) {
  const ctx=context || await browser.newContext();const p=await ctx.newPage();const counts={config:0,token:0,me:0,test:0};
  p.on('pageerror',e=>errors.push(e.message));
  if (value !== undefined) await p.addInitScript(({value,key})=>{if(sessionStorage.getItem('initialized'))return;sessionStorage.setItem('initialized','1');localStorage.setItem(key,typeof value==='string'?value:JSON.stringify(value));localStorage.setItem('language','en');}, {value,key});
  await p.route('https://fonts.googleapis.com/**',r=>r.abort());await p.route('https://fonts.gstatic.com/**',r=>r.abort());
  await p.route(base+'/api/**',r=>{
   const url=new URL(r.request().url());let status=200,data={};
   if(url.pathname.endsWith('/auth/config')) {counts.config++;status=beginLogin?200:503;data={issuer:base+'/oidc',client_id:'test-client',end_session_url:base+'/end-session',landing_url:base+'/',realm:'test'};}
   else if(url.pathname.endsWith('/me')){counts.me++;status=meStatus;data={sub:'callback-user',full_name:'Callback User',mobile:'09000000000',panel:callbackRole,role:callbackRole};}
   else if(url.pathname.endsWith('/test')){counts.test++;status=testStatus;}
   return r.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  });
  await p.route(base+'/oidc/protocol/openid-connect/token',r=>{counts.token++;return r.fulfill({contentType:'application/json',body:JSON.stringify({access_token:'callback-token',expires_in:expiresIn,token_type:'Bearer'})});});
  await p.route(base+'/oidc/protocol/openid-connect/auth*',r=>r.fulfill({contentType:'text/html',body:'Sign-in fixture'}));
  await p.route(base+'/end-session*',r=>r.fulfill({contentType:'text/html',body:'End-session fixture'}));
  return {p,ctx,counts};
 }
 async function harness(value,options={}) {const v=await fresh(value,options);await v.p.goto(base+'/tests/fixtures/t04-auth.html');await v.p.waitForFunction(()=>window.t04);return v;}
 async function waitUser(p,id) {await p.waitForFunction(id=>window.t04.auth.session?.user.id===id,id);}
 const close = async v=>v.ctx.close();
 try {
  await new Promise(r=>setTimeout(r,900));
  for(const role of cases) {
   const v=await fresh(undefined);await v.p.goto(base+'/'+role);await v.p.waitForURL(base+'/login');assert.equal(await v.p.locator('.student-portal-shell,.management-portal-shell').count(),0);pass('anonymous denied: '+role);await close(v);
  }
  for(const role of cases) {
   const v=await fresh(session(role));
   for(const requested of cases){await v.p.goto(base+'/'+requested);await v.p.waitForURL(base+'/'+role);await v.p.waitForSelector(role==='student'?'.student-portal-shell':'.management-portal-shell--'+role);}
   const sub=role==='student'?'exams':role==='instructor'?'questions':role==='counsellor'?'sessions':'products';
   await v.p.goto(base+'/'+role+'/'+sub);await v.p.waitForSelector('.management-service-card,.student-service-page-view');await v.p.reload();await v.p.waitForSelector('.management-service-card,.student-service-page-view');pass('role guard matrix and direct refresh: '+role);await close(v);
  }
  const bad=[null,[],{},'{bad json',session('root'),{...session(),user:null},{...session(),user:{id:'A',primaryRole:'student'}},{...session(),accessToken:''},{...session(),expiresAt:undefined},{...session(),expiresAt:'tomorrow'},session('admin','A','token-A',Date.now()-10)];
  for(let i=0;i<bad.length;i++){const v=await fresh(bad[i]);await v.p.goto(base+'/admin');await v.p.waitForURL(base+'/login');assert.equal(await v.p.evaluate(key=>localStorage.getItem(key),key),null);await close(v);}pass('11 malformed/expired stored sessions rejected and removed');
  for(const [old,role,sub] of [['professor','instructor','questions'],['consultant','counsellor','sessions']]) {
   const v=await fresh(session(role));const target=base+'/'+role+'/'+sub+'?page=2#details';await v.p.goto(base+'/'+old+'/'+sub+'?page=2#details');await v.p.waitForURL(target);await v.p.waitForSelector('.management-service-card');await v.p.reload();assert.equal(v.p.url(),target);pass('legacy alias keeps suffix, query, hash: '+old);await close(v);
  }
  const alias=await fresh(session('student'));await alias.p.goto(base+'/professor/questions');await alias.p.waitForURL(base+'/student');pass('legacy alias cannot bypass role guard');await close(alias);
  const exp=await fresh(session('admin','A','short-token',Date.now()+1800));await exp.p.goto(base+'/admin');await exp.p.waitForSelector('.management-portal-shell');await exp.p.waitForURL(base+'/login');assert.equal(await exp.p.evaluate(key=>localStorage.getItem(key),key),null);pass('live expiry removes panel and stored session without refresh');await close(exp);
  for(const event of ['focus','visibilitychange']){
   const v=await harness(session());await v.p.evaluate(event=>{Date.now=()=>9e15;if(event==='visibilitychange')document.dispatchEvent(new Event(event));else window.dispatchEvent(new Event(event));},event);await v.p.waitForFunction(()=>window.t04.auth.session===null);pass('expiry recheck on '+event);await close(v);
  }
  const cache=await harness(session());
  await cache.p.evaluate(()=>{window.t04.client.setQueryData(['private','A'],{secret:'A'});window.t04.client.getMutationCache().build(window.t04.client,{mutationKey:['A']});});
  await cache.p.evaluate(s=>window.t04.auth.setSession(s),session('admin','B','token-B'));await waitUser(cache.p,'B');
  assert.deepEqual(await cache.p.evaluate(()=>[window.t04.client.getQueryCache().getAll().length,window.t04.client.getMutationCache().getAll().length]),[0,0]);pass('account switch clears query and mutation caches');
  await cache.p.evaluate(()=>window.t04.client.setQueryData(['private','B'],{secret:'B'}));await cache.p.evaluate(s=>window.t04.auth.setSession(s),session('admin','B','rotated-token'));await waitUser(cache.p,'B');assert.equal(await cache.p.evaluate(()=>window.t04.client.getQueryData(['private','B']).secret),'B');pass('same account token rotation preserves its cache');
  await cache.p.evaluate(s=>window.t04.auth.setSession(s),session('student','B','new-role-token'));await cache.p.waitForFunction(()=>window.t04.auth.session?.user.primaryRole==='student');assert.equal(await cache.p.evaluate(()=>window.t04.client.getQueryCache().getAll().length),0);pass('role change clears private cache');
  await cache.p.evaluate(()=>{window.t04.client.fetchQuery({queryKey:['late-A'],queryFn:()=>new Promise(resolve=>{window.releaseLate=resolve;})}).catch(()=>{});});await cache.p.waitForFunction(()=>window.releaseLate);
  await cache.p.evaluate(s=>window.t04.auth.setSession(s),session('admin','C','token-C'));await waitUser(cache.p,'C');await cache.p.evaluate(()=>window.releaseLate('old-response'));await cache.p.waitForTimeout(40);assert.equal(await cache.p.evaluate(()=>window.t04.client.getQueryCache().getAll().length),0);pass('late query result cannot restore previous account cache');
  await cache.p.evaluate(()=>{window.t04.client.setQueryData(['private'],1);window.t04.auth.setSession(null);});await cache.p.waitForFunction(()=>!window.t04.auth.session);assert.equal(await cache.p.evaluate(()=>window.t04.client.getQueryCache().getAll().length),0);assert.equal(await cache.p.evaluate(key=>localStorage.getItem(key),key),null);pass('logout clears session and cache');await close(cache);
  const tabs=await harness(session());const second=await tabs.ctx.newPage();await second.goto(base+'/tests/fixtures/t04-auth.html');await second.waitForFunction(()=>window.t04);await waitUser(second,'A');
  await tabs.p.evaluate(s=>window.t04.auth.setSession(s),session('admin','B','token-B'));await waitUser(second,'B');await tabs.p.evaluate(()=>window.t04.auth.setSession(null));await second.waitForFunction(()=>!window.t04.auth.session);pass('real cross-tab storage events synchronize account switch and logout');await close(tabs);
  for(const code of [401,403]){
   const v=await harness(session(),{testStatus:code});await v.p.evaluate(()=>window.t04.client.setQueryData(['private'],1));
   const status=await v.p.evaluate(async()=>{try{await window.t04.httpClient.get('/test',{headers:{Authorization:'Bearer token-A'}});}catch(e){return e.status;}});assert.equal(status,code);
   if(code===401){await v.p.waitForFunction(()=>!window.t04.auth.session);assert.equal(await v.p.evaluate(()=>window.t04.client.getQueryCache().getAll().length),0);}else{assert.equal(await v.p.evaluate(()=>window.t04.auth.session.user.id),'A');assert.equal(await v.p.evaluate(()=>window.t04.client.getQueryData(['private'])),1);}
   pass(code+' authenticated request: typed error and correct session/cache behavior');await close(v);
  }
  const stale=await harness(session('admin','B','token-B'),{testStatus:401});await stale.p.evaluate(async()=>{try{await window.t04.httpClient.get('/test',{headers:{Authorization:'Bearer token-A'}});}catch{}});assert.equal(await stale.p.evaluate(()=>window.t04.auth.session.user.id),'B');await stale.p.evaluate(async()=>{try{await window.t04.httpClient.get('/test');}catch{}});assert.equal(await stale.p.evaluate(()=>window.t04.auth.session.user.id),'B');pass('stale-token and unauthenticated 401 cannot log out a new account');await close(stale);
  for(const code of [401,403,500]){
   const v=await harness(session(),{testStatus:code});await v.p.evaluate(async()=>{try{await window.t04.client.fetchQuery({queryKey:['retry'],retryDelay:0,queryFn:()=>window.t04.httpClient.get('/test')});}catch{}});assert.equal(v.counts.test,code===500?2:1);pass('query retry policy: '+code);await close(v);
  }
  for(const [backend,frontendRole] of [['student','student'],['professor','instructor'],['consultant','counsellor'],['admin','admin']]){
   const v=await fresh(undefined,{callbackRole:backend,beginLogin:true});await v.p.addInitScript(()=>{sessionStorage.setItem('gradian.auth.pkce_verifier','fixture-verifier');sessionStorage.setItem('gradian.auth.oidc_state','fixture-state');});await v.p.goto(base+'/auth/callback?code=fixture-code&state=fixture-state');await v.p.waitForURL(base+'/'+frontendRole);assert.equal(v.counts.token,1);assert.equal(await v.p.evaluate(key=>JSON.parse(localStorage.getItem(key)).user.primaryRole,key),frontendRole);pass('PKCE callback role mapping + concurrent callback dedupe: '+backend);await close(v);
  }
  for(const status of [401,403]){
   const v=await fresh(undefined,{meStatus:status,beginLogin:true});await v.p.addInitScript(()=>{sessionStorage.setItem('gradian.auth.pkce_verifier','fixture-verifier');sessionStorage.setItem('gradian.auth.oidc_state','fixture-state');localStorage.setItem('language','en');});await v.p.goto(base+'/auth/callback?code=fixture-code&state=fixture-state');await v.p.waitForSelector('[role="alert"]');assert.match(await v.p.locator('h1').innerText(),status===403?/Access denied/:/Sign-in is not valid/);assert.equal(await v.p.evaluate(key=>localStorage.getItem(key),key),null);pass('callback /me '+status+' has explicit error, no private panel/session');await close(v);
  }
  const unknown=await fresh(undefined,{callbackRole:'superuser',beginLogin:true});await unknown.p.addInitScript(()=>{sessionStorage.setItem('gradian.auth.pkce_verifier','v');sessionStorage.setItem('gradian.auth.oidc_state','s');});await unknown.p.goto(base+'/auth/callback?code=c&state=s');await unknown.p.waitForSelector('[role="alert"]');assert.equal(await unknown.p.evaluate(key=>localStorage.getItem(key),key),null);pass('unknown backend role rejected before storing a session');await close(unknown);
  const mismatch=await fresh(undefined,{beginLogin:true});await mismatch.p.addInitScript(()=>{sessionStorage.setItem('gradian.auth.pkce_verifier','v');sessionStorage.setItem('gradian.auth.oidc_state','expected');});await mismatch.p.goto(base+'/auth/callback?code=c&state=wrong');await mismatch.p.waitForSelector('[role="alert"]');assert.equal(mismatch.counts.token,0);pass('mismatched callback state never exchanges a code');await close(mismatch);
  const noExpiry=await fresh(undefined,{beginLogin:true,expiresIn:0});await noExpiry.p.addInitScript(()=>{sessionStorage.setItem('gradian.auth.pkce_verifier','v');sessionStorage.setItem('gradian.auth.oidc_state','s');});await noExpiry.p.goto(base+'/auth/callback?code=c&state=s');await noExpiry.p.waitForSelector('[role="alert"]');assert.equal(await noExpiry.p.evaluate(key=>localStorage.getItem(key),key),null);pass('callback cannot store an already-expired token response');await close(noExpiry);
  const pkce=await fresh(undefined,{beginLogin:true});await pkce.p.goto(base+'/login');await pkce.p.waitForURL(base+'/oidc/protocol/openid-connect/auth*');const authURL=new URL(pkce.p.url());assert.equal(authURL.searchParams.get('code_challenge_method'),'S256');const verifier=await pkce.p.evaluate(()=>sessionStorage.getItem('gradian.auth.pkce_verifier'));assert.equal(authURL.searchParams.get('code_challenge'),crypto.createHash('sha256').update(verifier).digest('base64url'));pass('existing PKCE S256 authorize flow preserved');await close(pkce);
  const again=await harness(session(),{beginLogin:true});const pairs=await again.p.evaluate(async()=>{const a=[];for(const code of ['first','second']){history.replaceState(null,'','/auth/callback?code='+code+'&state=fixture-state');sessionStorage.setItem('gradian.auth.pkce_verifier','fixture-v');sessionStorage.setItem('gradian.auth.oidc_state','fixture-state');a.push(await window.t04.authApi.finishLogin());}return a.map(s=>s.user.id);});assert.equal(pairs.length,2);assert.equal(again.counts.token,2);pass('a subsequent callback starts a fresh token exchange, no cached successful login');await close(again);
  assert.deepEqual(errors,[]);pass('no browser JavaScript errors');
  const out=process.env.T04_RESULTS_PATH;if(out){fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify({status:'passed',scenarios:results,errors},null,2));}
  console.log(`Completed ${results.length} scenario groups.`);
 }finally{await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
