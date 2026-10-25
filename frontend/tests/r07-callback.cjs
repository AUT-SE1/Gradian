// R07 callback contract test. Uses the real authFlow/authCallback sources and Node + TypeScript.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const frontend = path.resolve(__dirname, '..');
const authFlowSource = path.join(frontend, 'src/features/auth/api/authFlow.ts');
const callbackSource = path.join(frontend, 'src/features/auth/api/authCallback.ts');
const authApiSource = path.join(frontend, 'src/features/auth/api/authApi.ts');
const callbackPageSource = path.join(frontend, 'src/features/auth/pages/AuthCallbackPage.tsx');
const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gradian-r07-'));
const emptyTypeRoots = fs.mkdtempSync(path.join(os.tmpdir(), 'gradian-r07-types-'));

execFileSync('tsc', [
  authFlowSource,
  callbackSource,
  '--target', 'ES2022',
  '--module', 'commonjs',
  '--lib', 'ES2022,DOM',
  '--strict',
  '--skipLibCheck',
  '--typeRoots', emptyTypeRoots,
  '--outDir', outDir,
], { stdio: 'inherit' });

const callback = require(path.join(outDir, 'authCallback.js'));
const flow = require(path.join(outDir, 'authFlow.js'));
const {
  AuthCallbackFailure,
  callbackFailureFromStatus,
  clearCallbackAttempt,
  readCallbackAttempt,
} = callback;
const { OIDC_FLOW_KEY, OIDC_STATE_KEY, PKCE_VERIFIER_KEY } = flow;

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    values,
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); },
  };
}

function expectFailure(fn, kind, retryFlow) {
  assert.throws(fn, (error) => {
    assert.ok(error instanceof AuthCallbackFailure);
    assert.equal(error.kind, kind);
    assert.equal(error.retryFlow, retryFlow);
    return true;
  });
}

try {
  {
    const storage = memoryStorage({
      [OIDC_FLOW_KEY]: 'registration',
      [OIDC_STATE_KEY]: 'state-1',
      [PKCE_VERIFIER_KEY]: 'verifier-1',
    });
    const attempt = readCallbackAttempt('?code=code-1&state=state-1', storage);
    assert.deepEqual(attempt, { flow: 'registration', code: 'code-1', verifier: 'verifier-1' });
  }

  {
    const storage = memoryStorage({
      [OIDC_FLOW_KEY]: 'registration',
      [OIDC_STATE_KEY]: 'expected',
      [PKCE_VERIFIER_KEY]: 'verifier',
    });
    expectFailure(
      () => readCallbackAttempt('?code=code&state=wrong', storage),
      'invalid',
      'registration',
    );
    clearCallbackAttempt(storage);
    assert.equal(storage.values.size, 0, 'terminal callback cleanup must clear state/verifier/flow');
  }

  {
    const storage = memoryStorage({
      [OIDC_FLOW_KEY]: 'registration',
      [OIDC_STATE_KEY]: 'state',
      [PKCE_VERIFIER_KEY]: 'verifier',
    });
    expectFailure(
      () => readCallbackAttempt('?error=access_denied&state=state', storage),
      'cancelled',
      'registration',
    );
  }

  {
    const storage = memoryStorage({
      [OIDC_STATE_KEY]: 'state',
      [PKCE_VERIFIER_KEY]: 'verifier',
    });
    expectFailure(() => readCallbackAttempt('?state=state', storage), 'invalid', 'login');
  }

  {
    const expected = new Map([
      [400, 'invalid'],
      [401, 'unauthorized'],
      [403, 'forbidden'],
      [409, 'conflict'],
      [502, 'provider'],
      [503, 'provider'],
      [500, 'failed'],
    ]);
    for (const [status, kind] of expected) {
      const failure = callbackFailureFromStatus(status, 'registration');
      assert.equal(failure.kind, kind);
      assert.equal(failure.retryFlow, 'registration');
    }
  }

  const apiText = fs.readFileSync(authApiSource, 'utf8');
  const pageText = fs.readFileSync(callbackPageSource, 'utf8');
  const tokenIndex = apiText.indexOf('tokenResponse = await fetch');
  const meIndex = apiText.indexOf("httpClient.get<Me>('/me'");
  const validateIndex = apiText.indexOf('isUsableSession(session)');
  assert.ok(tokenIndex >= 0 && meIndex > tokenIndex && validateIndex > meIndex,
    'session must be built only after token exchange and /me');
  assert.match(apiText, /finally\s*\{[\s\S]*clearCallbackAttempt\(sessionStorage\)/,
    'every terminal callback must clear one-shot PKCE state');
  assert.match(pageText, /setSession\(null\);[\s\S]*authApi\.finishLogin\(\)/,
    'callback page must clear previous session/cache before verifying the new identity');
  assert.match(pageText, /authApi\.retryCallback\(retryFlow\)/,
    'retry must start a fresh flow of the same kind rather than reuse the consumed callback');

  console.log('R07 callback tests: 6 scenario groups passed.');
} finally {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.rmSync(emptyTypeRoots, { recursive: true, force: true });
}
