#!/usr/bin/env python3
"""Small offline regression entry point; never attach to a personal browser."""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]


def offline_guard(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system', 'os.posix_spawn'):
        raise RuntimeError('Offline tests prohibit network and external commands; inject a fixture')


def main():
    sys.addaudithook(offline_guard)
    names = sys.argv[1:] or [
        'tests.test_vertex_route', 'tests.test_delivery_en',
        'tests.test_visuals', 'tests.test_test_runner',
    ]
    suite = (unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
             if names == ['--full'] else unittest.defaultTestLoader.loadTestsFromNames(names))
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
