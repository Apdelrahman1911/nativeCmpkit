// SPDX-License-Identifier: Apache-2.0
// Local test responses on Karma's existing server; no package, file, or external-network access.
// The different loopback host name supplies a genuine second browser origin.
(() => {
  const prefix = '/nativecmpkit-iframe-fixture/';
  const sessions = new Map();
  const middleware = () => (request, response, next) => {
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith(prefix)) return next();
    const action = url.pathname.slice(prefix.length);
    const token = url.searchParams.get('token');
    const stage = url.searchParams.get('stage') || 'receipt';
    if (request.method !== 'GET' || !/^[a-z0-9]{1,40}$/.test(token || '') ||
        !/^[a-z0-9-]{1,60}$/.test(stage) || !['allow', 'csp', 'xfo', 'receipt', 'close'].includes(action)) {
      response.writeHead(400); response.end(); return;
    }
    response.setHeader('Cache-Control', 'no-store');
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (action === 'close') {
      sessions.delete(token);
      response.end('<script>parent.postMessage(' + JSON.stringify('closed|' + token) + ', "*")</script>');
      return;
    }
    if (!sessions.has(token)) {
      if (sessions.size >= 64) { response.writeHead(503); response.end(); return; }
      sessions.set(token, { allow: 0, csp: 0, xfo: 0, cspPolicy: '', xfoPolicy: '' });
    }
    const counts = sessions.get(token);
    let message;
    if (action === 'receipt') {
      message = ['receipt', token, counts.allow, counts.csp, counts.xfo,
        counts.cspPolicy, counts.xfoPolicy].join('|');
    } else {
      counts[action]++;
      if (action === 'csp') {
        response.setHeader('Content-Security-Policy', "frame-ancestors 'none'");
        counts.cspPolicy = response.getHeader('Content-Security-Policy');
      }
      if (action === 'xfo') {
        response.setHeader('X-Frame-Options', 'DENY');
        counts.xfoPolicy = response.getHeader('X-Frame-Options');
      }
      message = ['page', token, stage].join('|');
    }
    response.end('<!doctype html><title>' + stage + '</title><p id="nativecmpkit-page">' + stage +
      '</p><script>document.documentElement.setAttribute("data-nativecmpkit-ready", "yes");' +
      'parent.postMessage(' + JSON.stringify(message) + ', "*");</script>');
  };
  // Karma's legacy DI parser only infers classic function arguments; this factory owns no services.
  middleware.$inject = [];
  config.plugins = (config.plugins || ['karma-*']).concat({
    'middleware:nativecmpkit-iframe-fixture': ['factory', middleware]
  });
  config.middleware = (config.middleware || []).concat('nativecmpkit-iframe-fixture');
})();
