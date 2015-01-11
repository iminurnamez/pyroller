# coding=utf-8
#
# fysom - pYthOn Finite State Machine - this is a port of Jake
#         Gordon's javascript-state-machine to python
#         https://github.com/jakesgordon/javascript-state-machine
#
# Copyright (C) 2011 Mansour Behabadi <mansour@oxplot.com>, Jake Gordon
#                                        and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__author__ = 'Mansour Behabadi'
__copyright__ = 'Copyright 2011, Mansour Behabadi and Jake Gordon'
__credits__ = ['Mansour Behabadi', 'Jake Gordon']
__license__ = 'MIT'
__version__ = '${version}'
__maintainer__ = 'Mansour Behabadi'
__email__ = 'mansour@oxplot.com'


import collections


WILDCARD = '*'


class FysomError(Exception):

    '''
        Raised whenever an unexpected event gets triggered.
    '''
    pass


class Canceled(FysomError):

    '''
        Raised when an event is canceled due to the
        onbeforeevent handler returning False
    '''


class Fysom(object):

    '''
        Wraps the complete finite state machine operations.
    '''

    def __init__(self, cfg={}, initial=None, events=None, callbacks=None, final=None):
        '''
        Construct a Finite State Machine.

        Arguments:

            cfg         finite state machine specification,
                        a dictionary with keys 'initial', 'events', 'callbacks', 'final'

            initial     initial state

            events      a list of dictionaries (keys: 'name', 'src', 'dst')
                        or a list tuples (event name, source state or states,
                        destination state or states)

            callbacks   a dictionary mapping callback names to functions

            final       a state of the FSM where its is_finished() method returns True

        Named arguments override configuration dictionary.

        Example:

        >>> fsm = Fysom(events=[('tic', 'a', 'b'), ('toc', 'b', 'a')], initial='a')
        >>> fsm.current
        'a'
        >>> fsm.tic()
        >>> fsm.current
        'b'
        >>> fsm.toc()
        >>> fsm.current
        'a'

        '''
        cfg = dict(cfg)
        # override cfg with named arguments
        if "events" not in cfg:
            cfg["events"] = []
        if "callbacks" not in cfg:
            cfg["callbacks"] = {}
        if initial:
            cfg["initial"] = initial
        if final:
            cfg["final"] = final
        if events:
            cfg["events"].extend(list(events))
        if callbacks:
            cfg["callbacks"].update(dict(callbacks))
        # convert 3-tuples in the event specification to dicts
        events_dicts = []
        for e in cfg["events"]:
            if isinstance(e, collections.Mapping):
                events_dicts.append(e)
            elif hasattr(e, "__iter__"):
                name, src, dst = list(e)[:3]
                events_dicts.append({"name": name, "src": src, "dst": dst})
        cfg["events"] = events_dicts
        self._apply(cfg)

    def isstate(self, state):
        '''
            Returns if the given state is the current state.
        '''
        return self.current == state

    def can(self, event):
        '''
            Returns if the given event be fired in the current machine state.
        '''
        return (event in self._map and ((self.current in self._map[event]) or WILDCARD in self._map[event])
                and not hasattr(self, 'transition'))

    def cannot(self, event):
        '''
            Returns if the given event cannot be fired in the current state.
        '''
        return not self.can(event)

    def is_finished(self):
        '''
            Returns if the state machine is in its final state.
        '''
        return self._final and (self.current == self._final)

    def _apply(self, cfg):
        '''
            Does the heavy lifting of machine construction. More notably:
             >> Sets up the initial and finals states.
             >> Sets the event methods and callbacks into the same object namespace.
             >> Prepares the event to state transitions map.
        '''
        init = cfg['initial'] if 'initial' in cfg else None
        if self._is_base_string(init):
            init = {'state': init}

        self._final = cfg['final'] if 'final' in cfg else None

        events = cfg['events'] if 'events' in cfg else []
        callbacks = cfg['callbacks'] if 'callbacks' in cfg else {}
        tmap = {}
        self._map = tmap

        def add(e):
            '''
                Adds the event into the machine map.
            '''
            if 'src' in e:
                src = [e['src']] if self._is_base_string(
                    e['src']) else e['src']
            else:
                src = [WILDCARD]
            if e['name'] not in tmap:
                tmap[e['name']] = {}
            for s in src:
                tmap[e['name']][s] = e['dst']

        # Consider initial state as any other state that can have transition from none to
        # initial value on occurance of startup / init event ( if specified).
        if init:
            if 'event' not in init:
                init['event'] = 'startup'
            add({'name': init['event'], 'src': 'none', 'dst': init['state']})

        for e in events:
            add(e)

        # For all the events as present in machine map, construct the event handler.
        for name in tmap:
            setattr(self, name, self._build_event(name))

        # For all the callbacks, register them into the current object namespace.
        for name in callbacks:
            setattr(self, name, callbacks[name])

        self.current = 'none'

        # If initialization need not be deferred, trigger the event for transition to initial state.
        if init and 'defer' not in init:
            getattr(self, init['event'])()

    def _build_event(self, event):
        '''
            For every event in the state machine, prepares the event handler and
            registers the same into current object namespace.
        '''
        def fn(*args, **kwargs):

            if hasattr(self, 'transition'):
                raise FysomError(
                    "event %s inappropriate because previous transition did not complete" % event)

            # Check if this event can be triggered in the current state.
            if not self.can(event):
                raise FysomError(
                    "event %s inappropriate in current state %s" % (event, self.current))

            # On event occurence, source will always be the current state.
            src = self.current
            # Finds the destination state, after this event is completed.
            dst = ((src in self._map[event] and self._map[event][src]) or
                   WILDCARD in self._map[event] and self._map[event][WILDCARD])

            # Prepares the object with all the meta data to be passed to callbacks.
            class _e_obj(object):
                pass
            e = _e_obj()
            e.fsm, e.event, e.src, e.dst = self, event, src, dst
            for k in kwargs:
                setattr(e, k, kwargs[k])

            setattr(e, 'args', args)

            # Try to trigger the before event, unless it gets canceled.
            if self._before_event(e) is False:
                raise Canceled(
                    "Cannot trigger event {0} because the onbefore{0} handler returns False".format(e.event))

            # Wraps the activities that must constitute a single successful transaction.
            if self.current != dst:
                def _tran():
                    delattr(self, 'transition')
                    self.current = dst
                    self._enter_state(e)
                    self._change_state(e)
                    self._after_event(e)
                self.transition = _tran

                # Hook to perform asynchronous transition.
                if self._leave_state(e) is not False:
                    self.transition()
            else:
                self._reenter_state(e)
                self._after_event(e)

        fn.__name__ = str(event)
        fn.__doc__ = ("Event handler for an {event} event. This event can be " +
                      "fired if the machine is in {states} states.".format(
                          event=event, states=self._map[event].keys()))

        return fn

    def _before_event(self, e):
        '''
            Checks to see if the callback is registered before this event can be triggered.
        '''
        fnname = 'onbefore' + e.event
        if hasattr(self, fnname):
            return getattr(self, fnname)(e)

    def _after_event(self, e):
        '''
            Checks to see if the callback is registered for, after this event is completed.
        '''
        for fnname in ['onafter' + e.event, 'on' + e.event]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def _leave_state(self, e):
        '''
            Checks to see if the machine can leave the current state and perform the transition.
            This is helpful if the asynchronous job needs to be completed before the machine can
            leave the current state.
        '''
        fnname = 'onleave' + e.src
        if hasattr(self, fnname):
            return getattr(self, fnname)(e)

    def _enter_state(self, e):
        '''
            Executes the callback for onenter_state_ or on_state_.
        '''
        for fnname in ['onenter' + e.dst, 'on' + e.dst]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def _reenter_state(self, e):
        '''
            Executes the callback for onreenter_state_.
            This allows callbacks following reflexive transitions (i.e. where src == dst)
        '''
        fnname = 'onreenter' + e.dst
        if hasattr(self, fnname):
            return getattr(self, fnname)(e)

    def _change_state(self, e):
        '''
            A general change state callback. This gets triggered at the time of state transition.
        '''
        fnname = 'onchangestate'
        if hasattr(self, fnname):
            return getattr(self, fnname)(e)

    def _is_base_string(self, object):  # pragma: no cover
        '''
            Returns if the object is an instance of basestring.
        '''
        try:
            return isinstance(object, basestring)
        except NameError:
            return isinstance(object, str)

    def trigger(self, event, *args, **kwargs):
        '''
            Triggers the given event.
            The event can be triggered by calling the event handler directly, for ex: fsm.eat()
            but this method will come in handy if the event is determined dynamically and you have
            the event name to trigger as a string.
        '''
        if not hasattr(self, event):
            raise FysomError(
                "There isn't any event registered as %s" % event)
        return getattr(self, event)(*args, **kwargs)