"""Simple system to propagate events throughout the game


There are two main use cases for the event system:

1. Making general components (like buttons) the people can use in lots of
different ways

2. Allowing different components of the application to respond to global changes
without having to explicitly pass around references to the components (Broadcasting)

These use cases are described in more detail below.


1. General Components
=====================

You need a general component that will detect certain conditions and then
delegate a response to another component. Since your general component doesn't
know ahead of time what to do (eg when a button it clicked) it creates an event
and other interested components can listen for the event and respond accordingly.

This is implemented by,

 1. Defining an event (by convention this is just a string, eg "button-click")
 2. Create your component class (MyComponent) using the EventAware class as a mixin
 3. Call MyComponent.initEvents in your component
 4. When your component detects an event then have it call MyComponent.processEvent(("button-click", self))
 5. Interested components call MyComponent.linkEvent("button-click", some_function_to_call, arg)
 6. Component defines some_function_to_call(obj, arg)

When the button click is detected then some_function_to_call will be executed with the button instance
and the (optional) argument.

Example code is below,

E_BUTTON_CLICK = 'button-click'

class MyButton(EventAware):
    def __init__(self, name, x, y):
        self.initEvents()
        ...

    def periodicCheck(self):
        '''This would be called by the framework'''
        # Check for stuff
        if button_is_clicked_on:
            self.processEvents((E_BUTTON_CLICK, self))

class MyGameScreen:
    def __init__(self):
        self.ok_button = MyButton('OK', 100, 200)
        self.ok_button.linkEvent(E_BUTTON_CLICK, self.button_clicked)
        self.cancel_button = MyButton('Cancel', 200, 200)
        self.cancel_button.linkEvent(E_BUTTON_CLICK, self.button_clicked)

    def button_clicked(self, button, arg=None):
        print('Button {0} was clicked'.format(button.name)

Now MyGameScreen can implement all the handling for button clicks and other events.



2. Broadcasting
===============

You have components that need to respond to certain state changes in the application
but it is tricky to pass around references to the components that detect the changes.
You can use one or more Broadcasters to publish events for components to listen to.

For example, suppose you want to award points to the player for various activities but
the activities are handled by numerous components. You can define a global event and use
a global broadcaster to route notifications that the event has occurred.

This is implemented by,

1. Defining an event (by convention this is just a string, eg "player-did-well")
2. Define a global singleton broadcaster, Broadcaster
3. The score handling component registers interest in "player-did-well" events by calling
the Broadcaster.linkEvent("player-did-well", ...) method
4. At any place in the rest of the application where appropriate call
the broadcaster.processEvent(("player-did-well", ..)) method

Example code is below,

E_DID_WELL = 'player-did-well'

class MyScorer:
    def __init__(self):
        Broadcaster.linkEvent(E_DID_WELL, self.player_did_well)
        self.score = 0

    def player_did_well(self, obj, score):
        '''Record that the player did well'''
        print('Player did well, detected by {0}. Score of {1}'.format(obj, score))
        self.score += score

# in some other components ...

class OtherComponent1:
    def periodicCheck(self):
        # some series of checks determining if the player did something
        if the_player_did_well:
            Broadcaster.processEvent((E_DID_WELL, +10))

class OtherComponent2:
    def periodicCheck(self):
        # some series of checks determining if the player did something
        if the_player_did_well:
            Broadcaster.processEvent((E_DID_WELL, +20))

"""


class EventNotLinked(Exception):
    """An event was not found or linked to anything"""


class EventAware(object):
    """A mixin class that allows objects to respond to events"""

    def initEvents(self):
        """Initialise the events system

        All classes inheriting from this mixin should call this as soon as they are
        created and before any other components try to link events.

        """
        self._event_handlers = {}
        self._registered_events = set()

    def processEvent(self, event):
        """Process an incoming event

        event is a tuple of (event_name, object_detecting_event)

        The event name can be anything but it is typically useful to make it a meaningful
        string so that you can easily debug what is going on when events are being called.

        """
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
        """Handle an incoming event

        Subclasses can specifically implement this if they want to do something in particular
        rather than just calling all the event listeners. Normally this is not necessary.
        """
        return None

    def linkEvent(self, name, callback, arg=None):
        """Link an event to a callback

        Name should be an event name (typically a string) and callback should be a callable
        function with a signature (obj, arg). This is the function that will be called
        when the event is triggered.

        The optional argument arg will be passed to the callback. This allows more general
        callback functions to be defined.

        """
        self._event_handlers.setdefault(name, []).append((callback, arg))

    def unlinkEvent(self, name, callback=None):
        """Unlink an event from a callback

        This will stop a listener being called whenever an event occurs.

        """
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
    """A simple broadcaster of events

    This is a useful class to create as a singleton to be used within a certain scope
    of the application to allow components to broadcast and listen for certain events
    occurring within the application without having to explicitly link the components
    together.

    """

    def __init__(self):
        """Initialise the broadcaster"""
        self.initEvents()