// SPDX-License-Identifier: Apache-2.0
// Finite #64 request responses on Karma's existing owned HTTP listener.
// The accepted iframe/CSP/XFO fixture is deliberately unchanged.
(() => {
  const prefix = '/nativecmpkit-request-fixture/';
  const actions = ['open', 'page', 'hold', 'redirect', 'abort', 'receipt', 'release', 'close'];
  const sessions = new Map();
  const reply = (response, message, status = 200) => {
    response.writeHead(status, {
      'Cache-Control': 'no-store', 'Content-Type': 'text/html; charset=utf-8'
    });
    response.end('<!doctype html><script>parent.postMessage(' + JSON.stringify(message) + ', "*")</script>');
  };
  const pageScript = (token, stage, phase) =>
    '<script>document.documentElement.setAttribute("data-nativecmpkit-request-ready", ' +
    JSON.stringify(phase === 'held' ? 'holding' : 'yes') + ');parent.postMessage(' +
    JSON.stringify([phase, token, stage].join('|')) + ', "*");</script>';
  const middleware = () => (request, response, next) => {
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith(prefix)) return next();
    const action = url.pathname.slice(prefix.length);
    const token = url.searchParams.get('token');
    const stage = url.searchParams.get('stage') || 'receipt';
    if (request.method !== 'GET' || !actions.includes(action) ||
        !/^[a-z0-9]{1,40}$/.test(token || '') || !/^[a-z0-9-]{1,60}$/.test(stage)) {
      reply(response, 'invalid-request', 400); return;
    }
    if (action === 'open') {
      if (sessions.has(token) || sessions.size >= 32) {
        reply(response, 'open-refused|' + token, 409); return;
      }
      sessions.set(token, { stages: new Map(), pending: new Map(), requests: 0, location: '', closing: false });
      reply(response, 'opened|' + token); return;
    }
    const session = sessions.get(token);
    // A spent work budget must never strand an already acquired cleanup lease.
    if (!session || session.closing || (action !== 'close' && ++session.requests > 128)) {
      reply(response, 'unknown-or-exhausted|' + token, 409); return;
    }
    if (action === 'receipt') {
      const rows = Array.from(session.stages.entries()).sort(([a], [b]) => a.localeCompare(b)).map(([name, count]) =>
        [name, count.page, count.hold, count.redirect, count.abort, count.abortClosed,
          count.holdCompleted, count.holdCancelled, count.expired,
          session.pending.has(name) ? 1 : 0].join(','));
      reply(response, ['receipt', token, rows.join(';'), session.location].join('|')); return;
    }
    if (action === 'release') {
      const lease = session.pending.get(stage);
      if (!lease || lease.completed || lease.response.destroyed) {
        reply(response, ['release-refused', token, stage].join('|'), 409); return;
      }
      lease.completed = true;
      lease.response.end(pageScript(token, stage, 'page') + '</body></html>');
      // The native close event owns removal; writing end() alone is not cleanup evidence.
      lease.closed.then(() => reply(response, ['released', token, stage, 1].join('|')));
      return;
    }
    if (action === 'close') {
      session.closing = true;
      const leases = Array.from(session.pending.values());
      for (const lease of leases) lease.response.destroy();
      let terminal = false;
      const timer = setTimeout(() => {
        if (terminal) return;
        terminal = true;
        reply(response, 'close-failed|' + token, 503);
      }, 2000);
      Promise.all(leases.map(lease => lease.closed)).then(() => {
        if (terminal) return;
        terminal = true;
        clearTimeout(timer);
        if (session.pending.size !== 0 || sessions.get(token) !== session) {
          reply(response, 'close-failed|' + token, 503); return;
        }
        sessions.delete(token);
        reply(response, 'closed|' + token + '|0');
      });
      return;
    }
    if (!session.stages.has(stage)) {
      if (session.stages.size >= 16) { reply(response, 'stage-capacity|' + token, 409); return; }
      session.stages.set(stage, { page: 0, hold: 0, redirect: 0, abort: 0, abortClosed: 0,
        holdCompleted: 0, holdCancelled: 0, expired: 0 });
    }
    const counts = session.stages.get(stage);
    if (action === 'abort') {
      counts.abort++;
      response.once('close', () => { counts.abortClosed++; });
      // Actual transport refusal before headers/body, not an iframe error-event injection.
      // Browsers may retry GET; receipts retain every attempt rather than inventing exactly one.
      response.destroy(); return;
    }
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (action === 'redirect') {
      const target = prefix + 'hold?token=' + token + '&stage=' + stage + '-final';
      // Only a validated, session-owned relative destination; no supplied redirect or host.
      if ((stage + '-final').length > 60) { reply(response, 'stage-too-long|' + token, 400); return; }
      counts.redirect++;
      response.setHeader('Location', target);
      session.location = response.getHeader('Location');
      response.writeHead(302); response.end(); return;
    }
    if (action === 'hold') {
      if (session.pending.has(stage) || session.pending.size >= 4) {
        reply(response, 'hold-refused|' + token, 409); return;
      }
      counts.hold++;
      let completeClose;
      const lease = { response, completed: false, closed: new Promise(resolve => { completeClose = resolve; }) };
      session.pending.set(stage, lease);
      const timer = setTimeout(() => {
        if (session.pending.get(stage) !== lease) return;
        counts.expired++;
        response.destroy();
      }, 20000);
      response.once('close', () => {
        clearTimeout(timer);
        if (session.pending.get(stage) === lease) session.pending.delete(stage);
        if (lease.completed) counts.holdCompleted++; else counts.holdCancelled++;
        completeClose();
      });
      response.writeHead(200);
      response.write('<!doctype html><html><head><title>' + stage + '</title></head><body>' +
        '<p id="nativecmpkit-request-stage">' + stage + '</p>' + pageScript(token, stage, 'held') +
        // Chromium must receive enough bytes to commit/execute while the response remains open.
        ' '.repeat(2048));
      return;
    }
    counts.page++;
    response.end('<!doctype html><html><head><title>' + stage + '</title></head><body>' +
      '<p id="nativecmpkit-request-stage">' + stage + '</p>' + pageScript(token, stage, 'page') + '</body></html>');
  };
  middleware.$inject = [];
  config.plugins = (config.plugins || ['karma-*']).concat({
    'middleware:nativecmpkit-request-fixture': ['factory', middleware]
  });
  config.middleware = (config.middleware || []).concat('nativecmpkit-request-fixture');
})();
