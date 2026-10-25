// R08 auth error/accessibility/display contract. Source-level: browser screenshots remain blocked by R02.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const frontend = path.resolve(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(frontend, p), 'utf8');
const login = read('src/features/auth/pages/LoginPage.tsx');
const register = read('src/features/auth/pages/RegisterPage.tsx');
const callback = read('src/features/auth/pages/AuthCallbackPage.tsx');
const css = read('src/shared/styles/globals.css');
const fa = JSON.parse(read('src/locales/fa/auth.json'));
const en = JSON.parse(read('src/locales/en/auth.json'));

for (const [name, source] of [['login', login], ['register', register], ['callback', callback]]) {
  assert.match(source, /role="status"/, `${name}: pending state must be announced`);
  assert.match(source, /aria-live="polite"/, `${name}: non-error status must use a polite live region`);
  assert.match(source, /aria-atomic="true"/, `${name}: status/error announcement must be atomic`);
  assert.match(source, /role=(?:\"alert\"|\{[^\n]*'alert'[^\n]*\})/, `${name}: failure state must be an alert`);
  assert.match(source, /tabIndex=\{-1\}/, `${name}: programmatic error focus target must be focusable`);
  assert.match(source, /\.current\?\.focus\(\)/, `${name}: error/return state must receive focus`);
  assert.match(source, /disabled=\{retrying\}/, `${name}: retry must expose busy/disabled behavior`);
}

assert.match(login, /t\('connectionError'\)/, 'login network error must be localized');
assert.match(login, /t\(retrying \? 'retrying' : 'retry'\)/, 'login retry label must be localized');
assert.doesNotMatch(login, /در حال انتقال|اتصال به سرویس|تلاش دوباره/, 'LoginPage must not hard-code Persian status copy');
assert.match(register, /aria-live=\{status === 'error' \? 'assertive' : 'polite'\}/,
  'registration errors must be assertive while return info stays polite');
assert.match(callback, /aria-busy=\{!error\}/, 'callback processing state must expose busy semantics');

for (const [lang, auth] of [['fa', fa], ['en', en]]) {
  assert.ok(auth.pending && auth.connectionError && auth.retrying && auth.retry,
    `${lang}: login pending/network/retry strings must be complete`);
  for (const key of ['invalid', 'unauthorized', 'forbidden', 'conflict', 'provider', 'failed', 'cancelled']) {
    assert.ok(auth.callback?.[key] && auth.callback?.[`${key}Title`], `${lang}: callback ${key} copy must be complete`);
  }
  assert.ok(auth.registration?.pending && auth.registration?.error && auth.registration?.returned
    && auth.registration?.continue && auth.registration?.retrying,
    `${lang}: registration transition strings must be complete`);
}

assert.match(css, /text-align:\s*start/, 'auth cards must follow RTL/LTR document direction');
assert.match(css, /:root\[data-theme='dark'\] \.auth-figma-card/, 'React dark theme must style auth cards');
assert.match(css, /@media \(max-width: 360px\)/, 'auth UI must have a narrow viewport guard');
assert.match(css, /\.auth-page[\s\S]*overflow-x:\s*hidden/, 'auth page must prevent horizontal overflow');
assert.match(css, /\.auth-figma-card[\s\S]*overflow-wrap:\s*anywhere/, 'long error text must wrap inside the card');
assert.match(css, /\.auth-figma-submit:focus-visible/, 'keyboard focus on retry/submit controls must be visible');

console.log('R08 React accessibility/display contract: 28 checks passed.');
