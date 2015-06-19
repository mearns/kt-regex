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

        @property
        def next(self):
            return self._next

    def __init__(self, char = None, *nextStates):
        self.char = char
        if len(nextStates):
            self._outputs = tuple(self.Output(self, state) for state in nextStates)
        else:
            self._outputs = tuple((self.Output(self),))

    def print_chain(self, ostream, indent='', already_printed = None):
        if already_printed is None:
            already_printed = {}

        repeat = self in already_printed
        if repeat:
            nodeid = '%s*' % (already_printed[self])
        else:
            nodeid = already_printed[self] = len(already_printed)+1

        line = ''
        if self.char is None:
            line += '%s( )' % (nodeid,)
        else:
            line += ('%s(%r)' % (nodeid, self.char))

        if repeat:
            ostream.write(line)

        else:
            if len(self.outputs) == 1:
                line += '-->'
                ostream.write(line)
                indent += ' '*len(line)
                next = self.outputs[0].next
                if next is not None:
                    next.print_chain(ostream, indent, already_printed)

            else:
                ostream.write(line)
                prefix = '|-->'
                oindent = indent
                indent = indent + '|' + (' '*(len(prefix)-1))
                for op in self.outputs:
                    ostream.write('\n')
                    ostream.write(oindent + prefix)
                    next = op.next
                    if next is not None:
                        next.print_chain(ostream, indent, already_printed)


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
    """
    A fragment is an encapsulation of one or more `State` objects. It has an `enter` state
    and any number of "dangling" `outputs`. Internally, there may be a digraph of additional states.
    The leaf states of this graph represent the terminal states of the fragment, and the collection
    of all outputs from those terminal states are the dangling outputs of the fragment.

    To join to fragments together, use the `append` method.
    """

    def __init__(self, enter):
        self.enter = enter
        self.outputs = set(enter.outputs)

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
        


def postfix_to_nfa(postfix):
    stack = []
    for c in postfix:
        #Concat.
        if c == '.':
            f2 = stack.pop()
            f1 = stack.pop()
            for op in f1.outputs:
                op.set(f2.enter)
            f1.outputs = f2.outputs
            stack.append(f1)

        #Alternate
        elif c == '|':
            f2 = stack.pop()
            f1 = stack.pop()

            #A state with automatic trigger and an output to each fragment.
            state = State(None, f1.enter, f2.enter)

            #Fragment's enter state is our newly created state.
            frag = Fragment(state)
            frag.outputs = f1.outputs.union(f2.outputs)

            stack.append(frag)

        #Zero or one
        elif c == '?':
            f = stack.pop()

            #New state to form the split. One output is dangling, one output goes to the
            # old fragment. Trigger is automatic
            state = State(None, f.enter, None)

            #New fragment has the new state as enter state.
            frag = Fragment(state)

            #Outputs of the fragment are the unused output of the new state, and the
            frag.outputs = set(f.outputs)
            frag.outputs.add(state.outputs[1])

            stack.append(frag)

        #Zero or more
        elif c == '*':
            f = stack.pop()

            #New state to form the split. One output is dangling and will serve as the
            # only output from this fragment. The other output will point to the enter
            # state of the old fragment.
            state = State(None, f.enter, None)

            #New fragment as the new state as enter state.
            frag = Fragment(state)

            #Only output from the fragment is the dangling output from the new state.
            frag.outputs = set((state.outputs[1],))

            #All dangling outputs from the old fragment loop back and point at our
            # new state, so after matching that fragment, they can either match it again, or
            # exit this fragment.
            for op in f.outputs:
                op.set(state)

            stack.append(frag)

        #One or more
        elif c == '+':
            f = stack.pop()

            #New state to form the split, /after/ the frag.
            # The new state has two outputs: one points back to the start of the fragment,
            # and one is unset, which will be the only dangling output from the new fragment.
            state = State(None, f.enter, None)

            #All the outputs of the fragment will point to this new state.
            for op in f.outputs:
                op.set(state)

            #TODO: Can probably reuse this fragment object, actually.
            frag = Fragment(f.enter)
            frag.outputs = set((state.outputs[1],))

            stack.append(frag)

        #Literal
        else:
            state = State(c)
            frag = Fragment(state)
            stack.append(frag)


    stack_length = len(stack)
    if stack_length == 1:
        return stack[0]

    elif stack_length > 1:
        raise Exception('Invalid expression, multiple fragments left on the stack.')

    else:
        raise Exception('Empty expression, nothing left on the stack.')


if __name__ == '__main__':
    
    import sys


    frag = postfix_to_nfa('ab.c|+e.fgh..|')

    frag.enter.print_chain(sys.stdout)
    


