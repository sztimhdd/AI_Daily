import unittest
from scripts.test import offline_guard


class TestRunnerSafetyTests(unittest.TestCase):
    def test_network_is_blocked_including_local_cdp(self):
        with self.assertRaises(RuntimeError):
            offline_guard('socket.connect', (None, ('127.0.0.1', 9222)))

    def test_external_commands_are_blocked_before_launch(self):
        with self.assertRaises(RuntimeError):
            offline_guard('subprocess.Popen', ('python', ['python', 'fetch_walled.py']))

    def test_file_access_is_allowed(self):
        offline_guard('open', ('fixture.json', 'r', 0))
