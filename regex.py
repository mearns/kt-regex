#! /usr/bin/env python
# vim: set fileencoding=utf-8: set encoding=utf-8:

import abc


class State(object):
    """
    Represents a state in a Nondeterministic Finite Automaton (NFA). A state has
    a `trigger`, which can be thougt of as an acceptance test. If the incoming sequence
    matches the trigger, then the state advances to the next state or states.
    A state can also be auto-triggered, which is specified by having the trigger set to ``None``.
    An auto-triggered state automatically advances to the next state(s), regardless of input.

    A state also has zero or more `outputs`. Outputs are kind of like sockets that another
    state can be plugged into, forming a directed graph of states.
    """

    def __init__(self, trigger = None, *nextStates):
        """
        :param trigger: The trigger for this state, or ``None`` for an auto-triggered state.

        :param \*nextStates:    Any additional arguments are taken as the next states, and are plugged
            into `outputs` for the created state. The outputs are set at init time, so you cannot
            add or remove outputs afterwards, but you can reassign them (each output is actually
            an `Output` object, so you can use the `Output.set` method). To reserve an output without
            specifying the next state, just pass ``None``. This creates a "dangling" output.
        """
        self._trigger = trigger
        if len(nextStates):
            self._outputs = tuple(self.Output(self, state) for state in nextStates)
        else:
            self._outputs = tuple()

    @staticmethod
    def Match():
        return State(None)

    def print_chain(self, ostream, indent='', already_printed = None):
        """
        Pretty prints the graph of states, starting with this one.
        Each node in the graph is printed as a unique numeric identifier, which
        start with 1 and increment for each node visited (left to right, top bottom).
        Note that numeric IDs are unique to the particular printing of the graph,
        they may change if the graph changes or a different subgraph is printed.

        Nodes are printed with their numeric IDs, followed by their trigger in parenthesis.
        An empty pair of parens means an automatic trigger.

        Transitions are printed as arrows leading from the node to the next node(s).

        Cycles are detected and printed as a node reference. This simply prints the
        node again, but with a ``*`` after the nodeid, indicating that the node already
        exists somewhere in the graph (previously on the same line, or in on a previous
        line). The children of the referenced node are not pritned again, since this
        can lead to infinite recursion.
        """
        if self.is_match():
            ostream.write('M')
            return

        if already_printed is None:
            already_printed = {}

        repeat = self in already_printed
        if repeat:
            nodeid = '%s*' % (already_printed[self])
        else:
            nodeid = already_printed[self] = len(already_printed)+1

        line = ''
        if self.trigger is None:
            line += '%s( )' % (nodeid,)
        else:
            line += ('%s(%r)' % (nodeid, self.trigger))

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

    def is_match(self):
        return len(self.outputs) == 0 and self.trigger is None

    @property
    def trigger(self):
        """
        The trigger acts as an acceptance test for the state.
        """
        return self._trigger

    @property
    def outputs(self):
        """
        A tuple of the outputs from this state. Each element in the tuple is an `Output`
        object which can be assigned at any time to point to any state in order to create
        the NDA graph.

        The tuple itself is created at initialization and fixed, so the number of outputs is
        locked in, even though they can be reassigned. An output with no state assigned to it
        (i.e., ``None`` assigned) repersents a "dangling" output which is generally used for
        chaining `Fragment` objects.
        """
        return self._outputs

    def __repr__(self):
        return 'State#%s(%r)' % (id(self), self._trigger)

    def auto_expand(self):
        if self.trigger is None:
            expanded = set()
            for op in self._outputs:
                next = op.next
                if next is not None:
                    expanded = expanded.union(next.auto_expand())
            return expanded
        else:
            #Not auto-triggered, so return self
            return set((self,))

    def advance(self, char=None):
        """
        Advance to the next state or states, given that ``char`` is the next character.
        Return a set of all states that are now active as a result. Returning an
        empty set indicates that the state didn't pass. Returning ``True`` indicates
        a match has occurred at this state.
        """
        next_states = set()
        current_states = self.auto_expand()
        print 'Expanded to %r' % (current_states,)
        for state in current_states:
            print 'Checking %r against %r' % (char, state.trigger)
            assert (state.trigger is not None)
            if state.trigger == char:
                #This state passed
                print 'Accepted.'
                if len(state.outputs):
                    #Has outputs, so those states become active.
                    new_state = set((op.next for op in state.outputs if op.next is not None))
                    print 'New states: %r' % (new_state,)
                    next_states = next_states.union(new_state)
                else:
                    #No outputs, this is a match state.
                    print 'Accepted. Returning True'
                    return True

        return next_states


    def match(self, string):
        active_states = set((self,))

        for c in string:
            new_states = set()
            for state in active_states:
                next_states = state.advance(c)
                print "Advanced to: %r" % (next_states,)
                if next_states is True:
                    #Found a match
                    return True
                else:
                    new_states = new_states.union(next_states)
                    
            #None of the current states matched.
            print "New states: %r" % (new_states,)
            if len(new_states) == 0:
                break

            active_states = new_states;

        #If any states are auto-advance, we need to let them go as well.
        while active_states:
            new_states = set()
            for state in active_states:
                next_states = state.advance()
                if next_states is True:
                    return True
                else:
                    new_states = new_states.union(next_states)

            active_states = new_states

        #No match
        return False



    class Output(object):
        """
        Represents one output slot from a state. The output slots for a state are created
        at initialization, but the slots can be assigned to at state at any time to connect
        states together in the NFA graph.
        """
        def __init__(self, state, next=None):
            self._state = state
            self._next = next

        def set(self, state):
            """
            Assign the next state for this output.
            """
            self._next = state

        @property
        def next(self):
            """
            The assigned next state for this output. ``None`` if the output is unassigned,
            termed a "dangling" output.
            """
            return self._next

        def dangling(self):
            """
            Returns ``True`` if and only if the `next` state is assigned as ``None``,
            ``False`` otherwise.
            """
            return self._next is None


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
            state = State(c, None)
            frag = Fragment(state)
            stack.append(frag)


    stack_length = len(stack)
    if stack_length == 1:
        nfa = stack[0]
        match = State.Match()
        for op in nfa.outputs:
            op.set(match)
        return nfa

    elif stack_length > 1:
        raise Exception('Invalid expression, multiple fragments left on the stack.')

    else:
        raise Exception('Empty expression, nothing left on the stack.')


if __name__ == '__main__':
    
    import sys


    frag = postfix_to_nfa('ab|')
    pattern = frag.enter

    frag.enter.print_chain(sys.stdout)
    print ''

    print pattern.match("a")
    


