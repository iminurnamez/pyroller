"""Tests for the main control class"""

import unittest
import time


# Default test settings
RESOLUTION = (10, 20)
RESOLUTIONS = [
    RESOLUTION,
    (30, 40),
    (50, 60),
    (70, 80),
]

# Set up the pygame system
import pygame as pg
pg.init()
pg.display.set_mode(RESOLUTION)


# Make the tests work from the test directory
import sys
sys.path.append('..')
try:
    from data import tools
except ImportError:
    print('\n** ERROR ** Tests must be run from the test directory\n\n')
    sys.exit(1)


class TestControl(unittest.TestCase):
    """Tests for the Control"""

    def setUp(self):
        """Set up the tests"""
        #
        # Simple control to use for testing
        self.c = self._getControl()
        #
        # Some simple states
        self.states = {
            'one': SimpleState('one'),
            'two': SimpleState('two'),
            'three': SimpleState('three'),
            'four': SimpleState('four'),
        }

    def tearDown(self):
        """Tear down the tests"""

    def _getControl(self):
        """Utility method to get a control"""
        return tools.Control('caption', RESOLUTION, RESOLUTIONS)

    def testSetupStates(self):
        """testSetupStates: can setup the initial state and states dictionary"""
        self.c.setup_states(self.states, 'one')
        #
        # Initial state should be set
        self.assertEqual('one', self.c.state._name)
        #
        # Other states should be there
        for name in self.states:
            self.assertTrue(name in self.c.state_dict)

    def testFailSetupStateWithBadState(self):
        """testFailSetupStateWithBadState: should fail cleanly when setting up states with a bad name"""
        self.assertRaises(KeyError, self.c.setup_states, self.states, 'NOT-THERE')

    def testUpdateChecksStateCompletion(self):
        """testUpdateChecksStateCompletion: update method should check if a state has completed"""
        raise NotImplementedError

    def testUpdateChecksForStateQuit(self):
        """testUpdateChecksForStateQuit: update method should check if a state wants to quite"""
        raise NotImplementedError

    def testUpdateCallsStateUpdate(self):
        """testUpdateCallsStateUpdate: update method should call the active states update method"""
        raise NotImplementedError

    def testUpdateCallsMusicHandlerUpdate(self):
        """testUpdateCallsMusicHandlerUpdate: update method should call the music handler update"""
        raise NotImplementedError

    def testUpdateWorksIfNoMusicHandler(self):
        """testUpdateWorksIfNoMusicHandler: update method should bypass music if no music handler"""
        raise NotImplementedError

    def testUpdateRespectsStateNotWantingMusic(self):
        """testUpdateRespectsStateNotWantingMusic: update should check and respect if state doesn't want music handled"""
        raise NotImplementedError

    def testUpdateShouldScaleScreen(self):
        """testUpdateShouldScaleScreen: update method should scale the screen"""
        raise NotImplementedError

    def testUpdateScreenScalingOmittedIfNotNeeded(self):
        """testUpdateScreenScalingOmittedIfNotNeeded: update method should do no scaling if it is not required"""
        raise NotImplementedError

    def testFlipState(self):
        """testFlipState: should be able to flip back to previous state"""
        raise NotImplementedError

    def testCanHandleKeyPressEvents(self):
        """testCanHandleKeyPressEvents: should detect and store key presses"""
        raise NotImplementedError

    def testCanHandleTakingScreenshots(self):
        """testCanHandleTakingScreenshots: should detect screenshot key and store screenshot"""
        raise NotImplementedError

    def testCanHandleFPS(self):
        """testCanHandleFPS: should detect FPS key pressed and show FPS"""
        raise NotImplementedError

    def testCanHandleScreenResize(self):
        """testCanHandleScreenResize: should call screen resize if the screen has changed"""
        raise NotImplementedError

    def testEventsArePassedToMusicHandler(self):
        """testEventsArePassedToMusicHandler: should pass on events to the music handler"""
        raise NotImplementedError

    def testResizeToLargerSize(self):
        """testResizeToLargerSize: can handle resizing to larger screen size"""
        raise NotImplementedError

    def testResizeToSmallerSize(self):
        """testResizeToSmallerSize: can handle resizing to smaller screen size"""
        raise NotImplementedError

    def testResizeToSameSize(self):
        """testResizeToSameSize: can handle resizing to same screen size"""
        raise NotImplementedError

    def testFailResizeIfInvalidSize(self):
        """testFailResizeIfInvalidSize: should fail cleanly if invalid screen size detected"""
        raise NotImplementedError

    def testCanToggleFPSDisplay(self):
        """testCanToggleFPSDisplay: should be able to toggle FPS display"""
        raise NotImplementedError

    def testMainLoopRespectsDone(self):
        """testMainLoopRespectsDone: main loop should quit when done is set"""
        raise NotImplementedError

    def testMainCallsUpdateWithDelta(self):
        """testMainCallsUpdateWithDelta: main loop should call update with appropriate delta"""
        raise NotImplementedError

    def testMainCausesFPSToShow(self):
        """testMainCausesFPSToShow: main loop should cause the FPS to display when needed"""
        raise NotImplementedError


class SimpleState(tools._State):
    """A simple state to use for testing"""

    def __init__(self, name):
        """Initialise the state"""
        super(SimpleState, self).__init__()
        self._name = name


if __name__ == '__main__':
    unittest.main()
