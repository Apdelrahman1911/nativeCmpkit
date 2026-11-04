// SPDX-License-Identifier: Apache-2.0
// NEW bounded real HTTP middleware controls, not browser/DOM/native executions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const crypto = require('node:crypto');

const sourcePath = path.resolve(__dirname, '../../calf-webview/karma.config.d/nativecmpkit-content-policy-fixture.js');
async function withFixture(method, body) {
  const config = { plugins: [], middleware: [] };
  vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), { config, URL, Buffer, setTimeout, clearTimeout, Map, Set, Promise });
  assert.deepEqual(config.middleware, ['nativecmpkit-content-policy-fixture']);
  const middleware = config.plugins[0]['middleware:nativecmpkit-content-policy-fixture'][1]();
  const server = http.createServer((request, response) => middleware(request, response, () => {
    response.writeHead(404); response.end('not-an-owned-content-route');
  }));
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const token = crypto.randomBytes(16).toString('hex');
  const base = 'http://127.0.0.1:' + server.address().port + '/nativecmpkit-content-policy/' + token + '/';
  const fixture = {
    base, method,
    url: (kind, stage) => base + kind + '/' + method + '/' + stage,
    async trip(kind, stage, verb = 'GET', bytes, headers) {
      const url = fixture.url(kind, stage);
      return new Promise((resolve, reject) => {
        const request = http.request(url, { method: verb, headers, agent: false }, response => {
          const chunks = [];
          response.on('data', chunk => chunks.push(chunk));
          response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString('utf8') }));
          response.on('error', reject);
        });
        request.on('error', reject); request.setTimeout(4000, () => request.destroy(new Error('Bounded control timeout')));
        request.end(bytes);
      });
    },
    async control(action) {
      const result = await fixture.trip('control', action);
      assert.equal(result.status, 200);
      const matched = result.body.match(/parent\.postMessage\((.*), window\.location\.origin\)/);
      assert.ok(matched);
      const parts = JSON.parse(matched[1]).split('|');
      assert.deepEqual(parts.slice(0, 3), ['policy', token, method]);
      const rows = parts[3].trim().split('\n').map(row => {
        assert.match(row, /^[a-z_]+=[0-9]{1,10}$/); const [key, value] = row.split('='); return [key, Number(value)];
      });
      assert.equal(new Set(rows.map(([key]) => key)).size, rows.length);
      return Object.fromEntries(rows);
    },
    async stats(stage) {
      let result;
      const deadline = Date.now() + 3000;
      do {
        result = await fixture.control('stats/' + stage);
        if (!result.pending) return result;
        await new Promise(resolve => setTimeout(resolve, 5));
      } while (Date.now() < deadline);
      throw new Error('Owned HTTP response failed to drain');
    }
  };
  try { await fixture.control('open'); await body(fixture); }
  finally { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
}

test('real owned GET generations and numeric receipts exclude control requests', async () => {
  await withFixture('restore', async fixture => {
    for (const count of [1, 2]) {
      const result = await fixture.trip('page', 'url');
      assert.equal(result.status, 200); assert.match(result.headers['cache-control'], /no-store/);
      assert.ok(result.body.includes('<title>restore-url-' + count + '</title>'));
      assert.ok(result.body.includes('Ελληνικά العربية 漢字 café 🙂'));
    }
    const counts = await fixture.stats('url');
    assert.equal(counts.get, 2); assert.equal(counts.page, 2); assert.equal(counts.post, 0); assert.equal(counts.closed, 2);
    assert.ok(counts.response_bytes > 0); assert.equal(counts.fixture_error, 0);
    assert.equal((await fixture.control('done')).done, 1);
  });
});

test('actual 302 final URL remount counts do not replay original redirect route', async () => {
  await withFixture('restore', async fixture => {
    const redirect = await fixture.trip('page', 'redirect');
    assert.equal(redirect.status, 302);
    assert.ok(fixture.url('page', 'final').endsWith(redirect.headers.location));
    for (const count of [1, 2]) {
      assert.ok((await fixture.trip('page', 'final')).body.includes('restore-final-' + count));
    }
    assert.equal((await fixture.stats('redirect')).redirect, 1);
    assert.equal((await fixture.stats('final')).get, 2);
    assert.equal((await fixture.control('done')).done, 1);
  });
});

test('genuine form POST result and one-time GET are finite independent counters', async () => {
  await withFixture('replay', async fixture => {
    assert.equal((await fixture.trip('page', 'one-time')).status, 200);
    assert.ok((await fixture.trip('page', 'form')).body.includes('method="post"'));
    const bytes = 'nativecmpkit_form=fixture-only';
    const posted = await fixture.trip('page', 'posted', 'POST', bytes, {
      'Content-Length': Buffer.byteLength(bytes), 'Content-Type': 'application/x-www-form-urlencoded'
    });
    assert.equal(posted.status, 200); assert.ok(posted.body.includes('replay-posted-1'));
    const counts = await fixture.stats('posted');
    assert.equal(counts.post, 1); assert.equal(counts.get, 0); assert.equal(counts.page, 1);
    assert.equal((await fixture.stats('one-time')).get, 1);
    assert.equal((await fixture.control('done')).done, 1);
  });
});

test('actual prohibited GET replay of one-time or POST-only fixture stays red', async () => {
  for (const stage of ['one-time', 'posted']) await withFixture('replay', async fixture => {
    if (stage === 'one-time') assert.equal((await fixture.trip('page', stage)).status, 200);
    assert.equal((await fixture.trip('page', stage)).status, stage === 'one-time' ? 409 : 405);
    const counts = await fixture.stats(stage);
    assert.equal(counts.fixture_error, 1);
    assert.equal(counts.page, stage === 'one-time' ? 1 : 0);
    assert.equal((await fixture.control('close')).fixture_error, 1);
  });
});

test('unattempted rejected routes remain zero but genuine asset attempts are counted', async () => {
  await withFixture('unsupported', async fixture => {
    await fixture.trip('page', 'seed');
    for (const stage of ['state-headers', 'navigator-headers', 'state-base', 'navigator-base']) {
      const counts = await fixture.stats(stage);
      for (const key of ['get', 'post', 'page', 'script', 'style', 'image']) assert.equal(counts[key], 0);
    }
    for (const asset of ['probe.js', 'probe.css', 'probe.svg']) assert.equal((await fixture.trip('base', 'state-base/' + asset)).status, 200);
    const counts = await fixture.stats('state-base');
    assert.equal(counts.get, 3); assert.equal(counts.script, 1); assert.equal(counts.style, 1); assert.equal(counts.image, 1);
    assert.equal((await fixture.control('done')).done, 1);
  });
});

test('duplicate process lease and spent nonce cannot silently reopen or admit content', async () => {
  await withFixture('restore', async fixture => {
    assert.equal((await fixture.trip('control', 'open')).status, 409);
    assert.equal((await fixture.control('close')).fixture_error, 1);
    assert.equal((await fixture.trip('control', 'open')).status, 409);
    assert.equal((await fixture.trip('page', 'url')).status, 409);
  });
});

test('duplicate header and oversized body refusal are before content admission', async () => {
  await withFixture('replay', async fixture => {
    const duplicate = await fixture.trip('page', 'get', 'GET', undefined,
      ['Host', '127.0.0.1', 'X-Own-Header', 'one', 'X-Own-Header', 'two']);
    assert.equal(duplicate.status, 409);
    const large = await fixture.trip('page', 'posted', 'POST', 'x'.repeat(513), { 'Content-Length': 513 });
    assert.equal(large.status, 409);
    assert.equal((await fixture.stats('get')).get, 0); assert.equal((await fixture.stats('posted')).post, 0);
    assert.equal((await fixture.control('close')).fixture_error, 1);
  });
});

test('independent close acquires native response close events for only its partial request', async () => {
  await withFixture('replay', async fixture => {
    const partial = http.request(fixture.url('page', 'posted'), { method: 'POST', agent: false,
      headers: { 'Content-Length': 29 } });
    const terminal = new Promise(resolve => { partial.on('error', resolve); partial.on('close', resolve); });
    partial.write('nativecmpkit_form=');
    // An actual later control round trip observes the route lease after request headers reached the server.
    await fixture.control('stats/posted');
    const closed = await fixture.control('close');
    assert.equal(closed.closed, 1); assert.equal(closed.fixture_error, 1);
    await terminal;
  });
});

test('finite own method and stage registries refuse prototype properties before admission', async () => {
  await withFixture('restore', async fixture => {
    for (const stage of ['toString', 'constructor', '__proto__']) {
      assert.equal((await fixture.trip('page', stage)).status, 409);
      assert.equal((await fixture.trip('control', 'stats/' + stage)).status, 409);
    }
    const ownUrl = fixture.url;
    try {
      for (const method of ['toString', 'constructor', '__proto__']) {
        fixture.url = (kind, stage) => fixture.base + kind + '/' + method + '/' + stage;
        assert.equal((await fixture.trip('control', 'open')).status, 409);
      }
    } finally { fixture.url = ownUrl; }
    assert.equal((await fixture.stats('url')).get, 0);
    assert.equal((await fixture.control('close')).fixture_error, 1);
  });
});

test('GET body is refused for actual control and content ingress without hidden admission', async () => {
  await withFixture('replay', async fixture => {
    for (const [kind, stage] of [['control', 'stats/get'], ['page', 'get']]) {
      assert.equal((await fixture.trip(kind, stage, 'GET', 'x', { 'Content-Length': 1 })).status, 409);
    }
    assert.equal((await fixture.stats('get')).get, 0);
    assert.equal((await fixture.control('close')).fixture_error, 1);
  });
});
