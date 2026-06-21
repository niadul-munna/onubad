"""Single-instance IPC over a unix socket.

The running tray app runs a server; CLI invocations (--open / --clipboard)
act as clients that hand the action to the already-running instance.
"""

import os
import socket
import threading


def socket_path():
    base = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(base, "onubad.sock")


def try_connect_and_send(action, path=None):
    """Send `action` to a running server. True if delivered, False if none."""
    path = path or socket_path()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as c:
            c.settimeout(1.0)
            c.connect(path)
            c.sendall(action.encode("utf-8"))
        return True
    except OSError:
        return False


class Server:
    def __init__(self, handler, path):
        self.handler = handler
        self.path = path
        self._running = True
        try:
            os.unlink(path)  # clear stale socket
        except FileNotFoundError:
            pass
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        self.sock.listen(5)
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self._running:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                break
            with conn:
                try:
                    data = conn.recv(1024)
                except OSError:
                    continue
                if data:
                    try:
                        self.handler(data.decode("utf-8").strip())
                    except Exception:  # never let a handler kill the loop
                        pass

    def close(self):
        self._running = False
        try:
            self.sock.close()
        except OSError:
            pass
        try:
            os.unlink(self.path)
        except FileNotFoundError:
            pass


def serve(handler, path=None):
    """Start a background server; returns a Server with .close()."""
    return Server(handler, path or socket_path())
