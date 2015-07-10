"""Tests for the main control class"""

import unittest
import contextlib
import os


# Default test settings
import data.control
import data.state

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
        self.call_times = {}

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
            self.call_times[name] = self.call_times.get(name, 0) + 1
        #
        return called

    def _safeRemoveFile(self, filename):
        """Remove a file if it is there - if it isn't just return"""
        try:
            os.remove(filename)
        except OSError:
            pass

    def _checkPoint(self, colour, surface, point, name, accuracy=1, check_alpha=True):
        """Check a point is the right colour

        There is quite a bit of variability in pixel colours so this method allows
        some variation in the check and it will still pass

        """
        x, y = point
        upto = 4 if check_alpha else 3
        try:
            got = surface.get_at((x, y))
        except IndexError:
            raise IndexError('Point {0} is outside the range of the surface'.format(point))
        for e, g in list(zip(colour, got))[:upto]:
            self.assertTrue(abs(e - g) <= accuracy,
                         '%s - Failed colour test at %d, %d (%s). Expected (%s)' % (name, x, y, got, colour))

    def testSetupStates(self):
        """can setup the initial state and states dictionary"""
        #
        # Initial state should be set
        self.assertEqual('one', self.c.state._name)
        #
        # Other states should be there
        for name in self.states:
            self.assertTrue(name in self.c.state_dict)

    def testFailSetupStateWithBadState(self):
        """should fail cleanly when setting up states with a bad name"""
        # TODO: this behaviour should throw a more specific error (StateNotFound)
        self.assertRaises(KeyError, self.c.setup_states, self.states, 'NOT-THERE')

    def testUpdateFlipsStateWhenStateCompletion(self):
        """update should check if a state has completed and flip state"""
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
        """update method should check if a state wants to quit"""
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
        """update should check for quit before done"""
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
        """update method should call the active states update method"""
        #
        self.c.update(10)
        #
        # Update should have been called
        self.assertTrue(self.c.state._update_called)

    def testUpdateCallsMusicHandlerUpdate(self):
        """update method should call the music handler update if needed"""
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
        """update method should bypass music if no music handler"""
        #
        # Update should work fine if there is no music handler set
        self.assertEqual(None, self.c.music_handler)
        #
        self.c.update(10)
        # Nothing to test - should just work

    def testRenderShouldScaleScreen(self):
        """Control.render method should scale the screen"""
        #
        # We will creatae an image at a higher resolution and then
        # use the control render method to scale back down.
        w, h = 100, 100
        self.c = SimpleControl('control', (w, h), [])

        self.c.render_size = (w, h)
        real_surface = pg.Surface(self.c.render_size)
        self.c.render_surf = real_surface
        real_surface.fill((255, 0, 0))
        pg.draw.rect(real_surface, (0, 255, 0), (10, 10, 80, 80))
        #
        # The new surface should be red at the edges and green in the middle
        for point in ((0, 0), (0, w - 1), (h - 1, 0), (w - 1, h - 1)):
            self._checkPoint((255, 0, 0), real_surface, point, 'red', 1, False)
        for point in ((11, 11), (11, 88), (88, 11), (88, 88)):
            self._checkPoint((0, 255, 0), real_surface, point, 'green', 1, False)
        #
        # Now call render, which should create a scaled down version of this
        self.c.render()
        #pg.image.save(self.c.render_surf, 'test1.png')
        #pg.image.save(self.c.screen, 'test2.png')
        #
        # Check size
        self.assertEqual(RESOLUTION, self.c.screen.get_size())
        #
        # Offsets of the test pixels to check scaling
        dx, dy = int(10./w * RESOLUTION[0]) + 1, int(10./h * RESOLUTION[1]) + 1
        #
        # The scaled surface should be red at the edges and green in the middle
        for point in ((0, 0), (RESOLUTION[0] - 1, 0), (0, RESOLUTION[1] - 1),
                      (RESOLUTION[0] - 1, RESOLUTION[1] - 1)):
            self._checkPoint((255, 0, 0), self.c.screen, point, 'red', 5, False)
        for point in ((dx, dy), (RESOLUTION[0] - 1 - dx, dy), (dx, RESOLUTION[1] - 1 - dy),
                      (RESOLUTION[0] - 1 - dx, RESOLUTION[1] - 1 - dy)):
            self._checkPoint((0, 255, 0), self.c.screen, point, 'green', 5, False)

    def testFlipState(self):
        """should be able to flip back to previous state"""
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
        """should detect and store key presses"""
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
        """should detect screenshot key and store screenshot"""
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
        """should detect FPS key pressed and show FPS"""
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
        """should call screen resize if the screen has changed"""
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
        """should pass on events to the music handler"""
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
        """can handle resizing to larger screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTIONS[2])
        self.assertEqual(RESOLUTIONS[2], self.c.screen_rect.size)

    def testResizeToSmallerSize(self):
        """can handle resizing to smaller screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTIONS[0])
        self.assertEqual(RESOLUTIONS[0], self.c.screen_rect.size)

    def testResizeToSameSize(self):
        """can handle resizing to same screen size"""
        #
        # Initial size should be default
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)
        #
        # Increase size
        self.c.on_resize(RESOLUTION)
        self.assertEqual(RESOLUTION, self.c.screen_rect.size)

    def testResizeInvalidSize(self):
        """should just grow or shrink screen if invalid resolution selected"""
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
        """should be able to toggle FPS display"""
        #
        # By default caption should not include FPS
        with controllable_main_loop(self, 'pgupdate', 1):
            self.c.main()
            self.assertEqual('pygame window', pg.display.get_caption()[0])
        #
        # When turning on FPS then the caption should reflect it
        self.c.done = False
        with controllable_main_loop(self, 'pgupdate', 1):
            self.c.show_fps = True
            self.c.main()
            #
            # We don't check the exact text, just that there is some FPS display
            self.assertTrue('FPS' in pg.display.get_caption()[0])

    def testMainLoopRespectsDone(self):
        """main loop should quit when done is set"""
        #
        # Need to check that main does something but exits so we check
        # that it will call the event_loop
        self.c.event_loop = self._catchCall('event_loop')
        with controllable_main_loop(self, 'pgupdate', 2, after_call=lambda: setattr(self.c, 'done', True)):
            self.c.main()
            self.assertTrue(self.called['event_loop'])

    def testMainCallsUpdateWithDelta(self):
        """main loop should call update with appropriate delta"""
        #
        # Check that the main loop calls update with the right delta
        self.c.update = self._catchCall('update')
        with controllable_main_loop(self, 'pgupdate', 2):
            self.c.fps = 10
            self.c.main()
            #
            # Update should have been called with a delta of 10 fps (ie 1/10th of a second)
            self.assertTrue(self.called['update'])
            self.assertAlmostEqual(self.call_arguments['update'][0][0] / 1000., 0.1, 2)
        #
        # Now do again with a different FPS
        with controllable_main_loop(self, 'pgupdate', 2):
            self.called['update'] = False
            self.c.fps = 20
            self.c.done = False
            self.c.main()
            #
            self.assertTrue(self.called['update'])
            self.assertAlmostEqual(self.call_arguments['update'][0][0] / 1000., 0.05, 2)

    def testMainCallsPygameUpdate(self):
        """main loop should call pygame update"""
        #
        # This test is a bit redundant given how we are controlling the main loop
        # but is kept here as a reminder to create the proper test when the
        # main loop is made more directly testable
        #
        with controllable_main_loop(self, 'pgupdate', 2):
            self.c.main()
        #
        self.assertTrue(self.called['pgupdate'])

    def testCanExitMainAfterNumberOfIterations(self):
        """should be able to quit the main loop after a number of iterations"""
        #
        # Test base behaviour that continues to run for ever
        with controllable_main_loop(self, 'pgupdate-1', 10):
            self.c.main()
        #
        # Should have called the update 10 times
        self.assertEqual(10, self.call_times['pgupdate-1'])
        #
        # Now try again but tell the control to only run for a few iterations
        # and check that we called the exact amount of times
        self.c.max_iterations = 5
        self.c.done = False
        with controllable_main_loop(self, 'pgupdate-2', 10):
            self.c.main()
        #
        self.assertEqual(5, self.call_times['pgupdate-2'])


class SimpleControl(data.control.Control):
    """A simple control to use for testing"""

    def __init__(self, *args, **kw):
        super(SimpleControl, self).__init__(*args, **kw)


class SimpleState(data.state.State):
    """A simple state to use for testing"""

    def __init__(self, name):
        super(SimpleState, self).__init__()
        self._name = name
        self._update_called = False
        self._surface_to_render = None

    def update(self, surface, keys, now, dt, scale):
        super(SimpleState, self).update(surface, keys, now, dt, scale)
        #
        # Test rendering to the surface
        if self._surface_to_render:
            surface.blit(self._surface_to_render, (0, 0))
        #
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


class RanTooLongException(Exception): """The main loop ran for too long"""


@contextlib.contextmanager
def controllable_main_loop(test_class, called_name, loops, after_call=None):
    """Context manager to allow the main loop to be controlled"""
    #
    # This is a real hack - we cannot run the main loop and exit without creating
    # threads which are a pain in unit tests. So we abuse the fact that pg.display.update
    # should be called. We replace that call with some control logic that allows us to
    # break out at will.
    # TODO: alter the main loop to be testable
    #
    control = test_class.c
    #
    def new_update():
        test_class.called[called_name] = True
        test_class.call_times[called_name] = test_class.call_times.get(called_name, 0) + 1
        control._update_count += 1
        if control._update_count == loops:
            # This should break out of the main loop ...
            control.done = True
        elif control._update_count >= loops:
            # But if the main loop is badly broken then we will be stuck
            # in which case we raise an exception to make sure the test doesn't
            # hang completely
            raise RanTooLongException('Main loop did not exit properly')
        #
        if after_call:
            after_call()
    #
    old_pg = pg.display.update
    pg.display.update = new_update
    control._update_count = 0
    #
    try:
        yield
    finally:
        pg.display.update = old_pg


if __name__ == '__main__':
    unittest.main()
