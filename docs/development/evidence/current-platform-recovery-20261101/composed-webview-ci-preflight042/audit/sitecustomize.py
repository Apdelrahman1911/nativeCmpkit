import os, pathlib, sys
BASE = pathlib.Path(os.environ['NATIVECMPKIT_PREFLIGHT_PRIVATE']).resolve()
ROOT = pathlib.Path(os.environ['NATIVECMPKIT_PREFLIGHT_ROOT']).resolve()
ALLOWED_FOCUSES = {'android-webview-request-state', 'webview-ios-native-request-state', 'tls-rendering', 'tls-rendering-cookies-policy', 'tls-rendering-cookies-policy-media'}
EVENTS = []
def owned(path, dir_fd=None):
    if isinstance(path, int):
        return
    path = pathlib.Path(os.fsdecode(path))
    if not path.is_absolute():
        anchor = pathlib.Path(os.readlink('/proc/self/fd/' + str(dir_fd))) if dir_fd not in (None, -1) else pathlib.Path.cwd()
        path = anchor / path
    candidate = path.absolute()
    # Checking the resolved parent also permits removal of a private test-owned
    # symlink without following that symlink's synthetic target.
    if not (candidate == BASE or BASE in candidate.resolve().parents):
        raise PermissionError('Preflight refuses a write outside its private directory')
def audit(event, args):
    if event == 'open':
        path, mode, flags = args
        if (mode is not None and any(c in mode for c in 'wax+')) or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            owned(path)
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir'):
        owned(args[0], args[-1] if len(args)>1 else None)
    elif event in ('os.rename', 'os.link'):
        owned(args[0], args[2] if len(args)>2 else None); owned(args[1], args[3] if len(args)>3 else None)
    elif event == 'os.symlink':
        owned(args[1], args[2] if len(args)>2 else None)
    elif event in ('os.chmod', 'os.chown', 'os.utime'):
        owned(args[0], args[-1] if len(args)>2 and isinstance(args[-1], int) else None)
    elif event == 'subprocess.Popen':
        executable, argv, cwd, env = args
        command = list(argv) if isinstance(argv, (list,tuple)) else []
        if len(command)<6 or pathlib.Path(command[0]).resolve()!=pathlib.Path(sys.executable).resolve() or command[1]!='-B' or command[3]!='plan':
            raise PermissionError('Preflight permits only exact Python source-plan children')
        script=pathlib.Path(command[2]).resolve()
        if script not in (ROOT/'scripts/ci/library_tests.py', ROOT/'scripts/ci/android_device_tests.py') or '--focus' not in command or command[command.index('--focus')+1] not in ALLOWED_FOCUSES:
            raise PermissionError('Preflight refuses an unselected source-plan child')
        if cwd is not None and pathlib.Path(cwd).resolve()!=ROOT:
            raise PermissionError('Preflight refuses a foreign source-plan checkout')
        if env is not None and (env.get('PYTHONPATH')!=os.environ.get('PYTHONPATH') or env.get('NATIVECMPKIT_PREFLIGHT_PRIVATE')!=str(BASE)):
            raise PermissionError('Preflight refuses a child without the inherited audit gate')
        EVENTS.append({'operation':'source-plan', 'script':script.name,'focus':command[command.index('--focus')+1]})
    elif event.startswith('socket.') or event in ('os.system', 'os.exec', 'os.spawn'):
        raise PermissionError('Preflight refuses network or non-plan process work')
sys.addaudithook(audit)
