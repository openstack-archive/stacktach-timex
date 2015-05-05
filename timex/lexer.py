#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2014 Rackspace Hosting.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import sys

import ply.lex

from timex.expression import TimexLexerError


logger = logging.getLogger(__name__)


class TimexLexer(object):
    """Lexing/tokenising for time expressions"""

    def __init__(self, debug=False):
        self.debug = debug
        if not self.__doc__:
            raise TimexLexerError("Docstring information is missing. "
                                  "Timex uses PLY which requires "
                                  "docstrings for configuration.")
        self.lexer = ply.lex.lex(module=self,
                                 debug=self.debug,
                                 errorlog=logger)
        self.lexer.string_value = None
        self.latest_newline = 0

    def input(self, string):
        self.lexer.input(string)

    def token(self):
        token = self.lexer.token()
        if token is None:
            if self.lexer.string_value is not None:
                raise TimexLexerError("Unexpected EOF in expression")
        else:
            token.col = token.lexpos - self.latest_newline
        return token

    reserved_words = {
        'to': 'TO',
        'us': 'MICROSECOND',
        's': 'SECOND',
        'sec': 'SECOND',
        'm': 'MINUTE',
        'min': 'MINUTE',
        'h': 'HOUR',
        'hr': 'HOUR',
        'd': 'DAY',
        'mo': 'MONTH',
        'y': 'YEAR',
        'yr': 'YEAR',
    }

    tokens = ('NUMBER',
              'PLUS',
              'MINUS',
              'REPLACE',
              'RPAREN',
              'LPAREN',
              'VAR',
              'IDENTIFIER') + tuple(set(reserved_words.values()))

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_REPLACE = r'@'
    t_VAR = r'\$'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.reserved_words.get(t.value, 'IDENTIFIER')
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        self.latest_newline = t.lexpos

    t_ignore = ' \t'

    def t_error(self, t):
        raise TimexLexerError('Error on line %s, col %s: Unexpected character:'
                              ' %s ' % (t.lexer.lineno,
                                        t.lexpos - self.latest_newline,
                                        t.value[0]))


if __name__ == '__main__':
    logging.basicConfig()
    lexer = TimexLexer(debug=True)
    lexer.input(sys.stdin.read())
    token = lexer.token()
    while token:
        print('%-20s%s' % (token.value, token.type))
        token = lexer.token()
