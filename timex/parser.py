import sys, os
import logging

import ply.yacc

from timex.lexer import TimexLexer
from timex.expression import TimexParserError
from timex.expression import Replace, Plus, Minus
from timex.expression import Duration, Variable
from timex.expression import TimeRangeFunction, TimeRangeExpression



"""
Parse Time Expression:

BNF:
--------------------------

time_expression : timerange_expression
                | timestamp_expression

timerange_expression : timestamp_expression TO timestamp_expression
                     | timestamp_expression PLUS duration
                     | timestamp_expression MINUS duration
                     | timerange_expression REPLACE duration
                     | LPAREN timerange_expression RPAREN
                     | range_function

timestamp_expression : timestamp_expression PLUS duration
                     | timestamp_expression MINUS duration
                     | timestamp_expression REPLACE duration
                     | LPAREN timestamp_expression RPAREN
                     | variable

range_function : IDENTIFIER LPAREN timestamp_expression RPAREN
               | IDENTIFIER

variable : VAR IDENTIFIER

duration : duration duration
         | NUMBER unit
         | NUMBER

unit : SECOND
     | MICROSECOND
     | MINUTE
     | HOUR
     | DAY
     | MONTH
     | YEAR

"""



logger = logging.getLogger(__name__)


def parse(string):
    return TimexParser().parse(string)


class TimexParser(object):
    """ LALR parser for time expression mini-language."""
    tokens = TimexLexer.tokens

    def __init__(self, debug=False, lexer_class=None, start='time_expression'):
        self.debug = debug
        self.start = start
        if not self.__doc__:
            raise TimexParserError("Docstring information is missing. "
                    "Timex uses PLY which requires docstrings for "
                    "configuration.")
        self.lexer_class = lexer_class or TimexLexer

    def _parse_table(self):
        tabdir = os.path.dirname(__file__)
        try:
            module_name = os.path.splitext(os.path.split(__file__)[1])[0]
        except:
            module_name = __name__
        table_module = '_'.join([module_name, self.start, 'parsetab'])
        return (tabdir, table_module)

    def parse(self, string):
        lexer = self.lexer_class(debug=self.debug)

        tabdir, table_module = self._parse_table()
        parser = ply.yacc.yacc(module=self,
                               debug=self.debug,
                               tabmodule = table_module,
                               outputdir = tabdir,
                               write_tables=0,
                               start = self.start,
                               errorlog = logger)

        return parser.parse(string, lexer=lexer)

    precedence = [
        ('left', 'TO'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'REPLACE'),
        ('right', 'VAR'),
    ]

    def p_error(self, t):
        raise TimexParserError('Parse error at %s:%s near token %s (%s)' %
                                (t.lineno, t.col, t.value, t.type))

    def p_time_expression(self, p):
        """time_expression : timerange_expression
                           | timestamp_expression
        """
        p[0] = p[1]

    def p_timerange_to(self, p):
        'timerange_expression : timestamp_expression TO timestamp_expression'
        p[0] = TimeRangeExpression(p[1], p[3])

    def p_timerange_replace(self, p):
        """timerange_expression : timerange_expression REPLACE duration"""
        p[0] = Replace(p[1], p[3])

    def p_timerange_plus(self, p):
        """timerange_expression : timerange_expression PLUS duration"""
        p[0] = Plus(p[1], p[3])

    def p_timerange_minus(self, p):
        """timerange_expression : timerange_expression MINUS duration"""
        p[0] = Minus(p[1], p[3])

    def p_timerange_parens(self, p):
        """timerange_expression : LPAREN timerange_expression RPAREN"""
        p[0] = p[2]

    def p_timerange_function(self, p):
        """timerange_expression : range_function"""
        p[0] = p[1]

    def p_timestamp_replace(self, p):
        """timestamp_expression : timestamp_expression REPLACE duration"""
        p[0] = Replace(p[1], p[3])

    def p_timestamp_plus(self, p):
        """timestamp_expression : timestamp_expression PLUS duration"""
        p[0] = Plus(p[1], p[3])

    def p_timestamp_minus(self, p):
        """timestamp_expression : timestamp_expression MINUS duration"""
        p[0] = Minus(p[1], p[3])

    def p_timestamp_parens(self, p):
        """timestamp_expression : LPAREN timestamp_expression RPAREN"""
        p[0] = p[2]

    def p_timestamp_variable(self, p):
        """timestamp_expression : variable"""
        p[0] = p[1]

    def p_range_function_expr(self, p):
        """range_function : IDENTIFIER LPAREN timestamp_expression RPAREN"""
        p[0] = TimeRangeFunction(p[1], p[3])

    def p_range_function(self, p):
        """range_function : IDENTIFIER"""
        p[0] = TimeRangeFunction(p[1])

    def p_varible(self, p):
        'variable : VAR IDENTIFIER'
        p[0] = Variable(p[2])

    def p_duration_unit(self, p):
        """duration : NUMBER unit"""
        p[0] = Duration(**{p[2]: p[1]})

    def p_duration_number(self, p):
        """duration : NUMBER"""
        p[0] = Duration(unknown=p[1])

    def p_duration_duration(self, p):
        """duration : duration duration"""
        p[0] = p[1] + p[2]

    def p_unit(self, p):
        """unit : SECOND
                | MICROSECOND
                | MINUTE
                | HOUR
                | DAY
                | MONTH
                | YEAR"""
        unit = TimexLexer.reserved_words[p[1]]
        unit = unit.lower()
        p[0] = unit
