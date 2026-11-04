// SPDX-License-Identifier: Apache-2.0
// NEW SOURCE/MODEL controls. Mock requests/responses are NOT browser/native/network evidence.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { EventEmitter } = require('node:events');
const root = path.resolve(__dirname, '../../..');
const source = fs.readFileSync(path.join(root, 'calf-webview/karma.config.d/nativecmpkit-cookie-wire-fixture.js'), 'utf8');
const specPath = path.join(root, 'scripts/ci/fixtures/cookie-wire-v1.json');
const token = '0'.repeat(32), owner = '1'.repeat(32), foreignToken = '2'.repeat(32), foreignOwner = '3'.repeat(32);
const host = 'r' + token + '.nativecmpkit.test';
const rootOrigin = 'http://' + host + ':17891';
function config(env = {}) {
  const result = { plugins: ['retained-model-plugin'], middleware: ['retained-model-middleware'] };
  vm.runInNewContext(source, { config: result, process: { env }, require, Buffer, setTimeout, clearTimeout });
  return result;
}
function fixture() {
  const result = config({ NATIVECMPKIT_COOKIE_WIRE_FOCUS: 'remaining-v1', NATIVECMPKIT_COOKIE_WIRE_SPEC: specPath,
    NATIVECMPKIT_COOKIE_WIRE_HOST: host });
  const plugin = result.plugins.find(item => typeof item === 'object');
  return plugin['middleware:nativecmpkit-cookie-wire-fixture'][1]();
}
class Response extends EventEmitter {
  constructor(hold = false) { super(); this.hold = hold; this.destroyed = false; this.status = 0; }
  writeHead(status, headers) { this.status = status; this.headers = headers; }
  end(body) { this.body = body; if (!this.hold) { this.emit('finish'); this.emit('close'); } }
  destroy() { if (!this.destroyed) { this.destroyed = true; this.emit('close'); } }
}
function request(route, { sub = false, cookie = '', nonce = token, rawHeaders, origin, hold = false, method = 'GET' } = {}) {
  const headers = { host: (sub ? 'sub.' : '') + host + ':17891', cookie };
  if (origin !== undefined) headers.origin = origin;
  return [{ url: '/nativecmpkit-cookie-wire/' + nonce + '/' + route, method, headers,
    rawHeaders: rawHeaders || Object.entries(headers).flat() }, new Response(hold)];
}
function call(middleware, route, options) { const [req, res] = request(route, options); middleware(req, res, () => assert.fail('Unexpected model fallthrough')); return res; }
async function turn() { await new Promise(resolve => setImmediate(resolve)); }

test('ordinary profiles keep retained config and require no specification or owned DNS lease', () => {
  const result = config();
  assert.deepEqual(result.plugins, ['retained-model-plugin']);
  assert.deepEqual(result.middleware, ['retained-model-middleware']);
  assert.equal(result.hostname, undefined);
});
test('explicit focus refuses missing guessed spec path and unowned hostname', () => {
  assert.throws(() => config({ NATIVECMPKIT_COOKIE_WIRE_FOCUS: 'unreviewed' }), /Unreviewed cookie-wire focus/);
  assert.throws(() => config({ NATIVECMPKIT_COOKIE_WIRE_FOCUS: 'remaining-v1' }), /explicit reviewed/);
  assert.throws(() => config({ NATIVECMPKIT_COOKIE_WIRE_FOCUS: 'remaining-v1', NATIVECMPKIT_COOKIE_WIRE_SPEC: specPath,
    NATIVECMPKIT_COOKIE_WIRE_HOST: 'foreign.invalid' }), /owned cookie-wire DNS host/);
});
test('model seed creates actual server Set-Cookie definitions including duplicates HttpOnly and expiry', () => {
  const middleware = fixture();
  assert.equal(call(middleware, 'control/open/' + owner).status, 200);
  const seeded = call(middleware, 'seed');
  const headers = seeded.headers['Set-Cookie'];
  assert.equal(headers.length, 12); // 14 total definitions, minus Secure and manager-owned.
  assert.equal(headers.filter(value => value.startsWith('nativecmpkit_' + token + '_equal=')).length, 2);
  assert(headers.some(value => value.includes('; HttpOnly')));
  assert(headers.some(value => value.includes('Expires=Thu, 01 Jan 1970')));
  assert(headers.some(value => value.includes('Expires=Fri, 01 Jan 2100')));
  assert(!headers.some(value => value.includes('; Secure')));
  assert(headers.some(value => value.includes('/' + token + '/private')));
  assert.equal(call(middleware, 'seed').status, 409);
});
test('model observed incoming Cookie counts retain duplicate equal values and filter foreign bytes', () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed');
  const raw = 'foreign=model-only; nativecmpkit_' + token + '_scope=root; nativecmpkit_' + token + '_scope=foo; ' +
    'nativecmpkit_' + token + '_equal=same; nativecmpkit_' + token + '_equal=same';
  const reply = call(middleware, 'foo/child', { cookie: raw });
  assert.equal(reply.status, 200);
  assert.equal(reply.body, 'cookie-wire|' + token + '|1,1,0,0,0,0,0,0,0,0,0,2');
  assert(!reply.body.includes('foreign'));
});
test('credentialed subhost CORS is exact root-origin GET only and rejects duplicate raw headers', () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed');
  const allowed = call(middleware, 'foo', { sub: true, origin: rootOrigin });
  assert.equal(allowed.status, 200); assert.equal(allowed.headers['Access-Control-Allow-Origin'], rootOrigin);
  assert.equal(allowed.headers['Access-Control-Allow-Credentials'], 'true');
  assert.equal(call(middleware, 'public', { sub: true, origin: 'http://foreign.invalid:17891' }).status, 409);
  assert.equal(call(middleware, 'foo', { rawHeaders: ['Host', host + ':17891', 'HOST', host + ':17891'] }).status, 409);
});
test('model done refuses partial stages and exact server logout expires owned HttpOnly path identities', () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed');
  assert.equal(call(middleware, 'control/done/' + owner).status, 409);
  const logout = call(middleware, 'logout');
  assert.equal(logout.headers['Set-Cookie'].length, 13);
  assert(logout.headers['Set-Cookie'].every(value => value.includes('Expires=Thu, 01 Jan 1970')));
  assert(logout.headers['Set-Cookie'].some(value => value.includes('; HttpOnly')));
});
test('owned close drains only the exact nonce and refuses foreign control ownership without disposal', async () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed');
  call(middleware, 'control/open/' + foreignOwner, { nonce: foreignToken }); call(middleware, 'seed', { nonce: foreignToken });
  const ownResponse = call(middleware, 'foo', { hold: true });
  const foreignResponse = call(middleware, 'foo', { nonce: foreignToken, hold: true });
  const denied = call(middleware, 'control/close/' + owner, { nonce: foreignToken });
  assert.equal(denied.status, 409); assert.equal(foreignResponse.destroyed, false);
  const closing = call(middleware, 'control/close/' + owner); await turn();
  assert.equal(closing.status, 200); assert.equal(ownResponse.destroyed, true); assert.equal(foreignResponse.destroyed, false);
  const foreignClosing = call(middleware, 'control/close/' + foreignOwner, { nonce: foreignToken }); await turn();
  assert.equal(foreignClosing.status, 200); assert.equal(foreignResponse.destroyed, true);
  assert.equal(call(middleware, 'control/open/' + owner).status, 409); // Spent identity cannot be replayed.
});
test('successful model logout and done is bounded but is explicitly not a browser/native method result', () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed'); call(middleware, 'logout');
  assert.equal(call(middleware, 'control/done/' + owner).status, 200);
  assert.equal(call(middleware, 'control/open/' + owner).status, 409);
});
test('NEW private and public are distinct admitted model paths, not unowned fallback routes', () => {
  const middleware = fixture(); call(middleware, 'control/open/' + owner); call(middleware, 'seed');
  assert.equal(call(middleware, 'private').status, 200);
  assert.equal(call(middleware, 'public').status, 200);
  assert.equal(call(middleware, 'private-extra').status, 409);
});
