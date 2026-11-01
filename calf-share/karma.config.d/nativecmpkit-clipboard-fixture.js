// SPDX-License-Identifier: Apache-2.0
// Four missing #82 C3 paths only. The same compiled library test bundle runs in each actual child realm.
(() => {
  const klass = 'com.mohamedrejeb.calf.share.WebClipboardEnvironmentAcceptanceTest';
  const methods = Object.freeze({
    missing: 'secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls',
    insecure: 'genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable',
    denied: 'actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess',
    gesture: 'directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite'
  });
  const args = config.client && config.client.args || [];
  const includes = [], excludes = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--tests' || args[i] === '--include') includes.push(String(args[++i] || ''));
    else if (args[i] === '--exclude') excludes.push(String(args[++i] || ''));
  }
  const matches = pattern => {
    const escaped = pattern.split('*').map(s => s.replace(/[.*+?^()|[\]\\{}$]/g, '\\$&')).join('.*');
    const expression = new RegExp('^' + escaped + '(?:\\.[^.]+)?$');
    return Object.values(methods).some(method => expression.test(klass + '.' + method)) || expression.test(klass);
  };
  // Accepted finite Promise-only filters keep their original launcher/configuration.
  const requested = (includes.length === 0 || includes.some(matches)) &&
    !excludes.some(p => p === klass || p === klass + '.*' || p === '*');
  if (!requested) return;

  const fs = require('node:fs');
  const path = require('node:path');
  const WebSocket = require('ws'); // Existing Karma dependency, not a new production/npm dependency.
  const base = require('karma-chrome-launcher')['launcher:ChromeHeadless'][1];
  const prefix = '/nativecmpkit-clipboard-fixture/';
  const insecureHost = 'nativecmpkit-clipboard-insecure.invalid';
  const owners = new Set(), sessions = new Map(), timers = new Set();
  const later = (milliseconds, callback) => {
    const handle = setTimeout(() => { timers.delete(handle); callback(); }, milliseconds);
    timers.add(handle); return handle;
  };
  const cancel = handle => { if (handle) { clearTimeout(handle); timers.delete(handle); } };
  const bounded = (promise, milliseconds) => new Promise((resolve, reject) => {
    const timer = later(milliseconds, () => reject(new Error('owned-clipboard-operation-timeout')));
    promise.then(value => { cancel(timer); resolve(value); }, error => { cancel(timer); reject(error); });
  });

  function OwnedClipboardHeadless(baseBrowserDecorator, args, finalConfig) {
    // Karma has finalized/restored defaults and reapplied CLI options before this owning construction.
    if (!finalConfig || finalConfig.hostname !== 'localhost' || finalConfig.listenAddress !== '127.0.0.1' ||
        finalConfig.protocol !== 'http:' || finalConfig.urlRoot !== '/' || !Array.isArray(finalConfig.browsers) ||
        finalConfig.browsers.length !== 1 || finalConfig.browsers[0] !== 'OwnedClipboardHeadless') {
      throw new Error('Native clipboard fixture requires the finalized literal owned loopback Karma/Chrome profile');
    }
    if (args.chromeDataDir || (args.flags && args.flags.length)) throw new Error('Clipboard fixture requires the unmodified disposable Karma profile');
    base.call(this, baseBrowserDecorator, {
      flags: ['--remote-debugging-port=0', '--host-resolver-rules=MAP ' + insecureHost + ' 127.0.0.1']
    });
    const launcher = this;
    this.name = 'OwnedClipboardHeadless';
    let profile = null;
    const originalOptions = this._getOptions;
    this._getOptions = function(url) {
      const options = originalOptions.call(this, url);
      const originalProfile = '--user-data-dir=' + this._tempDir;
      if (!profile || options.filter(option => option.startsWith('--user-data-dir=')).length !== 1 ||
          !options.includes(originalProfile)) throw new Error('Exact inherited Chrome profile option changed');
      return options.map(option => option === originalProfile ? '--user-data-dir=' + profile : option);
    };
    const originalStart = this._start;
    this._start = function(url) {
      if (owners.size !== 0 || this._process || profile !== null || !/^http:\/\/localhost:[0-9]+\/\?id=[0-9]+$/.test(url)) {
        throw new Error('Clipboard fixture refuses concurrent/reused/unexpected launch ownership');
      }
      const karmaRoot = this._tempDir;
      const rootStat = fs.lstatSync(karmaRoot);
      if (!rootStat.isDirectory() || rootStat.isSymbolicLink() || fs.readdirSync(karmaRoot).length !== 0) {
        throw new Error('Inherited Karma root is not an ordinary empty disposable directory');
      }
      const directory = fs.mkdtempSync(path.join(karmaRoot, 'nativecmpkit-clipboard-'));
      fs.chmodSync(directory, 0o700);
      const st = fs.lstatSync(directory), rootAfter = fs.lstatSync(karmaRoot);
      if (!st.isDirectory() || st.isSymbolicLink() || (st.mode & 0o777) !== 0o700 ||
          !rootAfter.isDirectory() || rootAfter.isSymbolicLink() ||
          rootAfter.dev !== rootStat.dev || rootAfter.ino !== rootStat.ino) {
        throw new Error('Exclusive owning Chrome profile/root identity changed');
      }
      const activePort = path.join(directory, 'DevToolsActivePort');
      try { fs.lstatSync(activePort); throw new Error('Preexisting DevTools port identity'); }
      catch (error) { if (error.code !== 'ENOENT') throw error; }
      profile = directory; // Exclusive profile belongs to this single new child; inherited Karma cleanup owns the root.
      originalStart.call(this, url);
      const child = this._process;
      if (!child || !Number.isInteger(child.pid) || child.pid < 1) throw new Error('No actual owned Chrome child');
      const owner = { launcher, child, directory, activePort, directoryDev: st.dev, directoryIno: st.ino,
        karmaRoot, rootDev: rootStat.dev, rootIno: rootStat.ino, url, exited: false };
      owners.add(owner);
      child.once('exit', () => { owner.exited = true; owners.delete(owner); });
      // No PID enumeration or attach to an unrelated browser, supplied port or profile.
    };
  }
  OwnedClipboardHeadless.prototype = Object.create(base.prototype);
  OwnedClipboardHeadless.$inject = ['baseBrowserDecorator', 'args', 'config'];
  const aliveOwner = () => {
    if (owners.size !== 1) throw new Error('Exactly one actual owned Chrome process is required');
    const owner = [...owners][0];
    if (owner.exited || owner.launcher._process !== owner.child || owner.child.exitCode !== null ||
        owner.child.signalCode !== null || owner.launcher.state !== owner.launcher.STATE_CAPTURED) {
      throw new Error('The captured owning Chrome process is no longer live');
    }
    const st = fs.lstatSync(owner.directory), rootStat = fs.lstatSync(owner.karmaRoot);
    if (!rootStat.isDirectory() || rootStat.isSymbolicLink() || rootStat.dev !== owner.rootDev || rootStat.ino !== owner.rootIno ||
        !st.isDirectory() || st.isSymbolicLink() || (st.mode & 0o777) !== 0o700 ||
        st.dev !== owner.directoryDev || st.ino !== owner.directoryIno) {
      throw new Error('Owned Karma profile identity changed');
    }
    return owner;
  };
  const devToolsUrl = owner => {
    if (aliveOwner() !== owner) throw new Error('DevTools owner changed');
    const fd = fs.openSync(owner.activePort, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
    try {
      const before = fs.fstatSync(fd);
      if (!before.isFile() || before.size < 3 || before.size > 256) throw new Error('Invalid owned DevTools port file');
      const buffer = Buffer.alloc(before.size + 1);
      const count = fs.readSync(fd, buffer, 0, buffer.length, 0);
      const after = fs.fstatSync(fd), named = fs.lstatSync(owner.activePort);
      if (!named.isFile() || named.isSymbolicLink() || named.dev !== before.dev || named.ino !== before.ino ||
          count !== before.size || before.nlink !== 1 || after.nlink !== 1 ||
          before.dev !== after.dev || before.ino !== after.ino ||
          before.size !== after.size || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs) throw new Error('Unstable owned DevTools port file');
      const match = /^([1-9][0-9]{0,4})\n(\/devtools\/browser\/[0-9a-f-]{36})\n?$/.exec(buffer.subarray(0, count).toString('ascii'));
      if (!match || Number(match[1]) > 65535) throw new Error('Invalid observed DevTools endpoint');
      return 'ws://127.0.0.1:' + match[1] + match[2];
    } finally { fs.closeSync(fd); }
  };

  const connect = async session => {
    if (session.connection) throw new Error('Do not reacquire an existing CDP lease');
    const socket = new WebSocket(devToolsUrl(session.owner), { handshakeTimeout: 5000, maxPayload: 1024 * 1024, perMessageDeflate: false });
    const pending = new Map();
    let serial = 0, closedResolve;
    const closed = new Promise(resolve => { closedResolve = resolve; });
    const connection = { socket, pending, attached: null, closed, closeObserved: false };
    session.connection = connection;
    socket.on('message', data => {
      let message;
      try { message = JSON.parse(String(data)); } catch (_) { socket.terminate(); return; }
      if (!Number.isInteger(message.id)) return; // No events, object handles or console transcripts are retained.
      const waiter = pending.get(message.id);
      if (!waiter) { socket.terminate(); return; }
      pending.delete(message.id);
      if (message.error) waiter.reject(new Error('Owning CDP command was refused'));
      else waiter.resolve(message.result);
    });
    socket.once('close', () => {
      connection.closeObserved = true;
      for (const waiter of pending.values()) waiter.reject(new Error('Owning CDP transport closed'));
      pending.clear(); closedResolve();
    });
    socket.on('error', () => {});
    await bounded(new Promise((resolve, reject) => {
      socket.once('open', resolve); socket.once('error', () => reject(new Error('Owning CDP connection refused')));
    }), 6000);
    connection.command = (method, params, sessionId) => {
      if (aliveOwner() !== session.owner || socket.readyState !== WebSocket.OPEN || pending.size >= 4 ||
          !['Target.getTargets', 'Target.attachToTarget', 'Target.detachFromTarget', 'Runtime.evaluate', 'Input.dispatchMouseEvent'].includes(method)) {
        return Promise.reject(new Error('Unowned/unsupported CDP command'));
      }
      const id = ++serial;
      return bounded(new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
      }), 5000);
    };
    const targets = await connection.command('Target.getTargets', {});
    const target = targets.targetInfos.filter(info => info.type === 'page' && info.url === session.owner.url);
    if (target.length !== 1) throw new Error('Exact owning Karma browser target is missing or ambiguous');
    const attached = await connection.command('Target.attachToTarget', { targetId: target[0].targetId, flatten: true });
    if (!attached || typeof attached.sessionId !== 'string' || !attached.sessionId) throw new Error('Missing owning CDP session identity');
    connection.attached = attached.sessionId;
    return connection;
  };
  const stopConnection = async session => {
    const connection = session.connection;
    if (!connection) return;
    let primary;
    try {
      if (connection.attached && connection.socket.readyState === WebSocket.OPEN) {
        await connection.command('Target.detachFromTarget', { sessionId: connection.attached });
        connection.attached = null;
      }
    } catch (error) { primary = error; }
    finally {
      connection.socket.close();
      try { await bounded(connection.closed, 2000); }
      catch (error) { connection.socket.terminate(); await bounded(connection.closed, 2000); if (!primary) primary = error; }
    }
    if (!connection.closeObserved || connection.pending.size !== 0 || connection.socket.readyState !== WebSocket.CLOSED) {
      throw new Error('Actual owning CDP transport did not close');
    }
    session.connection = null;
    if (primary) throw primary;
  };

  function inspectNativeButton(childId, expectedUrl) {
    const context = document.getElementById('context');
    if (!context || !context.contentDocument || context.contentWindow.location.origin !== location.origin) throw new Error('No owning Karma context');
    const child = context.contentDocument.getElementById(childId);
    if (!child || child.tagName !== 'IFRAME' || child.src !== expectedUrl || !child.contentDocument) throw new Error('No exact owning clipboard child');
    const button = child.contentDocument.getElementById('nativecmpkit-clipboard-action');
    if (!button || button.disabled || button.tagName !== 'BUTTON') throw new Error('No exact native action button');
    const a = context.getBoundingClientRect(), b = child.getBoundingClientRect(), c = button.getBoundingClientRect();
    const localX = c.left + c.width / 2, localY = c.top + c.height / 2;
    const contextX = b.left + localX, contextY = b.top + localY;
    const x = a.left + contextX, y = a.top + contextY;
    if (a.width <= 0 || a.height <= 0 || b.width <= 0 || b.height <= 0 || c.width <= 0 || c.height <= 0 ||
        x <= 0 || y <= 0 || x >= innerWidth || y >= innerHeight ||
        document.elementFromPoint(x, y) !== context ||
        context.contentDocument.elementFromPoint(contextX, contextY) !== child ||
        child.contentDocument.elementFromPoint(localX, localY) !== button) throw new Error('Actual native hit-test refused');
    return { x, y, childUrl: child.src, topUrl: location.href };
  }
  const click = session => {
    if (!['denied', 'gesture'].includes(session.mode) || session.closing || session.clickStarted ||
        session.clicked || session.childServed !== 1) throw new Error('No exact pending native gesture');
    session.clickStarted = true; // Reserve once before the first asynchronous owning operation.
    session.clickOperation = (async () => {
    const connection = await connect(session);
    // Fixed read-only DOM inspection of this child/button; no Runtime.evaluate userGesture flag.
    const expression = '(' + inspectNativeButton.toString() + ')(' +
      JSON.stringify('nativecmpkit-clipboard-child-' + session.token) + ',' + JSON.stringify(session.childUrl) + ')';
    const result = await connection.command('Runtime.evaluate', {
      expression, returnByValue: true, awaitPromise: false, includeCommandLineAPI: false
    }, connection.attached);
    if (result.exceptionDetails || !result.result || result.result.type !== 'object') throw new Error('Owning native DOM measurement failed');
    const point = result.result.value;
    if (!point || point.childUrl !== session.childUrl || point.topUrl !== session.owner.url ||
        !Number.isFinite(point.x) || !Number.isFinite(point.y) || point.x <= 0 || point.y <= 0) throw new Error('Unqualified native mouse coordinates');
    await connection.command('Input.dispatchMouseEvent', { type: 'mouseMoved', x: point.x, y: point.y }, connection.attached);
    let releaseNeeded = true, primary;
    try {
      await connection.command('Input.dispatchMouseEvent', { type: 'mousePressed', button: 'left', buttons: 1, clickCount: 1, x: point.x, y: point.y }, connection.attached);
      await connection.command('Input.dispatchMouseEvent', { type: 'mouseReleased', button: 'left', buttons: 0, clickCount: 1, x: point.x, y: point.y }, connection.attached);
      releaseNeeded = false;
      session.clicked = true;
      session.completedClicks++;
    } catch (error) { primary = error; throw error; }
    finally {
      // A refused/partially acknowledged original input still releases only this owned button.
      if (releaseNeeded) {
        try {
          await connection.command('Input.dispatchMouseEvent', {
            type: 'mouseReleased', button: 'left', buttons: 0, clickCount: 1, x: point.x, y: point.y
          }, connection.attached);
        } catch (cleanup) {
          session.inputReleaseFailed = true;
          if (!primary) throw cleanup;
        }
      }
    }
    })();
    return session.clickOperation;
  };

  const jsValue = value => JSON.stringify(value).replace(/</g, '\\u003c');
  function childBootstrap(token, mode, method, parentOrigin, klass) {
    const identity = token + '|' + mode + '|' + method;
    const h = { token, mode, method, calls: 0, resolved: 0, rejected: 0, unhandled: 0,
      errorName: '', errorType: '', cleaned: false, armed: false };
    window.__nativecmpkitClipboardNative = h;
    const unhandled = () => { h.unhandled++; }; // Observe, never prevent/suppress a rejection event.
    window.addEventListener('unhandledrejection', unhandled);
    const savedApi = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
    let masked = false, clipboard, savedWrite, nativeWrite, wrapper;
    h.maskApi = () => {
      if (mode !== 'missing' || masked || clipboard || window.isSecureContext !== true ||
          !navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') throw new Error('Wrong capability-absence owner');
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
      masked = true;
    };
    h.observeNativeWrites = () => {
      if (!['denied', 'gesture'].includes(mode) || clipboard || masked || window.isSecureContext !== true) throw new Error('Wrong native clipboard observer owner');
      clipboard = navigator.clipboard;
      nativeWrite = clipboard && clipboard.writeText;
      if (typeof nativeWrite !== 'function') throw new Error('No actual native writeText');
      savedWrite = Object.getOwnPropertyDescriptor(clipboard, 'writeText');
      wrapper = function(text) {
        if (this !== clipboard || text !== 'NativeCmpKit clipboard ' + token || h.calls !== 0) throw new Error('Wrong owned native write invocation');
        h.calls++;
        const promise = Reflect.apply(nativeWrite, clipboard, [text]);
        if (!(promise instanceof Promise)) throw new Error('Native writeText did not return a real Promise');
        promise.then(() => { h.resolved++; }, error => {
          h.rejected++;
          h.errorType = error instanceof DOMException ? 'DOMException' : 'non-DOMException';
          h.errorName = error && error.name || '';
        });
        return promise; // EXACT native Promise, no substituted permission, settlement or outcome.
      };
      Object.defineProperty(clipboard, 'writeText', { configurable: true, value: wrapper });
    };
    h.arm = () => {
      if (!['denied', 'gesture'].includes(mode) || h.armed || !clipboard || h.calls !== 0) throw new Error('Wrong pending native gesture owner');
      h.armed = true;
      parent.postMessage('armed|' + identity, parentOrigin);
    };
    h.restore = () => {
      if (h.cleaned) return false;
      if (clipboard) {
        const current = Object.getOwnPropertyDescriptor(clipboard, 'writeText');
        if (!current || current.value !== wrapper) throw new Error('Native observer identity changed');
        if (savedWrite) Object.defineProperty(clipboard, 'writeText', savedWrite);
        else delete clipboard.writeText;
        if (clipboard.writeText !== nativeWrite) throw new Error('Native write descriptor restoration failed');
      }
      if (masked) {
        const current = Object.getOwnPropertyDescriptor(navigator, 'clipboard');
        if (!current || current.value !== undefined) throw new Error('Capability absence owner changed');
        if (savedApi) Object.defineProperty(navigator, 'clipboard', savedApi);
        else delete navigator.clipboard;
      }
      window.removeEventListener('unhandledrejection', unhandled);
      h.cleaned = true;
      return true;
    };
    const stack = [];
    let selected, selections = 0, invocations = 0;
    window.kotlinTest = { adapterTransformer: () => ({
      suite(name, ignored, body) {
        stack.push(name);
        const fqn = stack.join('.');
        try { if (!ignored && (klass === fqn || klass.startsWith(fqn + '.'))) body(); }
        finally { stack.pop(); }
      },
      test(name, ignored, body) {
        if (stack.join('.') === klass && name === method) {
          if (ignored || selected) throw new Error('Ignored/duplicate native clipboard declaration');
          selected = body; selections++;
        }
        // No callback for any accepted test is ever invoked here.
      }
    }) };
    const sendFailure = error => {
      const name = String(error && error.name || 'fixture').replace(/[^A-Za-z0-9._-]/g, '?').slice(0, 40);
      const message = String(error && error.message || 'fixture-failure').replace(/[^A-Za-z0-9 .():=-]/g, '?').slice(0, 160);
      // Bounded public assertion category/message only, never stack/console/native clipboard content.
      parent.postMessage('failed|' + identity + '|' + name + ':' + message, parentOrigin);
    };
    window.__nativecmpkitClipboardBoot = async () => {
      try {
        if (typeof selected !== 'function' || selections !== 1 || invocations !== 0) throw new Error('Exact emitted native test method is missing/reused');
        parent.postMessage('ready|' + identity, parentOrigin);
        invocations++;
        await selected(); // Real compiled library-level method in THIS actual browser realm.
        if (!h.cleaned || h.unhandled !== 0) throw new Error('Native child cleanup/result boundary failed');
        parent.postMessage('done|' + identity + '|passed|' + h.unhandled + '|' + invocations, parentOrigin);
      } catch (error) { sendFailure(error); }
    };
    window.__nativecmpkitClipboardLoadFailure = sendFailure;
  }

  const isWasmPackage = basePath => typeof basePath === 'string' && path.isAbsolute(basePath) &&
    path.normalize(basePath) === basePath && /^(NativeCmpKit|nativeCmpkit)-calf-share-test$/.test(path.basename(basePath)) &&
    path.basename(path.dirname(basePath)) === 'packages' && path.basename(path.dirname(path.dirname(basePath))) === 'wasm' &&
    path.basename(path.dirname(path.dirname(path.dirname(basePath)))) === 'build';
  const scriptUrls = async (filesPromise, basePath) => {
    const files = await filesPromise;
    if (isWasmPackage(basePath)) {
      // KGP2.4.20 includes static/load.mjs, not its imported test .mjs. karma-webpack5 keeps
      // originalPath but serves the deterministic load.<entry-key>.js classic-script wrapper.
      const refused = () => { throw new Error('Exact emitted Wasm Karma loader inputs are missing'); };
      if (!files || !Array.isArray(files.included) || !Array.isArray(files.served)) refused();
      const loadPath = path.join(basePath, 'static', 'load.mjs');
      const chosen = files.included.filter(file => {
        if (!file || typeof file.originalPath !== 'string' || file.originalPath.includes('\0')) refused();
        const original = path.basename(file.originalPath);
        return ['runtime.js', 'commons.js', 'load.mjs'].includes(original) || /-calf-share-test\.m?js$/.test(original);
      });
      if (chosen.length !== 3 || path.basename(chosen[0].originalPath) !== 'runtime.js' ||
          path.basename(chosen[1].originalPath) !== 'commons.js' || chosen[2].originalPath !== loadPath ||
          path.dirname(chosen[0].originalPath) !== path.dirname(chosen[1].originalPath) ||
          !path.isAbsolute(chosen[0].originalPath) || path.normalize(chosen[0].originalPath) !== chosen[0].originalPath ||
          !path.isAbsolute(chosen[1].originalPath) || path.normalize(chosen[1].originalPath) !== chosen[1].originalPath) refused();
      const entryPath = 'load.' + require('karma-webpack/lib/utils/hash').hash(loadPath) + '.js';
      if (chosen.some(file => file.isUrl || typeof file.path !== 'string' || file.path.includes('\0') ||
          typeof file.sha !== 'string' || !/^[a-f0-9]{40}$/.test(file.sha) ||
          ![undefined, 'js'].includes(file.type) ||
          !files.served.some(served => served.originalPath === file.originalPath && served.path === file.path && served.sha === file.sha)) ||
          chosen[0].path !== chosen[0].originalPath || chosen[1].path !== chosen[1].originalPath ||
          chosen[2].path !== entryPath) refused();
      return chosen.map((file, index) => ({
        url: (file.path.startsWith(basePath) ? '/base' + file.path.slice(basePath.length) : '/absolute' + file.path) + '?' + file.sha,
        type: 'text/javascript', ...(index === 2 ? { wasmLoader: true } : {})
      }));
    }
    // Accepted JS selection/order/URLs/types remain byte-for-byte below; no Wasm fallback.
    const chosen = files.included.filter(file => {
      const original = path.basename(file.originalPath || file.path);
      return ['runtime.js', 'commons.js'].includes(original) || /^(NativeCmpKit|nativeCmpkit)-calf-share-test\.m?js$/.test(original);
    });
    if (chosen.length !== 3 || chosen.filter(file => /-calf-share-test\.m?js$/.test(path.basename(file.originalPath || file.path))).length !== 1 ||
        !chosen.some(file => path.basename(file.originalPath || file.path) === 'runtime.js') ||
        !chosen.some(file => path.basename(file.originalPath || file.path) === 'commons.js') ||
        chosen.some(file => file.isUrl || typeof file.path !== 'string' || file.path.includes('\0'))) throw new Error('Exact emitted Karma bundle inputs are missing');
    return chosen.map(file => ({
      url: (file.path.startsWith(basePath) ? '/base' + file.path.slice(basePath.length) : '/absolute' + file.path) + '?' + file.sha,
      type: file.type === 'module' ? 'module' : 'text/javascript'
    }));
  };
  function childLoad(scripts) {
    (async () => {
      try {
        for (const entry of scripts) {
          await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.type = entry.type; script.src = entry.url;
            script.onload = resolve; script.onerror = () => reject(new Error('Owning emitted bundle failed to load'));
            document.head.appendChild(script);
          });
        }
        await window.__nativecmpkitClipboardBoot();
      } catch (error) { window.__nativecmpkitClipboardLoadFailure(error); }
    })();
  }
  function wasmChildBootstrap() {
    try {
      // Only the exact KGP Wasm loader entry receives these disposable child-realm hooks.
      // The accepted JS bootstrap, load function and emitted HTML recipe are untouched.
      const h = window.__nativecmpkitClipboardNative;
      const restore = h && h.restore, boot = window.__nativecmpkitClipboardBoot;
      if (!h || h.cleaned || typeof restore !== 'function' || typeof boot !== 'function' || '__karma__' in window) {
        throw new Error('Owning Wasm loader hooks are missing/preexisting');
      }
      let loaded = 0, failed = false, release;
      // Resolve the fixture's own wait on error, then refuse; never suppress a native clipboard rejection.
      const ready = new Promise(resolve => { release = resolve; });
      const karma = Object.freeze({
        loaded() { if (++loaded !== 1) failed = true; release(); },
        error() { failed = true; release(); } // Fixed refusal only, no loader error body/stack/paths.
      });
      const assertReady = () => {
        if (failed || loaded !== 1 || window.__karma__ !== karma || window.__nativecmpkitClipboardNative !== h) {
          throw new Error('Exact emitted Wasm test registration failed/reused');
        }
      };
      const ownedBoot = async () => {
        await ready; // script.onload precedes webpack's asynchronous Wasm registration.
        assertReady();
        await boot(); // Unchanged exact-selection/one-invocation/native-cleanup/result boundary.
      };
      const ownedRestore = () => {
        if (h.cleaned) return false;
        assertReady();
        if (h.restore !== ownedRestore || window.__nativecmpkitClipboardBoot !== ownedBoot) {
          throw new Error('Owning Wasm loader cleanup identity changed');
        }
        if (restore() !== true || h.cleaned !== true) throw new Error('Owning Wasm native restoration failed');
        delete window.__karma__;
        if ('__karma__' in window) throw new Error('Owning Wasm loader hook removal failed');
        window.__nativecmpkitClipboardBoot = boot;
        h.restore = restore;
        return true;
      };
      window.__karma__ = karma;
      window.__nativecmpkitClipboardBoot = ownedBoot;
      h.restore = ownedRestore;
    } catch (_) {
      // A refused/partial setup can never fall through to the unguarded native method.
      window.__nativecmpkitClipboardBoot = async () => { throw new Error('Owning Wasm loader setup refused'); };
      window.__nativecmpkitClipboardLoadFailure(new Error('Owning Wasm loader setup refused'));
    }
  }
  const reply = (response, origin, message, status = 200) => {
    response.writeHead(status, { 'Cache-Control': 'no-store', 'Content-Type': 'text/html; charset=utf-8' });
    response.end('<!doctype html><script>parent.postMessage(' + jsValue(message) + ', ' + jsValue(origin) + ')</script>');
  };
  const close = session => {
    if (session.closeOperation) return session.closeOperation;
    session.closing = true; // No further child/input operation may enter during cleanup.
    cancel(session.lifetime);
    session.closeOperation = (async () => {
      let primary;
      if (session.clickOperation) {
        try { await session.clickOperation; } catch (error) { primary = error; }
      }
      await stopConnection(session); // Also releases a partially acquired connection.
      if (sessions.get(session.token) !== session) throw new Error('Owned clipboard session changed');
      sessions.delete(session.token);
      if (primary) throw primary; // Cleanup never turns an original refused native operation green.
    })();
    return session.closeOperation;
  };
  const middleware = (emitter, filesPromise, basePath) => {
    let shuttingDown = false;
    emitter.on('exit', done => {
      shuttingDown = true;
      Promise.all([...sessions.values()].map(close)).then(() => {
        if (sessions.size || timers.size) done(1); else done(0);
      }, () => done(1));
    });
    return (request, response, next) => {
      const url = new URL(request.url, 'http://localhost');
      if (!url.pathname.startsWith(prefix)) return next();
      const action = url.pathname.slice(prefix.length), token = url.searchParams.get('token');
      const port = request.socket.localPort, controlOrigin = 'http://localhost:' + port;
      if (request.method !== 'GET' || shuttingDown || !/^[a-z0-9]{30}$/.test(token || '') ||
          !['open', 'child', 'click', 'close'].includes(action) ||
          !['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(request.socket.remoteAddress)) {
        reply(response, controlOrigin, 'invalid-clipboard-control', 400); return;
      }
      let phase = 'control'; // Fixed Wasm-only phase observation, not an exception body or diagnosed cause.
      (async () => {
        if (action === 'open') {
          const mode = url.searchParams.get('mode'), method = url.searchParams.get('method');
          if (request.headers.host !== 'localhost:' + port || request.headers['sec-fetch-site'] !== 'same-origin' ||
              url.searchParams.size !== 3 || !Object.hasOwn(methods, mode) || methods[mode] !== method || sessions.size !== 0) {
            reply(response, controlOrigin, 'clipboard-open-refused', 409); return;
          }
          phase = 'open-owner';
          const owner = aliveOwner();
          phase = 'open-origin';
          if (new URL(owner.url).origin !== controlOrigin) throw new Error('Owning browser/control origin mismatch');
          const session = { token, mode, method, owner, controlOrigin, port, clicked: false, completedClicks: 0,
            clickStarted: false, clickOperation: null, closeOperation: null, closing: false, childServed: 0,
            connection: null, childUrl: (mode === 'insecure' ? 'http://' + insecureHost + ':' + port : controlOrigin) + prefix + 'child?token=' + token };
          sessions.set(token, session); // Reserve the exact owner before awaiting emitted script inputs.
          session.lifetime = later(60000, () => { close(session).catch(() => { session.failed = true; }); });
          try {
            phase = 'open-scripts';
            session.scripts = await bounded(scriptUrls(filesPromise, basePath), 5000);
            phase = 'open-readback';
            if (sessions.get(token) !== session || session.closing) throw new Error('Opening clipboard owner expired/changed');
            phase = 'open-devtools';
            devToolsUrl(owner); // Only this actually spawned profile's port file, never a guessed port.
          } catch (error) {
            try { await close(session); } catch (_) { session.failed = true; }
            throw error;
          }
          reply(response, controlOrigin, 'opened|' + token + '|' + mode + '|' + method); return;
        }
        const session = sessions.get(token);
        if (!session || session.port !== port || url.searchParams.size !== 1 || (session.failed && action !== 'close') ||
            (session.closing && action !== 'close')) {
          reply(response, controlOrigin, 'clipboard-owner-refused', 409); return;
        }
        const expectedHost = action === 'child' && session.mode === 'insecure' ? insecureHost : 'localhost';
        if (request.headers.host !== expectedHost + ':' + port) throw new Error('Unexpected actual child/control origin');
        if (action === 'child') {
          if (++session.childServed !== 1) throw new Error('No reload/duplicate native child execution');
          const headers = { 'Cache-Control': 'no-store', 'Content-Type': 'text/html; charset=utf-8' };
          if (session.mode === 'denied') headers['Permissions-Policy'] = 'clipboard-read=(), clipboard-write=()';
          response.writeHead(200, headers);
          const boot = '(' + childBootstrap.toString() + ')(' +
            [token, session.mode, session.method, controlOrigin, klass].map(jsValue).join(',') + ');';
          const wasmBoot = session.scripts.some(entry => entry.wasmLoader === true) ?
            '<script>(' + wasmChildBootstrap.toString() + ')();</script>' : '';
          const load = '(' + childLoad.toString() + ')(' + jsValue(session.scripts) + ');';
          response.end('<!doctype html><meta charset="utf-8"><style>html,body{margin:0}#nativecmpkit-clipboard-action{position:fixed;left:24px;top:24px;width:250px;height:64px}</style>' +
            '<button id="nativecmpkit-clipboard-action">NativeCmpKit owned clipboard action</button><script>' + boot + '</script>' + wasmBoot + '<script>' + load + '</script>');
          return;
        }
        if (request.headers['sec-fetch-site'] !== 'same-origin') throw new Error('Control must come from the exact same-origin owner');
        if (action === 'click') {
          await click(session);
          reply(response, controlOrigin, 'clicked|' + token + '|' + session.completedClicks); return;
        }
        await close(session);
        reply(response, controlOrigin, 'closed|' + token + '|' +
          (sessions.get(token) === session ? '1' : '0') + '|' + (session.connection ? '1' : '0'));
      })().catch(() => reply(response, controlOrigin, 'owned-clipboard-fixture-failed' +
        (isWasmPackage(basePath) ? '|' + phase : ''), 503));
    };
  };
  middleware.$inject = ['emitter', 'filesPromise', 'config.basePath'];
  config.plugins = config.plugins || [];
  config.plugins.push({ 'launcher:OwnedClipboardHeadless': ['type', OwnedClipboardHeadless],
    'middleware:nativecmpkit-clipboard-fixture': ['factory', middleware] });
  config.beforeMiddleware = [...(config.beforeMiddleware || []), 'nativecmpkit-clipboard-fixture'];
  // parseConfig uses explicit null sentinels here; undefined/foreign values are never defaults.
  if ((config.hostname !== null && config.hostname !== 'localhost') ||
      (config.listenAddress !== null && config.listenAddress !== '127.0.0.1') ||
      config.protocol !== 'http:' || config.urlRoot !== '/' || !Array.isArray(config.browsers) ||
      config.browsers.length !== 1 || config.browsers[0] !== 'ChromeHeadless') {
    throw new Error('Native clipboard fixture requires the literal owned localhost Karma/Chrome profile');
  }
  config.hostname = 'localhost';
  config.browsers = ['OwnedClipboardHeadless'];
  config.listenAddress = '127.0.0.1';
})();
