"""Tests for the main control class"""

import unittest
import contextlib
import os


# Default test settings
RESOLUTIONS = (
    (5, 10),
    (10, 20),
    (30, 40),
    (50, 60),
    (70, 80),
)
DEFAULT_RESOLUTION_INDEX = 1
RESOLUTION = RESOLUTIONS[DEFAULT_RESOLUTION_INDEX]

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
        pg.display.set_mode(RESOLUTION, pg.RESIZABLE)
        #
        # Some simple states
        self.states = {
            'one': SimpleState('one'),
            'two': SimpleState('two'),
            'three': SimpleState('three'),
            'four': SimpleState('four'),
        }
        #
        # Simple control to use for testing
        self.c = self._getControl()
        #
        # Flags for detecting calls
        self.called = {}
        self.call_arguments = {}

    def tearDown(self):
        """Tear down the tests"""

    def _getControl(self):
        """Utility method to get a control"""
        control = SimpleControl('caption', RESOLUTION, RESOLUTIONS)
        control.setup_states(self.states, 'one')
        return control

    def _catchCall(self, name):
        """Return a utility method to catch calls to mock methods"""
        self.called[name] = False
        #
        def called(*args, **kw):
            self.called[name] = True
            self.call_arguments[name] = (args, kw)
        #
        return called

    def _safeRemoveFile(self, filename):
        """Remove a file if it is there - if it isn't just return"""
        try:
            os.remove(filename)
        except OSError:
            pass

    def testSetupStates(self):
        """testSetupStates: can setup the initial state and states dictionary"""
        #
        # Initial state should be set
        self.assertEqual('one', self.c.state._name)
        #
        # Other states should be there
        for name in self.states:
            self.assertTrue(name in self.c.state_dict)

    def testFailSetupStateWithBadState(self):
        """testFailSetupStateWithBadState: should fail cleanly when setting up states with a bad name"""
        # TODO: this behaviour should throw a more specific error (StateNotFound)
        self.assertRaises(KeyError, self.c.setup_states, self.states, 'NOT-THERE')

    def testUpdateFlipsStateWhenStateCompletion(self):
        """testUpdateFlipsStateWhenStateCompletion: update should check if a state has completed and flip state"""
        #
        # Update should call flip_state if the state is done so we want to check for this
        self.c.flip_state = self._catchCall('flip_state')
        #
        # Call when state is not done
        self.c.update(10)
        self.assertFalse(self.called['flip_state'])
        #
        # Now make the state done and it should call flip_state
        self.c.state.done = True
        self.c.update(10)
        self.assertTrue(self.called['flip_state'])

    def testUpdateChecksForStateQuit(self):
        """testUpdateChecksForStateQuit: update method should check if a state wants to quit"""
        #
        # Normally control done should not be set
        self.assertFalse(self.c.done)
        self.assertFalse(self.c.state.quit)
        #
        # Updating shouldn't change that if the state is not requesting it
        self.c.update(10)
        self.assertFalse(self.c.done)
        #
        # Now setting state to quit should set control to done
        self.c.state.quit = True
        self.c.update(10)
        self.assertTrue(self.c.done)

    def testQuitCheckedBeforeDone(self):
        """testQuitCheckedBeforeDone: update should check for quit before done"""
        #
        # Update would call flip_state if the state is done so we want to check for this
        self.c.flip_state = self._catchCall('flip_state')
        #
        # Call when state request a quit
        self.c.state.quit = True
        self.c.update(10)
        #
        # Should be done and flip state should not have been called
        self.assertTrue(self.c.done)
        self.assertFalse(self.called['flip_state'])

    def testUpdateCallsStateUpdate(self):
        """testUpdateCallsStateUpdate: update method should call the active states update method"""
        #
        self.c.update(10)
        #
        # Update should have been called
        self.assertTrue(self.c.state._update_called)

    def testUpdateCallsMusicHandlerUpdate(self):
        """testUpdateCallsMusicHandlerUpdate: update method should call the music handler update if needed"""
        #
        # Simple mock music handler to check calls are working
        handler = Mock()
        handler.update = self._catchCall('update')
        handler.draw = self._catchCall('draw')
        #
        # Set up the control
        self.c.music_handler = handler
        #
        # Update and then the music handler methods should have been called
        self.c.update(10)
        self.assertTrue(self.called['update'])
        self.assertTrue(self.called['draw'])
        #
        # Now set the state to request no music handling
        self.c.state.use_music_handler = False
        self.called['update'] = False
        self.called['draw'] = False
        #
        # Methods should not be called now
        self.c.update(10)
        self.assertFalse(self.called['update'])
        self.assertFalse(self.called['draw'])

    def testUpdateWorksIfNoMusicHandler(self):
        """testUpdateWorksIfNoMusicHandler: update method should bypass music if no music handler"""
        #
        # Update should work fine if there is no music handler set
        self.assertEqual(None, self.c.music_handler)
        #
        self.c.update(10)
        # Nothing to test - should just work

    def testUpdateShouldScaleScreen(self):
        """testUpdateShouldScaleScreen: update method should scale the screen"""
        raise NotImplementedError

    def testUpdateScreenScalingOmittedIfNotNeeded(self):
        """testUpdateScreenScalingOmittedIfNotNeeded: update method should do no scaling if it is not required"""
        raise NotImplementedError

    def testFlipState(self):
        """testFlipState: should be able to flip back to previous state"""
        #
        # Set the next state to go to and catch calls to the initial cleanup function
        # and next state startup, which should be called during the process
        self.states['one'].next = 'two'
        self.states['one'].cleanup = self._catchCall('cleanup')
        self.states['two'].startup = self._catchCall('startup')
        #
        # Now flip
        self.c.flip_state()
        #
        # Expect that
        # - we are in the new state
        # - the old state was cleaned up
        # - the new state was started up
        # - the 'previous' state of the next state is the initial state
        self.assertEqual('two', self.c.state._name)
        self.assertTrue(self.called['cleanup'])
        self.assertTrue(self.called['startup'])
        self.assertEqual('one', self.c.state.previous)

    def testCanHandleKeyPressEvents(self):
        """testCanHandleKeyPressEvents: should detect and store key presses"""
        #
        # Should store the keys on both key down and key up
        for event_type, key in [(pg.KEYDOWN, pg.K_a), (pg.KEYUP, pg.K_b)]:
            events = [pg.event.Event(event_type, key=key)]
            keys = [key]
            #
            # Run the event loop with mocked out events
            with mock_pygame_events() as (event_queue, key_queue):
                #
                # Push events onto queue
                event_queue.append(events)
                key_queue.append(keys)
                #
                # Do the loop
                self.c.event_loop()
            #
            # Should have picked up the keys
            self.assertEqual(keys, self.c.keys)

    def testCanHandleTakingScreenshots(self):
        """testCanHandleTakingScreenshots: should detect screenshot key and store screenshot"""
        try:
            #
            # Should store the keys on both key down and key up
            events = [pg.event.Event(pg.KEYDOWN, key=pg.K_PRINT)]
            keys = [pg.K_PRINT]
            #
            # Get rid of the screenshot file if it there
            self._safeRemoveFile('screenshot.png')
            self.assertFalse(os.path.isfile('screenshot.png'))
            #
            # Run the event loop with mocked out events
            with mock_pygame_events() as (event_queue, key_queue):
                #
                # Push events onto queue
                event_queue.append(events)
                key_queue.append(keys)
                #
                # Do the loop
                self.c.event_loop()
            #
            # Should have taken a screenshot
            self.assertEqual(keys, self.c.keys)
            self.assertTrue(os.path.isfile('screenshot.png'))
        finally:
            # Make sure to clean up the screenshot file
            self._safeRemoveFile('screenshot.png')

    def testCanHandleFPS(self):
        """testCanHandleFPS: should detect FPS key pressed and show FPS"""
        #
        # Should store the keys on both key down and key up
        events = [pg.event.Event(pg.KEYDOWN, key=pg.K_F5)]
        keys = [pg.K_F5]
        #
        # Initially showing FPS should be off
        self.assertFalse(self.c.show_fps)
        #
        # Run the event loop with mocked out events
        with mock_pygame_events() as (event_queue, key_queue):
            #
            # Push events onto queue
            event_queue.append(events)
            key_queue.append(keys)
            #
            # Do the loop
            self.c.event_loop()
        #
        # Now should be showing FPS
        self.assertTrue(self.c.show_fps)

    def testCanHandleScreenResize(self):
        """testCanHandleScreenResize: should call screen resize if the screen has changed"""
        #
        # Should store the keys on both key down and key up
        events = [pg.event.Event(pg.VIDEORESIZE, size=RESOLUTIONS[2])]
        #
        # Initially screen should be default size
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        self.assertEqual(RESOLUTION, self.c.screen.get_size())
        #
        # Run the event loop with mocked out events
        with mock_pygame_events() as (event_queue, key_queue):
            #
            # Push events onto queue
            event_queue.append(events)
            #
            # Do the loop
            self.c.event_loop()
        #
        # Now should be new resolution
        self.assertEqual(RESOLUTIONS[2], self.c.screen_rect.size)
        self.assertEqual(RESOLUTIONS[2], self.c.screen.get_size())

    def testEventsArePassedToMusicHandler(self):
        """testEventsArePassedToMusicHandler: should pass on events to the music handler"""
        #
        # Simple mock music handler to check calls are working
        handler = Mock()
        handler.get_event = self._catchCall('get_event')
        #
        events = [pg.event.Event(pg.MOUSEMOTION)]
        #
        # Run the event loop with mocked out events
        with mock_pygame_events() as (event_queue, key_queue):
            #
            # Push events onto queue
            #
            # With no music handler, events should not call the method
            event_queue.append(events)
            self.c.event_loop()
            self.assertFalse(self.called['get_event'])
            #
            # With music handler but state not requesting music, should not call the method
            self.c.music_handler = handler
            self.c.state.use_music_handler = False
            event_queue.append(events)
            self.c.event_loop()
            self.assertFalse(self.called['get_event'])
            #
            # With state requesting music, should call the method
            self.c.state.use_music_handler = True
            event_queue.append(events)
            self.c.event_loop()
            self.assertTrue(self.called['get_event'])

    def testResizeToLargerSize(self):
        """testResizeToLargerSize: can handle resizing to larger screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTIONS[2])
        self.assertEqual(RESOLUTIONS[2], self.c.screen_rect.size)

    def testResizeToSmallerSize(self):
        """testResizeToSmallerSize: can handle resizing to smaller screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTIONS[0])
        self.assertEqual(RESOLUTIONS[0], self.c.screen_rect.size)

    def testResizeToSameSize(self):
        """testResizeToSameSize: can handle resizing to same screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTION)
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)

    def testResizeInvalidSize(self):
        """testResizeInvalidSize: should just grow or shrink screen if invalid resolution selected"""
        #
        # Increase size but not by enough
        self.c.on_resize((RESOLUTION[0] + 1, RESOLUTION[1] + 1))
        self.assertEqual(RESOLUTIONS[DEFAULT_RESOLUTION_INDEX + 1], self.c.screen_rect.size)
        #
        # Reset
        self.c.on_resize(RESOLUTION)
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Decrease size but not by enough
        self.c.on_resize((RESOLUTION[0] - 1, RESOLUTION[1] - 1))
        self.assertEqual(RESOLUTIONS[DEFAULT_RESOLUTION_INDEX - 1], self.c.screen_rect.size)

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


class SimpleControl(tools.Control):
    """A simple control to use for testing"""

    def __init__(self, *args, **kw):
        super(SimpleControl, self).__init__(*args, **kw)


class SimpleState(tools._State):
    """A simple state to use for testing"""

    def __init__(self, name):
        super(SimpleState, self).__init__()
        self._name = name
        self._update_called = False

    def update(self, surface, keys, now, dt, scale):
        super(SimpleState, self).update(surface, keys, now, dt, scale)
        self._update_called = True


class Mock(object):
    """Basic mocking object"""


class MockEvent(Mock):
    """Mock of Pygame event queue"""

    def __init__(self):
        self.queue = []

    def get(self):
        try:
            return self.queue.pop()
        except IndexError:
            return []

    def clear(self, event_type):
        pass


class MockKeys(Mock):
    """Mock of Pygame keyboard queue"""

    def __init__(self):
        self.queue = []

    def get_pressed(self):
        try:
            return self.queue.pop()
        except IndexError:
            return []


@contextlib.contextmanager
def mock_pygame_events():
    """Context manager to do lock mocking out of pygame events system"""
    #
    # Remember old pygame objects to restore later
    old_pg = pg.event, pg.key
    #
    # Mock of the event and keyboard queues
    pg.event = MockEvent()
    pg.key = MockKeys()
    #
    try:
        yield pg.event.queue, pg.key.queue
    finally:
        pg.event, pg.key = old_pg


if __name__ == '__main__':
    unittest.main()
