// SPDX-License-Identifier: Apache-2.0
// A lazily leased destination listener only. Karma/control and the two accepted fixtures are untouched.
(() => {
  const http = require('node:http');
  const net = require('node:net');
  const host = '127.0.0.1';
  const prefix = '/nativecmpkit-offline-fixture/';
  const sessions = new Map();
  const reply = (response, message, status = 200) => {
    if (response.destroyed || response.writableEnded) return;
    response.writeHead(status, { 'Cache-Control': 'no-store', 'Content-Type': 'text/html; charset=utf-8' });
    response.end('<!doctype html><script>parent.postMessage(' + JSON.stringify(message) + ', "*")</script>');
  };
  const timer = (session, milliseconds, callback) => {
    const handle = setTimeout(() => { session.timers.delete(handle); callback(); }, milliseconds);
    session.timers.add(handle); return handle;
  };
  const cancel = (session, handle) => { session.timers.delete(handle); clearTimeout(handle); };
  const bounded = (session, promise, milliseconds) => new Promise((resolve, reject) => {
    const handle = timer(session, milliseconds, () => reject(new Error('owned-destination-timeout')));
    promise.then(value => { cancel(session, handle); resolve(value); }, error => { cancel(session, handle); reject(error); });
  });
  const verifyClosed = session => {
    if (session.server.listening || session.server.address() !== null || !session.closeObserved ||
        session.sockets.size !== 0 || session.responses.size !== 0 || session.probes.size !== 0) {
      throw new Error('owned-destination-not-closed');
    }
  };
  const stopListener = session => {
    if (!session.closed) {
      session.phase = 'closing';
      session.closeRequested = true;
      cancel(session, session.lifetime);
      // A timed-out startup still closes its exact listener if/when the actual listen later completes.
      const closeActual = () => new Promise((resolve, reject) => {
        // Only this nonce's actual server object, never Karma, a supplied port or an unrelated listener.
        session.server.close(error => {
          if (error) { reject(new Error('owned-listener-close-refused')); return; }
          session.closeObserved = true;
          resolve();
        });
      });
      session.closed = session.started.then(closeActual, error => {
        // A refused observed address still belongs to this explicitly created server object.
        // Close that object, but never probe or grant a lease for its unaccepted port.
        if (session.server.listening) return closeActual();
        throw error;
      });
    }
    return bounded(session, session.closed, 2000);
  };
  const probeAbsent = session => {
    verifyClosed(session);
    if (sessions.get(session.token) !== session || session.port < 1 || session.phase !== 'offline') {
      return Promise.reject(new Error('unowned-absence-probe'));
    }
    return new Promise((resolve, reject) => {
      // Literal address and port observed from THIS server's successful listen(0), not a guessed unused port.
      const probe = net.createConnection({ host, port: session.port });
      let connected = false;
      let refused = false;
      let timedOut = false;
      let completeClose;
      const closed = new Promise(done => { completeClose = done; });
      session.probes.set(probe, closed);
      const timeout = timer(session, 1000, () => { timedOut = true; probe.destroy(); });
      probe.once('connect', () => { connected = true; probe.destroy(); });
      probe.once('error', error => {
        refused = error.code === 'ECONNREFUSED' && error.syscall === 'connect' &&
          error.address === host && error.port === session.port;
      });
      probe.once('close', () => {
        cancel(session, timeout);
        session.probes.delete(probe);
        completeClose();
        if (refused && !connected && !timedOut) resolve('ECONNREFUSED');
        else reject(new Error('exact-owned-port-absence-not-proved'));
      });
    });
  };
  const cleanup = async session => {
    // Failure/exit cleanup may destroy only sockets/probes belonging to this exact lease.
    for (const socket of session.sockets.keys()) socket.destroy();
    for (const probe of session.probes.keys()) probe.destroy();
    await stopListener(session);
    await bounded(session, Promise.all([...session.sockets.values(), ...session.responses.values(), ...session.probes.values()]), 2000);
    session.phase = 'offline';
    verifyClosed(session);
    if (session.port > 0) await probeAbsent(session);
    verifyClosed(session);
    if (session.timers.size !== 0) throw new Error('owned-destination-timers-remain');
  };
  const receipt = (session, kind, probe) => [kind, session.token, session.port,
    session.pages, session.completed, session.sockets.size, session.responses.size,
    session.server.listening ? 1 : 0, session.server.address() === null ? 1 : 0,
    session.closeObserved ? 1 : 0, probe, session.controls, session.expired].join('|');

  const open = async (token, controlPort) => {
    const session = { token, controlPort, port: 0, phase: 'opening', pages: 0, completed: 0, controls: 0,
      expired: 0, closeObserved: false, closeRequested: false, closed: null, sockets: new Map(), responses: new Map(), probes: new Map(), timers: new Set() };
    sessions.set(token, session); // Reserve the nonce before asynchronous listen; a collision never acquires it.
    session.server = http.createServer({ maxHeaderSize: 8192 }, (request, response) => {
      if (session.phase !== 'online' || request.method !== 'GET' ||
          request.headers.host !== host + ':' + session.port ||
          request.url !== '/nativecmpkit-offline-destination/' + token + '/page' || session.pages >= 8) {
        response.writeHead(409, { Connection: 'close' }); response.end(); return;
      }
      session.pages++;
      let completeResponse;
      session.responses.set(response, new Promise(resolve => { completeResponse = resolve; }));
      response.once('close', () => {
        session.responses.delete(response);
        if (response.writableFinished) session.completed++;
        completeResponse();
      });
      response.writeHead(200, { 'Cache-Control': 'no-store', 'Content-Type': 'text/html; charset=utf-8', Connection: 'close' });
      response.end('<!doctype html><title>owned-destination-online</title><p>owned destination</p><script>parent.postMessage(' +
        JSON.stringify(['online', token, session.port].join('|')) + ', "*")</script>');
    });
    session.server.maxConnections = 4;
    session.server.maxHeadersCount = 32;
    session.server.requestTimeout = 2000;
    session.server.headersTimeout = 2000;
    session.server.keepAliveTimeout = 1;
    session.server.on('connection', socket => {
      let completeClose;
      session.sockets.set(socket, new Promise(resolve => { completeClose = resolve; }));
      socket.setTimeout(2000, () => socket.destroy());
      socket.once('close', () => { session.sockets.delete(socket); completeClose(); });
    });
    session.server.on('error', () => { session.failed = true; });
    session.lifetime = timer(session, 60000, () => {
      session.expired++;
      cleanup(session).then(() => { if (sessions.get(token) === session) sessions.delete(token); }, () => { session.failed = true; });
    });
    try {
      session.started = new Promise((resolve, reject) => {
        const failed = () => reject(new Error('owned-listener-open-refused'));
        session.server.once('error', failed);
        session.server.listen(0, host, () => {
          session.server.removeListener('error', failed);
          const address = session.server.address();
          if (!address || address.address !== host || !Number.isInteger(address.port) ||
              address.port < 1 || address.port > 65535 || address.port === controlPort || !session.server.listening) {
            reject(new Error('owned-listener-identity-refused')); return;
          }
          session.port = address.port;
          if (!session.closeRequested) session.phase = 'online';
          resolve();
        });
      });
      await bounded(session, session.started, 2000);
      if (session.phase !== 'online' || session.closeRequested || session.failed) throw new Error('owned-open-state-refused');
      return session;
    } catch (error) {
      // No successful open receipt: the server owner, not a refused browser client, owns this cleanup.
      try { await cleanup(session); if (sessions.get(token) === session) sessions.delete(token); }
      catch (_) { session.failed = true; }
      throw error;
    }
  };

  const middleware = emitter => {
    let shuttingDown = false;
    emitter.on('exit', done => {
      shuttingDown = true;
      // Karma6.4.4 emitExitAsync waits for this callback and preserves a nonzero cleanup result.
      Promise.all(Array.from(sessions.values(), async session => {
        await cleanup(session);
        if (sessions.get(session.token) !== session) throw new Error('owned-exit-identity-refused');
        sessions.delete(session.token);
      })).then(() => done(0), () => done(1));
    });
    return (request, response, next) => {
      const url = new URL(request.url, 'http://localhost');
      if (!url.pathname.startsWith(prefix)) return next();
      const action = url.pathname.slice(prefix.length);
      const token = url.searchParams.get('token');
      const port = url.searchParams.get('port');
      if (request.method !== 'GET' || shuttingDown || !['open', 'receipt', 'offline', 'close'].includes(action) ||
          !/^[a-z0-9]{1,40}$/.test(token || '') || url.searchParams.size !== (action === 'open' ? 1 : 2) ||
          (action !== 'open' && !/^[0-9]{1,5}$/.test(port || ''))) {
        reply(response, 'invalid-offline-request', 400); return;
      }
      (async () => {
        if (action === 'open') {
          if (sessions.has(token) || sessions.size >= 4) { reply(response, 'open-refused|' + token, 409); return; }
          const session = await open(token, request.socket.localPort);
          reply(response, ['opened', token, session.port, host, 1].join('|')); return;
        }
        const session = sessions.get(token);
        if (!session || String(session.port) !== port || request.socket.localPort !== session.controlPort ||
            (action !== 'close' && (session.failed || session.expired || ++session.controls > 64))) {
          reply(response, 'unknown-or-exhausted|' + token, 409); return;
        }
        if (action === 'close') {
          await cleanup(session);
          if (sessions.get(token) !== session) throw new Error('owned-close-identity-refused');
          sessions.delete(token);
          reply(response, ['closed', token, session.port, 0].join('|')); return;
        }
        if (action === 'offline') {
          const address = session.server.address();
          if (session.phase !== 'online' || !session.server.listening || !address || address.address !== host ||
              address.port !== session.port || session.pages !== 1 || session.completed !== 1 ||
              session.sockets.size !== 0 || session.responses.size !== 0) {
            reply(response, 'offline-prerequisite-refused|' + token, 409); return;
          }
          await stopListener(session);
          session.phase = 'offline';
        } else if (session.phase !== 'online' && session.phase !== 'offline') {
          reply(response, 'offline-state-refused|' + token, 409); return;
        }
        const proof = session.phase === 'offline' ? await probeAbsent(session) : 'not-requested';
        if (session.phase === 'offline') verifyClosed(session);
        reply(response, receipt(session, action, proof));
      })().catch(() => reply(response, 'owned-offline-operation-failed|' + token, 503));
    };
  };
  middleware.$inject = ['emitter'];
  config.plugins = (config.plugins || ['karma-*']).concat({
    'middleware:nativecmpkit-offline-fixture': ['factory', middleware]
  });
  config.middleware = (config.middleware || []).concat('nativecmpkit-offline-fixture');
})();
