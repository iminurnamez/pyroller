"""Tests for the main control class"""

import unittest
import time


class TestControl(unittest.TestCase):
    """Tests for the Control"""

    def setUp(self):
        """Set up the tests"""
    
    def tearDown(self):
        """Tear down the tests"""

    def testCreate(self):
        """testCreate: can create a control object"""
        raise NotImplementedError
    
    def testSetupStates(self):
        """testSetupStates: can setup the initial state and states dictionary"""
        raise NotImplementedError

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


if __name__ == '__main__':
    unittest.main()
