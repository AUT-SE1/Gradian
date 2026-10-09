const API = '/api/v1';
const $ = (id) => document.getElementById(id);
const logEl = $('log');

function log(message, data) {
  const time = new Date().toLocaleTimeString();
  const text = data === undefined ? '' : '\n' + (typeof data === 'string' ? data : JSON.stringify(data, null, 2));
  logEl.textContent = `[${time}] ${message}${text}\n\n` + logEl.textContent;
}

async function api(path, { method = 'GET', body, token = true } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) {
    const user = await manager.getUser();
    if (user) headers.Authorization = `Bearer ${user.access_token}`;
  }
  const response = await fetch(API + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  let payload = null;
  try { payload = await response.json(); } catch { /* empty body */ }
  log(`${method} ${path} -> ${response.status}`, payload);
  return { status: response.status, payload };
}

function decode(jwt) {
  const part = jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
  return JSON.parse(decodeURIComponent(escape(atob(part))));
}

let manager;
let registerManager;
let currentUser = null;

async function setup() {
  const { status, payload: config } = await api('/auth/config', { token: false });
  $('config').textContent = JSON.stringify(config, null, 2);
  if (status !== 200) throw new Error('could not read /auth/config');
  const settings = {
    authority: config.issuer,
    client_id: config.client_id,
    redirect_uri: `${window.location.origin}/auth/callback`,
    post_logout_redirect_uri: config.landing_url,
    response_type: 'code',
    scope: 'openid',
    automaticSilentRenew: true,
    userStore: new oidc.WebStorageStateStore({ store: window.localStorage }),
  };
  if (window.location.search.includes('debug')) { oidc.Log.setLevel(oidc.Log.DEBUG); oidc.Log.setLogger(console); }
  manager = new oidc.UserManager(settings);
  const metadata = await manager.metadataService.getMetadata();
  registerManager = new oidc.UserManager({
    ...settings,
    metadata: { ...metadata, authorization_endpoint: config.registration_endpoint },
  });
  manager.events.addUserLoaded(() => { log('event: token loaded or renewed'); refreshSession(); });
  manager.events.addAccessTokenExpiring(() => log('event: access token is about to expire, renewing'));
  manager.events.addAccessTokenExpired(() => log('event: access token expired'));
  manager.events.addSilentRenewError((e) => log('event: silent renew FAILED', String(e)));
  manager.events.addUserUnloaded(() => { log('event: signed out'); refreshSession(); });
}

async function refreshSession() {
  const user = await manager.getUser();
  currentUser = user;
  $('s-signed').textContent = user ? 'yes' : 'no';
  if (!user) {
    for (const id of ['s-expires', 's-refresh', 's-aud', 's-roles']) $(id).textContent = '-';
    return;
  }
  const claims = decode(user.access_token);
  $('s-refresh').textContent = user.refresh_token ? 'yes' : 'NO';
  $('s-aud').textContent = [].concat(claims.aud).join(', ');
  $('s-roles').textContent = ((claims.realm_access || {}).roles || []).join(', ');
}

function showMe(me) {
  $('m-name').textContent = me.full_name;
  $('m-panel').textContent = me.panel + (me.consultant_type ? ` (${me.consultant_type})` : '');
  $('m-home').textContent = me.home_path;
  $('m-route').textContent = `${window.location.origin}${me.home_path}`;
}

async function loadMe() {
  const { status, payload } = await api('/me');
  if (status === 200) showMe(payload);
  return status;
}

async function main() {
  await setup();
  if (window.location.pathname === '/auth/callback') {
    try {
      await manager.signinRedirectCallback();
      log('sign-in callback finished');
    } catch (error) {
      log('sign-in callback FAILED', String(error));
    }
    window.history.replaceState({}, '', '/');
    await refreshSession();
    await loadMe();
  } else {
    await refreshSession();
  }
  // Count down from the copy in memory. Calling manager.getUser() every second would re-arm the
  // library's expiry timers each time and keep postponing automatic renewal.
  setInterval(() => {
    if (currentUser) $('s-expires').textContent = `${currentUser.expires_at - Math.floor(Date.now() / 1000)}s`;
  }, 1000);
}

$('btn-config').onclick = () => api('/auth/config', { token: false }).then((r) => { $('config').textContent = JSON.stringify(r.payload, null, 2); });
$('btn-login').onclick = () => manager.signinRedirect();
$('btn-register').onclick = () => registerManager.signinRedirect();
$('btn-logout').onclick = () => manager.signoutRedirect();
$('btn-renew').onclick = async () => {
  try { await manager.signinSilent(); log('manual renew done'); } catch (e) { log('manual renew FAILED', String(e)); }
  await refreshSession();
};
$('btn-me').onclick = loadMe;
$('btn-patch').onclick = async () => {
  const { status, payload } = await api('/me', { method: 'PATCH', body: { bio: `set from the tester at ${new Date().toISOString()}` } });
  if (status === 200) showMe(payload);
};
$('btn-admin').onclick = () => api('/admin/users?limit=3');
$('btn-internal').onclick = () => api('/internal/users');
$('btn-anon').onclick = () => api('/me', { token: false });
$('btn-landing').onclick = () => api('/landing', { token: false });
$('btn-panel').onclick = () => api('/panel');
$('btn-services').onclick = () => api('/panel/services');
$('btn-dashboard').onclick = () => api('/student/dashboard');
$('btn-notifications').onclick = () => api('/notifications');
$('btn-clear').onclick = () => { logEl.textContent = ''; };

main().catch((error) => log('startup FAILED', String(error)));
