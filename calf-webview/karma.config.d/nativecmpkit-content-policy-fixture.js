// SPDX-License-Identifier: Apache-2.0
// NEW finite #66/#73 route lease on Karma's existing owned listener, not accepted request replay.
(() => {
  const prefix = '/nativecmpkit-content-policy/';
  const stages = {
    restore: ['url', 'navigator', 'redirect', 'final', 'html-recovery', 'null-recovery'],
    replay: ['get', 'one-time', 'form', 'posted', 'safe'],
    unsupported: ['seed', 'state-headers', 'navigator-headers', 'state-base', 'navigator-base', 'recovery']
  };
  const counterNames = ['get', 'post', 'page', 'redirect', 'script', 'style', 'image',
    'main_initial', 'main_authorization', 'script_initial', 'script_authorization',
    'style_initial', 'style_authorization', 'image_initial', 'image_authorization',
    'unexpected_initial', 'unexpected_authorization', 'response_bytes', 'closed', 'pending'];
  const sessions = new Map();
  const tombstones = new Set();
  const unicode = 'Ελληνικά العربية 漢字 café 🙂';
  const formBody = 'nativecmpkit_form=fixture-only';
  const owns = (registry, name) => Object.prototype.hasOwnProperty.call(registry, name);
  const records = values => Object.entries(values).map(([key, value]) => key + '=' + value).join('\n') + '\n';
  const controlReply = (response, token, method, values, status = 200) => {
    const message = ['policy', token, method, records(values)].join('|');
    const payload = '<!doctype html><script>parent.postMessage(' + JSON.stringify(message) +
      ', window.location.origin)</script>';
    response.writeHead(status, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
      'Content-Length': Buffer.byteLength(payload) });
    response.end(payload);
  };
  const path = (token, kind, method, stage) => prefix + token + '/' + kind + '/' + method + '/' + stage;
  const middleware = () => (request, response, next) => {
    if (!request.url.startsWith(prefix)) return next();
    const pieces = request.url.slice(prefix.length).split('/');
    const [token, kind, method, action, extra] = pieces;
    const refuse = () => {
      const session = sessions.get(token);
      if (session) session.error = 1;
      controlReply(response, 'refused', 'refused', { refused: 1 }, 409);
    };
    if (!/^[0-9a-f]{32}$/.test(token || '') || !owns(stages, method) ||
        pieces.length < 4 || pieces.length > 5 || !['control', 'page', 'base'].includes(kind) ||
        !['GET', 'POST'].includes(request.method) || request.url.includes('?') || request.url.includes('..')) {
      refuse(); return;
    }
    const rawHeaders = request.rawHeaders.join('\r\n');
    const headerNames = request.rawHeaders.filter((_, index) => index % 2 === 0).map(name => name.toLowerCase());
    if (Buffer.byteLength(rawHeaders) > 8192 || new Set(headerNames).size !== headerNames.length ||
        request.headers['transfer-encoding'] || !/^[0-9]{1,4}$/.test(request.headers['content-length'] || '0') ||
        Number(request.headers['content-length'] || '0') > 512 ||
        (request.method === 'GET' && Number(request.headers['content-length'] || '0') !== 0)) { refuse(); return; }
    if (kind === 'control' && action === 'open') {
      if (request.method !== 'GET' || pieces.length !== 4 || sessions.has(token) || tombstones.has(token) ||
          sessions.size + tombstones.size >= 16) { refuse(); return; }
      sessions.set(token, { method, rows: Object.fromEntries(stages[method].map(stage =>
        [stage, Object.fromEntries(counterNames.map(key => [key, 0]))])), connections: 1, error: 0, pending: new Set() });
      controlReply(response, token, method, { opened: 1 }); return;
    }
    const session = sessions.get(token);
    if (!session || session.method !== method || ++session.connections > 512) { refuse(); return; }
    if (kind === 'control') {
      if (request.method !== 'GET') { refuse(); return; }
      if (action === 'stats' && owns(session.rows, extra) && pieces.length === 5) {
        controlReply(response, token, method, { ...session.rows[extra], fixture_error: session.error }); return;
      }
      if (action === 'done' && pieces.length === 4) {
        if (session.error || session.pending.size || Object.values(session.rows).some(count => count.pending !== 0)) {
          refuse(); return;
        }
        tombstones.add(token); sessions.delete(token);
        controlReply(response, token, method, { done: 1 }); return;
      }
      if (action === 'close' && pieces.length === 4) {
        // Error cleanup owns only this nonce's response leases, not Karma's listener/socket pool.
        const pending = [...session.pending];
        let terminal = false;
        const timer = setTimeout(() => {
          if (terminal) return;
          terminal = true; session.error = 1;
          controlReply(response, token, method, { closed: 0, fixture_error: 1 }, 503);
        }, 2000);
        for (const lease of pending) {
          try { lease.response.destroy(); } catch (_) { session.error = 1; }
        }
        Promise.all(pending.map(lease => lease.closed)).then(() => {
          if (terminal) return;
          terminal = true; clearTimeout(timer);
          tombstones.add(token); sessions.delete(token);
          controlReply(response, token, method, { closed: 1, fixture_error: session.error });
        });
        return;
      }
      refuse(); return;
    }
    if (!owns(session.rows, action) || (kind === 'page' && pieces.length !== 4) ||
        (kind === 'base' && !['probe.js', 'probe.css', 'probe.svg'].includes(extra))) { refuse(); return; }
    const counts = session.rows[action];
    if (counts.get + counts.post >= 12 || session.pending.size >= 16) { refuse(); return; }
    const timer = setTimeout(() => { session.error = 1; response.destroy(); }, 3000);
    let resolveClosed;
    const lease = { response, closed: new Promise(resolve => { resolveClosed = resolve; }) };
    session.pending.add(lease);
    let admitted = false;
    let completed = false;
    response.once('finish', () => { completed = true; });
    response.once('close', () => {
      clearTimeout(timer);
      session.pending.delete(lease);
      if (admitted) { counts.closed++; counts.pending--; }
      if (!completed) session.error = 1;
      resolveClosed();
    });
    let body = '';
    request.setEncoding('utf8');
    request.on('data', chunk => {
      body += chunk;
      if (Buffer.byteLength(body) > 512) { session.error = 1; response.destroy(); }
    });
    request.on('aborted', () => { session.error = 1; response.destroy(); });
    request.on('end', () => {
      if (response.destroyed) return;
      if ((request.method === 'GET' && body) || (request.method === 'POST' &&
          !(method === 'replay' && kind === 'page' && action === 'posted' && body === formBody))) { refuse(); return; }
      admitted = true; counts.pending++; counts[request.method.toLowerCase()]++;
      const role = kind === 'page' ? 'main' : { 'probe.js': 'script', 'probe.css': 'style', 'probe.svg': 'image' }[extra];
      const initial = Number(request.headers['x-nativecmpkit-initial'] === 'fixture-only-' + token);
      const authorization = Number(request.headers.authorization === 'NativeCmpKitFixture ' + token);
      counts[role + '_initial'] += initial; counts[role + '_authorization'] += authorization;
      counts.unexpected_initial += Number('x-nativecmpkit-initial' in request.headers && !initial);
      counts.unexpected_authorization += Number('authorization' in request.headers && !authorization);
      let payload; let mime = 'text/html; charset=utf-8'; let status = 200; let location;
      if (kind === 'base') {
        counts[role]++;
        if (role === 'script') {
          payload = "document.documentElement.setAttribute('data-policy-script','h" + initial + '-a' + authorization + "');" +
            "document.getElementById('relative-resource-text').textContent='ресурс 日本語 café 🙂';";
          mime = 'application/javascript; charset=utf-8';
        } else if (role === 'style') {
          payload = '#policy-document { color: rgb(17, 34, 51); }'; mime = 'text/css; charset=utf-8';
        } else {
          payload = '<svg xmlns="http://www.w3.org/2000/svg" width="7" height="9"><rect width="7" height="9" fill="#123"/></svg>';
          mime = 'image/svg+xml';
        }
      } else if (method === 'restore' && action === 'redirect') {
        counts.redirect++; status = 302; location = path(token, 'page', method, 'final'); payload = '';
      } else if (method === 'replay' && action === 'one-time' && counts.get > 1) {
        status = 409; session.error = 1; payload = 'One-time fixture URL was repeated';
      } else if (method === 'replay' && action === 'posted' && request.method !== 'POST') {
        status = 405; session.error = 1; payload = 'Fixture form result is POST only';
      } else {
        counts.page++;
        const title = method + '-' + action + '-' + counts.page;
        payload = '<!doctype html><meta charset="utf-8"><link rel="icon" href="data:,"><title>' + title + '</title>' +
          '<p id="policy-document">' + unicode + '</p><p id="relative-resource-text"></p>';
        if (method === 'replay' && action === 'form') payload += '<form id="policy-form" method="post" action="' +
          path(token, 'page', method, 'posted') + '"><input name="nativecmpkit_form" value="fixture-only"><button type="submit">submit</button></form>';
      }
      const headers = { 'Content-Type': mime, 'Content-Length': Buffer.byteLength(payload),
        'Cache-Control': 'no-store, no-cache, max-age=0', 'Connection': 'close' };
      if (location) headers.Location = location;
      response.writeHead(status, headers);
      // Only authored response bytes actually written to this HTTP response are counted.
      response.end(payload, () => { counts.response_bytes += Buffer.byteLength(payload); });
    });
  };
  middleware.$inject = [];
  config.plugins = (config.plugins || ['karma-*']).concat({
    'middleware:nativecmpkit-content-policy-fixture': ['factory', middleware]
  });
  config.middleware = (config.middleware || []).concat('nativecmpkit-content-policy-fixture');
})();
