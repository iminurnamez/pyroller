"""Simple system to propagate events throughout the game"""


class EventNotLinked(Exception):
    """An event was not found or linked to anything"""


class EventAware(object):
    """A mixin class that allows objects to respond to events"""

    def initEvents(self):
        """Initialise the events system"""
        self._event_handlers = {}
        self._registered_events = set()

    def processEvent(self, event):
        """Process an incoming event"""
        name, obj = event
        #
        # Try to pass this off to a handler
        inhibits = set()
        try:
            links = self._event_handlers[name]
        except KeyError:
            new_inhibits = self.handleEvent(event)
            # Watch for new events to inhibit
            if new_inhibits:
                inhibits.add(new_inhibits)
        else:
            #
            # Process all the handler functions
            for callback, arg in links:
                new_inhibits = callback(obj, arg)
                # Watch for new events to inhibit
                if new_inhibits:
                    inhibits.add(new_inhibits)
        return inhibits

    def handleEvent(self, event):
        """Handle an incoming event"""
        return None

    def linkEvent(self, name, callback, arg=None):
        """Link an event to a callback"""
        self._event_handlers.setdefault(name, []).append((callback, arg))

    def unlinkEvent(self, name, callback=None):
        """Unlink an event from a callback"""
        if callback is None:
            try:
                del(self._event_handlers[name])
            except KeyError:
                raise EventNotLinked('No links to event "%s"' % name)
        else:
            #
            # Look for items with the same name and callback
            try:
                old_items, new_items = self._event_handlers[name], []
            except KeyError:
                raise EventNotLinked('No links to event "%s"' % name)
            #
            for the_callback, arg in old_items:
                if the_callback != callback:
                    # This one is ok
                    new_items.append((the_callback, arg))
            #
            # Were any changed?
            if old_items == new_items:
                raise EventNotLinked('No links for event "%s" with callback "%s"' % (name, callback))
            #
            # Reset events
            self._event_handlers[name] = new_items


class Broadcaster(EventAware):
    """A simple broadcaster of events"""

    def __init__(self):
        """Initialise the broadcaster"""
        self.initEvents()