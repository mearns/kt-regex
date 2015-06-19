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

    def __init__(self, char = None, *nextStates):
        self.char = char
        if len(nextStates):
            self._outputs = tuple(Output(self, state) for state in nextStates)
        else:
            self._outputs = tuple(Output(self),)

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

    @property
    def enter(self):
        return self._enter

    def append(self, fragment):
        """
        Adds the given fragment as a follow on to this one, so that all the dangling
        outputs of this fragment point to the enter state of the given frament, and the
        outputs of that fragment become the outputs of this one, so that this fragment
        effectively consumes the given one.
        """
        state = fragment.enter
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
            stack.push(f1)

        elif c == '|':
            #XXX
            f2 = stack.pop();
            f1 = stack.pop();
            state = State(None)
            frag = Fragment(state)

            outputs = state.outputs
            outputs[0].set(f1.enter)
            outputs[1].set(f2.enter)

            stack.push(frag)


        else:
            state = State(c)
            frag = Fragment(state)
            stack.push(frag)




if __name__ == '__main__':
    pass


