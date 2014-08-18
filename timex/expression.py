import logging
import datetime
import abc
import six


logger = logging.getLogger(__name__)


class TimexError(Exception):
    pass


class TimexLexerError(TimexError):
    pass


class TimexParserError(TimexError):
    pass


class TimexExpressionError(TimexError):
    pass


@six.add_metaclass(abc.ABCMeta)
class TimeMatcher(object):

    _allow_ambig_duration = False

    @abc.abstractmethod
    def match(self, dt):
        """Does a specific datetime match this?"""

    @abc.abstractmethod
    def __add__(self, other):
        """Add a duration"""

    @abc.abstractmethod
    def __sub__(self, other):
        """Subtract a duration"""

    @abc.abstractmethod
    def __mod__(self, other):
        """Implements the replace operation with a duration"""

    def total_seconds(self):
        return 0

    @property
    def is_range(self):
        return False

    def __nonzero__(self):
        return True

    def __contains__(self, other):
        return self.match(other)

    def _check_duration(self, duration):
        if isinstance(duration, Duration):
            if ((duration.ambiguous and self._allow_ambig_duration)
                or not duration.ambiguous):
                return True
        raise TimexExpressionError("Invalid duration for time operation")


    def _dt_replace(self, dt, duration):
        return dt.replace(**duration.as_dict)

    def _dt_add(self, dt, duration):
        d = duration.as_dict
        months = d.pop('month', 0)
        years = d.pop('year', 0)
        if d:
            delta = datetime.timedelta(**dict((k+"s",val) for k, val in d.items()))
            dt = dt + delta
        if months:
            newmonth = dt.month + months
            years += (newmonth - 1) // 12
            newmonth = ((newmonth-1) % 12) + 1
            dt = dt.replace(month=newmonth)
        if years:
            dt = dt.replace(year=(dt.year+years))
        return dt

    def _dt_sub(self, dt, duration):
        d = duration.as_dict
        months = d.pop('month', 0)
        years = d.pop('year', 0)
        if d:
            delta = datetime.timedelta(**dict((k+"s",val) for k, val in d.items()))
            dt = dt - delta
        if months:
            newmonth = dt.month - months
            years -= (newmonth - 1) // 12
            newmonth = ((newmonth-1) % 12) + 1
            dt = dt.replace(month=newmonth)
        if years:
            dt = dt.replace(year=(dt.year-years))
        return dt


class Timestamp(TimeMatcher):
    """This is a wrapper on a datetime that has the same
       interface as TimeRange"""

    def __init__(self, dt):
        self.timestamp = dt

    @property
    def begin(self):
        return self.timestamp

    @property
    def end(self):
        return self.timestamp

    def match(self, dt):
        return self.timestamp == dt

    def __add__(self, other):
        self._check_duration(other)
        return Timestamp(self._dt_add(self.timestamp, other))

    def __sub__(self, other):
        self._check_duration(other)
        return Timestamp(self._dt_sub(self.timestamp, other))

    def __mod__(self, other):
        self._check_duration(other)
        return Timestamp(self._dt_replace(self.timestamp, other))

    def __repr__(self):
        return "Timestamp for %r" % self.timestamp


class TimeRange(TimeMatcher):

    _allow_ambig_duration = True

    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    @property
    def timestamp(self):
        return self.begin

    def total_seconds(self):
        delta = self.end - self.begin
        return delta.seconds + (delta.days * 24 * 3600) + (delta.microseconds * 1e-6)

    def __nonzero__(self):
        return self.total_seconds() > 0

    @property
    def is_range(self):
        return True

    def match(self, dt):
        """TimeRanges match datetimes from begin (inclusive) to end (exclusive)"""
        return dt >= self.begin and dt < self.end

    def __add__(self, other):
        self._check_duration(other)
        duration = other.in_context(self)
        begin = self._dt_add(self.begin, duration)
        end = self._dt_add(self.end, duration)
        return TimeRange(begin, end)

    def __sub__(self, other):
        self._check_duration(other)
        duration = other.in_context(self)
        begin = self._dt_sub(self.begin, duration)
        end = self._dt_sub(self.end, duration)
        return TimeRange(begin, end)

    def __mod__(self, other):
        self._check_duration(other)
        duration = other.in_context(self)
        begin = self._dt_replace(self.begin, duration)
        end = self._dt_replace(self.end, duration)
        return TimeRange(begin, end)

    def next(self):
        begin = self.end
        end = self._dt_add(begin, Duration(second=self.total_seconds()))
        return TimeRange(begin, end)

    def prev(self):
        end = self.begin
        begin = self._dt_sub(end, Duration(second=self.total_seconds()))
        return TimeRange(begin, end)

    def __repr__(self):
        return "TimeRange from %r to %r" % (self.begin, self.end)

    def pin(self, dt, unit):
        return PinnedTimeRange(self.begin, self.end, dt, unit)


class PinnedTimeRange(TimeRange):

    def __init__(self, begin, end, pinned_to, unit):
        super(PinnedTimeRange, self).__init__(begin, end)
        self.pinned_to = pinned_to
        self.unit = unit
        self.duration = Duration(**{unit: 1})

    def _pin_adjust(self, time_range):
        if self.pinned_to in time_range:
            return time_range.pin(self.pinned_to, self.unit)
        while time_range.begin > self.pinned_to:
            time_range = time_range.prev()
        while time_range.end <= self.pinned_to:
            time_range = time_range.next()
        return time_range.pin(self.pinned_to, self.unit)

    def __add__(self, other):
        time_range = super(PinnedTimeRange, self).__add__(other)
        if other < self.duration:
            return self._pin_adjust(time_range)
        return self.time_range

    def __sub__(self, other):
        time_range = super(PinnedTimeRange, self).__sub__(other)
        if other < self.duration:
            return self._pin_adjust(time_range)
        return self.time_range

    def __mod__(self, other):
        time_range = super(PinnedTimeRange, self).__mod__(other)
        if other < self.duration:
            return self._pin_adjust(time_range)
        return self.time_range

    def __repr__(self):
        return "PinnedTimeRange from %r to %r. Pinned to %s(%r)" % (self.begin, self.end, self.unit, self.pinned_to)


class Environment(dict):

    def time_func_hour(self, timestamp):
        dt = timestamp.timestamp
        begin = dt.replace(minute=0, second=0, microsecond=0)
        end = begin + datetime.timedelta(hours=1)
        return PinnedTimeRange(begin, end, dt, 'hour')

    def time_func_day(self, timestamp):
        dt = timestamp.timestamp
        begin = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = begin + datetime.timedelta(days=1)
        return PinnedTimeRange(begin, end, dt, 'day')

    def time_func_month(self, timestamp):
        dt = timestamp.timestamp
        begin = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = Timestamp(begin) + Duration(month=1)
        return PinnedTimeRange(begin, end.timestamp, dt, 'month')

    def time_func_year(self, timestamp):
        dt = timestamp.timestamp
        begin = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = Timestamp(begin) + Duration(year=1)
        return PinnedTimeRange(begin, end.timestamp, dt, 'year')


@six.add_metaclass(abc.ABCMeta)
class TimeExpression(object):

    @abc.abstractmethod
    def apply(self, env):
        """Apply the expression to a given set of arguments.

        :param env: a dictionary-like object. expression functions should be methods
             on this object with names beginning with 'time_func_'
        returns: TimeMatcher instance
        """

    def __call__(self, **kw):
        env = Environment()
        env.update(kw)
        if 'timestamp' not in env:
            env['timestamp'] = datetime.datetime.utcnow()
        return self.apply(env)


class TimeRangeExpression(TimeExpression):
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.begin, self.end)

    def apply(self, env):
        begin = self.begin.apply(env)
        end = self.end.apply(env)
        return TimeRange(begin.timestamp, end.timestamp)


class TimeRangeFunction(TimeRangeExpression):
    def __init__(self, func_name, expr=None):
        self.func_name = func_name
        if expr is None:
            expr = Variable('timestamp')
        self.expr = expr

    def __repr__(self):
        return '%s %s(%r)' % (self.__class__.__name__, self.func_name, self.expr)

    def apply(self, env):
        arg = self.expr.apply(env)
        try:
            func = getattr(env, "time_func_%s" % self.func_name)
        except AttributeError:
            raise TimexExpressionError("Unknown Function %s" % self.func_name)
        return func(arg)


class Variable(TimeExpression):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "%s (%s)" % (self.__class__.__name__, self.name)

    def apply(self, env):
        if self.name not in env:
            raise TimexExpressionError("Variable %s not defined" % self.name)
        return Timestamp(env[self.name])


class Operation(TimeExpression):
    def __init__(self, expr, duration):
        if duration.ambiguous and not isinstance(expr, TimeRangeExpression):
            raise TimexParserError("Durations must have unit for "
                                   "TimestampExpressions")
        self.expr = expr
        self.duration = duration

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.expr, self.duration)


class Replace(Operation):

    def apply(self, env):
        val = self.expr.apply(env)
        return val % self.duration


class Plus(Operation):

    def apply(self, env):
        val = self.expr.apply(env)
        return val + self.duration


class Minus(Operation):

    def apply(self, env):
        val = self.expr.apply(env)
        return val - self.duration


class Duration(object):

    UNIT_SIZES = {'year': 365*24*60*60,
                  'month': 28*24*60*60,
                  'day': 24*60*60,
                  'hour': 60*60,
                  'minute': 60,
                  'second': 1,
                  'microsecond': 1e-6}
    UNITS = ('year',
             'month',
             'day',
             'hour',
             'minute',
             'second',
             'microsecond',)

    def __init__(self, year=None, month=None, day=None, hour=None,
                 minute=None, second=None, microsecond=None, unknown=None):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond
        self.unknown = unknown

    @property
    def ambiguous(self):
        return self.unknown is not None

    @property
    def as_dict(self):
        d = dict()
        for unit in self.UNITS:
            val = getattr(self, unit)
            if val is not None:
                d[unit] = val
        if self.ambiguous:
            d['unknown'] = self.unknown
        return d

    def in_context(self, timerange):
        if not self.ambiguous:
            return self
        d = abs(timerange.total_seconds())
        if d >= self.UNIT_SIZES['year']:
            unit = 'month'
        elif d >= self.UNIT_SIZES['month']:
            unit = 'day'
        elif d >= self.UNIT_SIZES['day']:
            unit = 'hour'
        elif d >= self.UNIT_SIZES['hour']:
            unit = 'minute'
        elif d >= self.UNIT_SIZES['minute']:
            unit = 'second'
        else:
            unit = microsecond
        vals = self.as_dict
        del vals['unknown']
        if unit in vals:
            vals[unit] += self.unknown
        else:
            vals[unit] = self.unknown
        return Duration(**vals)

    def __add__(self, other):
        result = self.as_dict
        o = other.as_dict
        for unit in o:
            if unit in result:
                result[unit] += o[unit]
            else:
                result[unit] = o[unit]
        return Duration(**result)

    def __repr__(self):
        return '%s %s' % (self.__class__.__name__, str(self.as_dict))

    def __gt__(self, other):
        for unit in self.UNITS:
            our_val = getattr(self, unit)
            other_val = getattr(other, unit)
            if our_val is not None and other_val is not None:
                return our_val > other_val
            elif our_val is not None and other_val is None:
                return True
            elif our_val is None and other_val is not None:
                return False
        return False

    def __lt__(self, other):
        for unit in self.UNITS:
            our_val = getattr(self, unit)
            other_val = getattr(other, unit)
            if our_val is not None and other_val is not None:
                return our_val < other_val
            elif our_val is not None and other_val is None:
                return False
            elif our_val is None and other_val is not None:
                return True
        return False

    def __eq__(self, other):
        for unit in self.UNITS:
            our_val = getattr(self, unit)
            other_val = getattr(other, unit)
            if our_val != other_val:
                return False
        return True

