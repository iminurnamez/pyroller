class State(object):
    """
    This is a prototype class for States.  All states should inherit from it.
    No direct instances of this class should be created. get_event and update
    must be overloaded in the childclass.  startup and cleanup need to be
    overloaded when there is data that must persist between States.
    """
    name = 'State Name'

    def __init__(self, persistant={}):
        self.start_time = 0.0
        self.now = 0.0
        self.done = False
        self.quit = False
        self.next = None
        self.previous = None
        self.persist = persistant
        self.use_music_handler = True

    def get_event(self, event, scale=(1,1)):
        """
        Processes events that were passed from the main event loop.
        Must be overloaded in children.
        """
        pass

    def startup(self, now, persistent):
        """
        Add variables passed in persistent to the proper attributes and
        set the start time of the State to the current time.
        """
        self.persist = persistent
        self.start_time = now

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        return self.persist

    def update(self, surface, keys, now, dt, scale):
        """Update function for state.  Must be overloaded in children."""
        pass

    def render_font(self, font, msg, color, center):
        """Return the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 1, color)
        rect = msg.get_rect(center=center)
        return msg, rect
