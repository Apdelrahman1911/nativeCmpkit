// SPDX-License-Identifier: Apache-2.0
// NEW missing-only #69/#70 actual cookie transport. No fabricated browser Cookie/Host headers.
(() => {
  const focus = process.env.NATIVECMPKIT_COOKIE_WIRE_FOCUS;
  if (focus === undefined) return; // Ordinary profiles neither load a spec nor acquire a listener lease.
  if (focus !== 'remaining-v1') throw new Error('Unreviewed cookie-wire focus');
  const fs = require('node:fs');
  const path = require('node:path');
  const crypto = require('node:crypto');
  // KGP embeds fragments in a GENERATED config directory. The owning controller
  // must pass this exact reviewed source path; never search relative directories.
  const specPath = process.env.NATIVECMPKIT_COOKIE_WIRE_SPEC;
  if (!specPath || !path.isAbsolute(specPath) || path.basename(specPath) !== 'cookie-wire-v1.json')
    throw new Error('Missing explicit reviewed cookie-wire specification');
  const originalSpec = fs.lstatSync(specPath);
  if (!originalSpec.isFile() || originalSpec.isSymbolicLink() || originalSpec.size > 8192)
    throw new Error('Missing explicit regular cookie-wire specification');
  let descriptor; let rawSpec;
  try {
    descriptor = fs.openSync(specPath, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0));
    const held = fs.fstatSync(descriptor);
    if (!held.isFile() || held.size !== originalSpec.size || held.ino !== originalSpec.ino || held.dev !== originalSpec.dev)
      throw new Error('Cookie-wire specification identity changed before ingress');
    rawSpec = Buffer.alloc(held.size);
    if (fs.readSync(descriptor, rawSpec, 0, held.size, 0) !== held.size || fs.readSync(descriptor, Buffer.alloc(1), 0, 1, held.size) !== 0)
      throw new Error('Cookie-wire specification changed during bounded ingress');
  } finally { if (descriptor !== undefined) fs.closeSync(descriptor); }
  if (crypto.createHash('sha256').update(rawSpec).digest('hex') !== '7b675f4ac252be68dd2c690be90d9c97555308305bf479cdbcaf6914158d16ad')
    throw new Error('Cookie-wire specification does not match its reviewed bytes');
  const specification = JSON.parse(rawSpec.toString('utf8'));
  const rootHost = process.env.NATIVECMPKIT_COOKIE_WIRE_HOST;
  if (!/^r[0-9a-f]{32}\.nativecmpkit\.test$/.test(rootHost || '')) throw new Error('Missing owned cookie-wire DNS host');
  config.hostname = rootHost;
  config.listenAddress = '127.0.0.1';
  const subHost = 'sub.' + rootHost;
  const prefix = specification.namespace;
  const groups = specification.groups;
  const definitions = specification.cookies;
  const pages = new Set(specification.paths);
  const limits = specification.limits;
  const sessions = new Map(); const spent = new Set();
  const own = (token, suffix) => 'nativecmpkit_' + token + '_' + suffix;
  const rootPath = token => prefix + token + '/';
  const hostParts = value => {
    if (!/^[a-z0-9.-]+:[1-9][0-9]{0,4}$/.test(value || '')) return null;
    const [host, port] = value.split(':');
    if (Number(port) > 65535 || ![rootHost, subHost].includes(host)) return null;
    return { host, port };
  };
  const encodeCookie = (token, entry, remove = false) => {
    const [suffix, value] = groups[entry.group];
    let header = own(token, suffix) + '=' + (remove ? '' : value) + '; Path=' + rootPath(token) + entry.path;
    if (entry.domain) header += '; Domain=.' + rootHost;
    if (remove || entry.past) header += '; Expires=Thu, 01 Jan 1970 00:00:00 GMT';
    else if (entry.future) header += '; Expires=Fri, 01 Jan 2100 00:00:00 GMT';
    if (entry.http_only) header += '; HttpOnly';
    if (entry.secure) header += '; Secure';
    return header;
  };
  const observed = (token, raw) => {
    if (typeof raw !== 'string' || Buffer.byteLength(raw) > limits.request_header_bytes)
      throw new Error('Unreviewed cookie-wire header budget');
    const counts = groups.map(() => 0);
    for (const text of raw.split(';')) {
      const item = text.trim(); const equal = item.indexOf('=');
      if (equal <= 0) continue;
      const name = item.slice(0, equal); const value = item.slice(equal + 1);
      if (!name.startsWith('nativecmpkit_' + token + '_')) continue;
      const index = groups.findIndex(([suffix, expected]) => name === own(token, suffix) && value === expected);
      if (index < 0 || ++counts[index] > 3) throw new Error('Unexpected owned cookie value/multiplicity');
    }
    return counts;
  };
  const middleware = () => (request, response, next) => {
    if (typeof request.url !== 'string' || !request.url.startsWith(prefix)) return next();
    const pieces = request.url.slice(prefix.length).split('/');
    const [token, first, second, owner] = pieces; const stage = pieces.slice(1).join('/');
    const host = hostParts(request.headers.host);
    const sessionBefore = sessions.get(token);
    const refuse = () => {
      if (sessionBefore && (first !== 'control' || sessionBefore.owner === owner)) sessionBefore.error = 1;
      response.writeHead(409, { 'Content-Type': 'text/plain', 'Cache-Control': 'no-store', 'Connection': 'close' });
      response.end('cookie-wire-refused');
    };
    if (!host || !/^[0-9a-f]{32}$/.test(token || '') || request.method !== 'GET' || request.url.includes('?') ||
        request.url.includes('..') || request.headers['transfer-encoding'] ||
        (request.headers['content-length'] && request.headers['content-length'] !== '0') ||
        Buffer.byteLength(request.rawHeaders.join('\r\n')) > limits.request_header_bytes) { refuse(); return; }
    const headerNames = request.rawHeaders.filter((_, i) => i % 2 === 0).map(name => name.toLowerCase());
    if (new Set(headerNames).size !== headerNames.length) { refuse(); return; }
    const origin = request.headers.origin;
    const rootOrigin = 'http://' + rootHost + ':' + host.port;
    if (origin !== undefined && origin !== rootOrigin) { refuse(); return; }
    if (host.host === subHost && (!pages.has(stage) || origin !== rootOrigin)) { refuse(); return; }
    if (first === 'control' && second === 'open' && pieces.length === 4) {
      if (!/^[0-9a-f]{32}$/.test(owner || '') || host.host !== rootHost || sessions.has(token) || spent.has(token) || sessions.size >= limits.live_sessions ||
          spent.size >= limits.spent_sessions) { refuse(); return; }
      sessions.set(token, { owner, port: host.port, expires: Date.now() + limits.lifetime_seconds * 1000,
        calls: 0, error: 0, pending: new Set(), seeded: false, logout: false, closing: false });
    }
    const session = sessions.get(token);
    if (session && first === 'control' && session.owner !== owner) { refuse(); return; }
    // Error cleanup stays admitted after a stage error, budget exhaustion or expiry.
    // It can destroy ONLY this nonce's responses, never Karma's listener/socket pool.
    const isClose = first === 'control' && second === 'close' && pieces.length === 4 && host.host === rootHost && session && session.owner === owner;
    if (!session || session.port !== host.port || session.closing || (!isClose &&
        (++session.calls > limits.connections || Date.now() >= session.expires || session.pending.size >= 4))) { refuse(); return; }
    const headers = { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store, no-cache, max-age=0', 'Connection': 'close' };
    if (host.host === subHost) {
      headers['Access-Control-Allow-Origin'] = rootOrigin;
      headers['Access-Control-Allow-Credentials'] = 'true'; headers.Vary = 'Origin';
    }
    const send = payload => {
      if (Buffer.byteLength(payload) > limits.response_bytes) { session.error = 1; refuse(); return; }
      let resolveClosed;
      const lease = { response, closed: new Promise(resolve => { resolveClosed = resolve; }) };
      session.pending.add(lease);
      let finished = false;
      const timer = setTimeout(() => { session.error = 1; response.destroy(); }, 3000);
      response.once('finish', () => { finished = true; });
      response.once('close', () => {
        clearTimeout(timer); session.pending.delete(lease); if (!finished) session.error = 1; resolveClosed();
      });
      headers['Content-Length'] = Buffer.byteLength(payload);
      try { response.writeHead(200, headers); response.end(payload); }
      catch (_) { session.error = 1; response.destroy(); }
    };
    if (first === 'control') {
      if (host.host !== rootHost || pieces.length !== 4 || session.owner !== owner || !['open', 'close', 'done'].includes(second)) { refuse(); return; }
      if (second === 'done' && (session.error || session.pending.size || !session.seeded || !session.logout)) { refuse(); return; }
      if (second === 'close') {
        session.closing = true;
        const pending = [...session.pending];
        let terminal = false;
        const timer = setTimeout(() => {
          if (terminal) return; terminal = true; session.error = 1;
          response.writeHead(503, { 'Content-Type': 'text/plain', 'Connection': 'close' }); response.end('cookie-close-refused');
        }, 3000);
        for (const lease of pending) { try { lease.response.destroy(); } catch (_) { session.error = 1; } }
        Promise.all(pending.map(lease => lease.closed)).then(() => {
          if (terminal) return; terminal = true; clearTimeout(timer);
          headers['Set-Cookie'] = definitions.filter(entry => !entry.secure).map(entry => encodeCookie(token, entry, true));
          spent.add(token); sessions.delete(token); send('cookie-control|' + token + '|close|1');
        });
        return;
      }
      if (second === 'done') { spent.add(token); sessions.delete(token); }
      send('cookie-control|' + token + '|' + second + '|1'); return;
    }
    if (stage === 'seed' && host.host === rootHost && pieces.length === 2) {
      if (session.seeded) { refuse(); return; }
      session.seeded = true;
      headers['Set-Cookie'] = definitions.filter(entry => !entry.secure && !entry.managed).map(entry => encodeCookie(token, entry));
      send('cookie-control|' + token + '|seed|1'); return;
    }
    if (stage === 'logout' && host.host === rootHost && pieces.length === 2) {
      if (!session.seeded || session.logout) { refuse(); return; }
      session.logout = true;
      headers['Set-Cookie'] = definitions.filter(entry => !entry.secure).map(entry => encodeCookie(token, entry, true));
      send('cookie-control|' + token + '|logout|1'); return;
    }
    if (pages.has(stage) && session.seeded) {
      try { send('cookie-wire|' + token + '|' + observed(token, request.headers.cookie || '').join(',')); }
      catch (_) { session.error = 1; refuse(); }
      return;
    }
    refuse();
  };
  middleware.$inject = [];
  config.plugins = (config.plugins || ['karma-*']).concat({ 'middleware:nativecmpkit-cookie-wire-fixture': ['factory', middleware] });
  config.middleware = (config.middleware || []).concat('nativecmpkit-cookie-wire-fixture');
})();
