#! /usr/bin/env python
# vim: set fileencoding=utf-8: set encoding=utf-8:

import regex

from pea import *

@step
def postfix_pattern_is(pattern):
    world.pattern = pattern
    world.nfa = regex.postfix_to_nfa(pattern)

@step
def input_string_is(string):
    world.input = string

@step
def pattern_matches():
    state = world.nfa.enter
    world.assertTrue(state.match(world.input))

@step
def pattern_does_not_match():
    state = world.nfa.enter
    world.assertFalse(state.match(world.input))

class TestPostfix(TestCase):

    def setup_matching(self, pattern, test):
        Given.postfix_pattern_is(pattern)
        And.input_string_is(test)
        
    def validate_matches(self, pattern, test):
        self.setup_matching(pattern, test)
        Then.pattern_matches()

    def validate_not_matches(self, pattern, test):
        self.setup_matching(pattern, test)
        Then.pattern_does_not_match()

    def test_literal(self):
        self.validate_matches('a', 'a')

    def test_concat(self):
        self.validate_matches('ab.', 'ab')

    def test_alternate(self):
        self.validate_matches('ab|', 'a')
        self.validate_matches('ab|', 'b')

    def test_zero_or_one(self):
        self.validate_matches('a?', 'a')
        self.validate_matches('a?', 'b')
        self.validate_not_matches('a?b.', 'aa')

    def test_zero_or_more(self):
        self.validate_matches('a*', '')
        self.validate_matches('a*', 'a')
        self.validate_matches('a*', 'aa')
        self.validate_matches('a*', 'aaa')
        self.validate_matches('a*', 'aaab')

    def test_one_or_more(self):
        self.validate_matches('a+', 'a')
        self.validate_matches('a+', 'aa')
        self.validate_matches('a+', 'aaa')
        self.validate_matches('a+', 'aaaaaaaaa')
        self.validate_matches('a+b.', 'ab')
        self.validate_matches('a+b.', 'aaaaaab')
        self.validate_not_matches('a+b.', 'b')

