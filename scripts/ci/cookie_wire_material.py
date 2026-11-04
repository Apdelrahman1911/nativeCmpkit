#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Ephemeral test-only cookie TLS material; never changes DNS/system/simulator trust.

Creation is a lead-owned RUNTIME action, not a source/model test. Every private key,
CSR/config and certificate stays in one uncommitted owner-only temporary directory.
Only CA/leaf hashes may be exported; the generated private bytes must not be archived.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile


TOKEN = re.compile(r"[0-9a-f]{32}\Z")
FILES = ("ca.key", "ca.pem", "server.key", "server.csr", "server.pem", "leaf.ext")


def leaf_extensions(token: str) -> str:
    if not TOKEN.fullmatch(token):
        raise ValueError("Missing fresh owned cookie TLS nonce")
    host = f"r{token}.nativecmpkit.test"
    return ("basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n"
            f"extendedKeyUsage=serverAuth\nsubjectAltName=DNS:{host},DNS:sub.{host}\n")


def certificate_commands(token: str, directory: Path, openssl: Path) -> tuple[tuple[str, ...], ...]:
    """Pure fixed command plan: no shell, network, key/certificate creation or trust changes."""
    if not TOKEN.fullmatch(token) or not directory.is_absolute() or not openssl.is_absolute():
        raise ValueError("Missing exact owned certificate command inputs")
    host = f"r{token}.nativecmpkit.test"
    own = lambda name: str(directory / name)
    return (
        (str(openssl), "req", "-x509", "-newkey", "rsa:3072", "-nodes", "-sha256", "-days", "2",
         "-subj", "/CN=NativeCmpKit disposable cookie fixture root", "-keyout", own("ca.key"), "-out", own("ca.pem"),
         "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign"),
        (str(openssl), "req", "-new", "-newkey", "rsa:2048", "-nodes", "-sha256", "-subj", f"/CN={host}",
         "-keyout", own("server.key"), "-out", own("server.csr")),
        (str(openssl), "x509", "-req", "-in", own("server.csr"), "-CA", own("ca.pem"), "-CAkey", own("ca.key"),
         "-set_serial", f"0x{token}", "-days", "2", "-sha256", "-extfile", own("leaf.ext"), "-out", own("server.pem")),
        (str(openssl), "verify", "-CAfile", own("ca.pem"), "-purpose", "sslserver", "-verify_hostname", host, own("server.pem")),
        (str(openssl), "verify", "-CAfile", own("ca.pem"), "-purpose", "sslserver", "-verify_hostname", f"sub.{host}", own("server.pem")),
    )


class OwnedCookieTlsMaterial:
    """Independent exact-file cleanup preserves both primary failure and foreign replacements."""
    def __init__(self, token: str, directory: Path):
        self.token, self.directory = token, directory
        self._closed = False
        self._failure: BaseException | None = None
        self._identities: dict[Path, tuple[int, int]] = {}
        self._directory_identity = (directory.stat().st_dev, directory.stat().st_ino)

    @property
    def certificate(self) -> Path: return self.directory / "server.pem"
    @property
    def private_key(self) -> Path: return self.directory / "server.key"
    @property
    def trust_anchor(self) -> Path: return self.directory / "ca.pem"

    @classmethod
    def create(cls, *, token: str, openssl: Path) -> "OwnedCookieTlsMaterial":
        if not TOKEN.fullmatch(token) or not openssl.is_absolute() or openssl.is_symlink() or not openssl.is_file():
            raise ValueError("Missing actual regular owning OpenSSL executable")
        if os.name != "posix":
            raise RuntimeError("Cookie material needs a separately verified owner-only private-directory ACL lease on this platform")
        directory = Path(tempfile.mkdtemp(prefix=f"nativecmpkit-cookie-wire-{token}-")).absolute()
        material = cls(token, directory)
        try:
            if os.name == "posix": os.chmod(directory, 0o700)
            for name in FILES:
                path = directory / name
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.close(descriptor)
                info = path.stat(); material._identities[path] = (info.st_dev, info.st_ino)
            (directory / "leaf.ext").write_text(leaf_extensions(token), encoding="ascii")
            for command in certificate_commands(token, directory, openssl):
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                primary: BaseException | None = None
                try:
                    if process.wait(timeout=45) != 0:
                        raise RuntimeError("Owned cookie certificate command returned nonzero")
                except BaseException as error:
                    primary = error
                    raise
                finally:
                    try:
                        if process.poll() is None:
                            process.kill(); process.wait(timeout=5)
                    except BaseException as cleanup:
                        if primary is None: raise
                        primary.add_note(f"Owned certificate process cleanup failed: {type(cleanup).__name__}")
            for path in material._identities:
                if path.is_symlink() or not path.is_file():
                    raise RuntimeError("Owned certificate generator replaced a regular input unexpectedly")
                info = path.stat()
                if (info.st_dev, info.st_ino) != material._identities[path]:
                    raise RuntimeError("Owned certificate input identity changed during generation")
                if os.name == "posix": os.chmod(path, 0o600)
            return material
        except BaseException as primary:
            try: material.close()
            except BaseException as cleanup: primary.add_note(f"Independent certificate file cleanup failed: {type(cleanup).__name__}")
            raise

    def close(self) -> None:
        if self._closed:
            if self._failure is not None: raise RuntimeError("Owned cookie material retained its original cleanup failure") from self._failure
            return
        self._closed = True
        failures: list[BaseException] = []
        for path, identity in self._identities.items():
            try:
                if path.exists() or path.is_symlink():
                    info = path.lstat()
                    if path.is_symlink() or (info.st_dev, info.st_ino) != identity:
                        raise RuntimeError("Preserve a foreign replacement certificate file; refuse deletion")
                    path.unlink()
            except BaseException as error: failures.append(error)
        try:
            info = self.directory.lstat()
            if self.directory.is_symlink() or (info.st_dev, info.st_ino) != self._directory_identity:
                raise RuntimeError("Preserve a foreign replacement certificate directory; refuse deletion")
            self.directory.rmdir() # Never recurse or delete an unexpected foreign residual.
        except BaseException as error: failures.append(error)
        if failures:
            self._failure = failures[0]
            failure = RuntimeError("Independent owned cookie material cleanup failed")
            for error in failures: failure.add_note(type(error).__name__)
            raise failure from failures[0]
