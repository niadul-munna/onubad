import tempfile
import threading
import unittest
from pathlib import Path

from translate_tool import ipc


class IpcTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "t.sock")

    def tearDown(self):
        self.tmp.cleanup()

    def test_send_returns_false_when_no_server(self):
        self.assertFalse(ipc.try_connect_and_send("open", self.path))

    def test_server_receives_sent_action(self):
        got = []
        received = threading.Event()

        def handler(action):
            got.append(action)
            received.set()

        server = ipc.serve(handler, self.path)
        try:
            self.assertTrue(ipc.try_connect_and_send("clipboard", self.path))
            self.assertTrue(received.wait(2), "handler not called")
            self.assertEqual(got, ["clipboard"])
        finally:
            server.close()

    def test_send_returns_false_after_server_closed(self):
        server = ipc.serve(lambda a: None, self.path)
        server.close()
        self.assertFalse(ipc.try_connect_and_send("open", self.path))


if __name__ == "__main__":
    unittest.main()
