"""Tests for the main control class"""

import unittest


# Make the tests work from the test directory
import sys
sys.path.append('..')
try:
    from data.states.baccarat import ui
except ImportError:
    print('\n** ERROR ** Tests must be run from the test directory\n\n')
    sys.exit(1)


class TestUI(unittest.TestCase):
    def test_make_change_sum(self):
        for i in range(0, 1000):
            change = ui.make_change(i)
            self.assertEqual(sum(change), i)

    def test_make_change_sum_break(self):
        for i in range(0, 1000):
            change = ui.make_change(i, True)
            self.assertEqual(sum(change), i)


if __name__ == '__main__':
    unittest.main()
