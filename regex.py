#! /usr/bin/env python
# vim: set fileencoding=utf-8: set encoding=utf-8:

import abc


class State(object):

    class Output(object):
        def __init__(self, state, next=None):
            self._state = state
            self._next = next

        def set(self, state):
            self._next = state

        @proeprty
        def next(self):
            return self._next

    def __init__(self, char = None, num_outputs):
        self.char = char
        self._outputs = tuple(Output(self) for i in xrange(num_outputs))

    @property
    def outputs(self):
        return self._outputs

    def advance(self, char):
        """
        Advance to the next state or states, given that ``char`` is the next character.
        Return a collection of all states that are now active as a result. Returning an
        empty set indicates that there is no transition out of this state for the given
        ``char``. Returning None indicates that we reached a terminal match state.
        """
        raise NotImplementedError()

class Fragment(object):
    def __init__(self, enter):
        self._enter = enter
        self._outputs = enter.outputs

    def append(self, state):
        for op in self._outputs:
            op.set(state)
        self._outputs = state.outputs
        


def postfixToNfa(postfix):
    stack = []
    for c in postfix:
        #Concat.
        if c == '.':
            f2 = stack.pop()
            f1 = stack.pop()
            f1.append(f2)

        elif c == '|':
            #XXX

        else:
            state = State(c, 1)
            frag = Fragment(state)
            stat.push(frag)




if __name__ == '__main__':
    pass


