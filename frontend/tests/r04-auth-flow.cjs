// R04 auth-flow contract test. Uses the real authFlow.ts and only Node + TypeScript.
const assert = require('node:assert/strict');
const cryptoModule = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const frontend = path.resolve(__dirname, '..');
const source = path.join(frontend, 'src/features/auth/api/authFlow.ts');
const outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gradian-r04-'));
const emptyTypeRoots = fs.mkdtempSync(path.join(os.tmpdir(), 'gradian-r04-types-'));

if (!globalThis.crypto) globalThis.crypto = cryptoModule.webcrypto;
if (!globalThis.btoa) globalThis.btoa = (value) => Buffer.from(value, 'binary').toString('base64');

execFileSync('tsc', [
  source,
  '--target', 'ES2022',
  '--module', 'commonjs',
  '--lib', 'ES2022,DOM',
  '--strict',
  '--skipLibCheck',
  '--typeRoots', emptyTypeRoots,
  '--outDir', outDir,
], { stdio: 'inherit' });

const flow = require(path.join(outDir, 'authFlow.js'));
const {
  createAuthFlowStarter,
  OIDC_STATE_KEY,
  PKCE_VERIFIER_KEY,
} = flow;

const baseConfig = {
  issuer: 'http://127.0.0.1:8080/realms/gradian',
  realm: 'gradian',
  client_id: 'gradian-web',
  registration_endpoint: 'http://127.0.0.1:8080/realms/gradian/protocol/openid-connect/registrations',
  end_session_url: 'http://127.0.0.1:8080/realms/gradian/protocol/openid-connect/logout',
  landing_url: 'http://127.0.0.1:5173/',
};

function memoryStorage() {
  const values = new Map();
  return {
    values,
    setItem(key, value) { values.set(key, String(value)); },
  };
}

function makeStarter({ getConfig = async () => baseConfig, assign = () => {} } = {}) {
  const storage = memoryStorage();
  const redirects = [];
  const starter = createAuthFlowStarter({
    getConfig,
    callbackUrl: () => 'http://127.0.0.1:5173/auth/callback',
    assign: (url) => { redirects.push(url); assign(url); },
    storage,
  });
  return { starter, storage, redirects };
}

(async () => {
  {
    const { starter, storage, redirects } = makeStarter();
    assert.equal(await starter.beginRegistration(), true);
    assert.equal(redirects.length, 1);
    const url = new URL(redirects[0]);
    const verifier = storage.values.get(PKCE_VERIFIER_KEY);
    const state = storage.values.get(OIDC_STATE_KEY);
    assert.equal(url.pathname, '/realms/gradian/protocol/openid-connect/registrations');
    assert.equal(url.searchParams.get('client_id'), 'gradian-web');
    assert.equal(url.searchParams.get('response_type'), 'code');
    assert.equal(url.searchParams.get('scope'), 'openid');
    assert.equal(url.searchParams.get('redirect_uri'), 'http://127.0.0.1:5173/auth/callback');
    assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
    assert.equal(url.searchParams.get('state'), state);
    assert.equal(url.searchParams.has('code_verifier'), false);
    assert.equal(
      url.searchParams.get('code_challenge'),
      cryptoModule.createHash('sha256').update(verifier).digest('base64url'),
    );
  }

  {
    const a = makeStarter();
    const b = makeStarter();
    await a.starter.beginRegistration();
    await b.starter.beginRegistration();
    assert.notEqual(a.storage.values.get(OIDC_STATE_KEY), b.storage.values.get(OIDC_STATE_KEY));
    assert.notEqual(a.storage.values.get(PKCE_VERIFIER_KEY), b.storage.values.get(PKCE_VERIFIER_KEY));
  }

  {
    let releaseConfig;
    let configCalls = 0;
    const pendingConfig = new Promise((resolve) => { releaseConfig = resolve; });
    const { starter, redirects } = makeStarter({
      getConfig: async () => { configCalls += 1; return pendingConfig; },
    });
    const first = starter.beginRegistration();
    const second = starter.beginRegistration();
    assert.equal(await second, false);
    releaseConfig(baseConfig);
    assert.equal(await first, true);
    assert.equal(configCalls, 1);
    assert.equal(redirects.length, 1);
  }

  {
    let calls = 0;
    const { starter, storage, redirects } = makeStarter({
      getConfig: async () => {
        calls += 1;
        if (calls === 1) throw new Error('temporary config failure');
        return baseConfig;
      },
    });
    await assert.rejects(starter.beginRegistration(), /temporary config failure/);
    assert.equal(storage.values.size, 0);
    assert.equal(await starter.beginRegistration(), true);
    assert.equal(calls, 2);
    assert.equal(redirects.length, 1);
  }

  {
    const badConfig = {
      ...baseConfig,
      registration_endpoint: 'https://evil.example/realms/gradian/protocol/openid-connect/registrations',
    };
    const { starter, storage, redirects } = makeStarter({ getConfig: async () => badConfig });
    await assert.rejects(starter.beginRegistration(), /Invalid registration endpoint/);
    assert.equal(storage.values.size, 0);
    assert.equal(redirects.length, 0);
  }

  {
    const { starter, redirects } = makeStarter();
    assert.equal(await starter.beginLogin(), true);
    const url = new URL(redirects[0]);
    assert.equal(url.pathname, '/realms/gradian/protocol/openid-connect/auth');
    assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
    assert.equal(url.searchParams.has('code_verifier'), false);
  }

  {
    const { starter, storage, redirects } = makeStarter();
    assert.equal(await starter.beginRegistration(), true);
    const firstState = storage.values.get(OIDC_STATE_KEY);
    assert.equal(await starter.beginRegistration(), true, 'a restored page must be able to start a fresh attempt');
    assert.equal(redirects.length, 2);
    assert.notEqual(storage.values.get(OIDC_STATE_KEY), firstState);
  }

  console.log('R04 auth-flow tests: 7 scenario groups passed.');
})().finally(() => {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.rmSync(emptyTypeRoots, { recursive: true, force: true });
}).catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
