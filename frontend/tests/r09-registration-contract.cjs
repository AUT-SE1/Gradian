// R09 registration integration contract checks that do not require Playwright or a live stack.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const frontend = path.resolve(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(frontend, p), 'utf8');

const router = read('src/app/router/AppRouter.tsx');
const register = read('src/features/auth/pages/RegisterPage.tsx');
const authApi = read('src/features/auth/api/authApi.ts');
const authFlow = read('src/features/auth/api/authFlow.ts');

let checks = 0;
function ok(condition, message) {
  assert.ok(condition, message);
  checks += 1;
}

ok(router.includes('path="/register" element={<RegisterPage />}'), 'public /register route must exist');
ok(router.includes('path="/login" element={<LoginPage />}'), 'existing /login route must remain');
ok(router.includes('path="/auth/callback" element={<AuthCallbackPage />}'), 'shared callback route must remain');
ok(register.includes('authApi.beginRegistration()'), 'RegisterPage must start provider-owned registration');
ok(register.includes('isUsableSession(session)'), 'usable existing session must bypass registration');
ok(/Navigate to=\{`\/\$\{session\.user\.primaryRole\}`\}/.test(register), 'existing session destination must come from its role');

ok(authFlow.includes('new URL(config.registration_endpoint)'), 'registration endpoint must come from runtime config');
ok(authFlow.includes("endpoint.searchParams.set('response_type', 'code')"), 'authorization code flow must remain');
ok(authFlow.includes("endpoint.searchParams.set('scope', 'openid')"), 'openid scope must remain');
ok(authFlow.includes("endpoint.searchParams.set('code_challenge_method', 'S256')"), 'PKCE S256 must remain');
ok(authFlow.includes("endpoint.searchParams.set('state', state)"), 'state must remain in the authorization request');
ok(!authFlow.includes("searchParams.set('code_verifier'"), 'PKCE verifier must never be placed in the URL');
ok(!authFlow.includes('localhost'), 'registration/login flow must not hard-code localhost');

ok(authApi.includes("httpClient.get<Me>('/me'"), 'session must be built only after /me');
ok(authApi.includes('if (me.home_path && me.home_path !== `/${me.panel}`)'), 'inconsistent provider home path must be rejected');
ok(authApi.includes('if (!isUsableSession(session))'), 'candidate session must pass the shared session validator');
ok(authApi.includes("sessionStorage.removeItem(PKCE_VERIFIER_KEY)"), 'logout must clear PKCE verifier');
ok(authApi.includes("sessionStorage.removeItem(OIDC_STATE_KEY)"), 'logout must clear OIDC state');
ok(authApi.includes("sessionStorage.removeItem(OIDC_FLOW_KEY)"), 'logout must clear flow marker');

ok(!register.includes('password'), 'React /register page must not collect a password');
ok(!register.includes('consultant_type'), 'React /register page must not expose consultant type');
ok(!register.includes('name="role"') && !register.includes("name='role'"), 'React /register page must not expose a role selector');

console.log(`R09 frontend registration contract: ${checks} checks passed.`);
