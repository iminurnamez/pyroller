"""Tests for the buttons
"""

import pygame
from mock import Mock, MagicMock
import unittest


# Make the tests work from the test directory
import sys
sys.path.append('..')
try:
    from data.components import labels
except ImportError:
    print('\n** ERROR ** Tests must be run from the test directory\n\n')
    sys.exit(1)


class TestUI(unittest.TestCase):

    def test_new_from_rect_like(self):
        b = labels.Button((0, 0, 100, 100))

    def test_new_from_rect(self):
        rect = pygame.Rect(0, 0, 100, 100)
        b = labels.Button(rect)

    def test_draw(self):
        m = Mock()
        b = labels.Button((0, 0, 100, 100))
        b.draw(m)
        m.assert_called_once_with(b.image, b.rect)


if __name__ == '__main__':
    unittest.main()
