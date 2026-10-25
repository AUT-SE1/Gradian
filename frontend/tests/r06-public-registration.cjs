// R06 public registration entry contract. Visual CTA remains blocked by R02.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const frontend = path.resolve(__dirname, '..');
const router = fs.readFileSync(path.join(frontend, 'src/app/router/AppRouter.tsx'), 'utf8');
const page = fs.readFileSync(path.join(frontend, 'src/features/auth/pages/RegisterPage.tsx'), 'utf8');
const login = fs.readFileSync(path.join(frontend, 'src/features/auth/pages/LoginPage.tsx'), 'utf8');
const landing = fs.readFileSync(path.join(frontend, 'src/features/landing/pages/LandingPage.tsx'), 'utf8');
const flow = fs.readFileSync(path.join(frontend, 'src/features/auth/api/authFlow.ts'), 'utf8');
const fa = JSON.parse(fs.readFileSync(path.join(frontend, 'src/locales/fa/auth.json'), 'utf8'));
const en = JSON.parse(fs.readFileSync(path.join(frontend, 'src/locales/en/auth.json'), 'utf8'));

assert.match(router, /path="\/register"\s+element=\{<RegisterPage\s*\/>\}/,
  'PublicLayout must expose a direct /register route');
assert.match(router, /path="\/login"\s+element=\{<LoginPage\s*\/>\}/,
  'existing /login route must remain');
assert.match(page, /authApi\.beginRegistration\(\)/,
  'register route must use the R04 registration flow');
assert.match(page, /isUsableSession\(session\)/,
  'only a currently usable session may bypass registration');
assert.match(page, /Navigate to=\{`\/\$\{session\.user\.primaryRole\}`\}/,
  'authenticated users must return to their own role home');
assert.match(page, /hasPendingRegistrationAttempt\(\)/,
  'Back from Keycloak must be recognized as an unfinished attempt');
assert.match(page, /clearCallbackAttempt\(sessionStorage\)/,
  'manual retry must discard abandoned one-shot PKCE material');
assert.match(page, /\.catch\(\(\) =>/,
  'initial redirect rejection must be handled');
assert.match(page, /async function handleRetry\(\)/,
  'an explicit retry path must exist');
assert.match(page, /const started = await authApi\.beginRegistration\(\)/,
  'retry must await a fresh registration start');
assert.match(page, /role=\{status === 'error' \? 'alert' : 'status'\}/,
  'error/returned states must expose accessible semantics');
assert.match(page, /role="status"[\s\S]*aria-live="polite"/,
  'loading state must be accessible');
assert.ok(fa.registration?.pending && fa.registration?.error && fa.registration?.retrying
  && fa.registration?.returned && fa.registration?.continue,
  'Persian registration transition strings must exist');
assert.ok(en.registration?.pending && en.registration?.error && en.registration?.retrying
  && en.registration?.returned && en.registration?.continue,
  'English React locale must remain complete');
assert.doesNotMatch(landing, /to="\/register"/,
  'R02 is blocked: do not invent a landing CTA placement or text in R06');
assert.match(login, /authApi\.beginLogin\(\)/,
  'login flow must remain intact');
assert.match(flow, /dependencies\.assign\(authorization\.url\);[\s\S]*starting = false;/,
  'completed start lock must not trap a bfcache-restored page');

console.log('R06 public registration contract: 17 checks passed.');
