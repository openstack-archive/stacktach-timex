import datetime

#for Python2.6 compatability.
import unittest2 as unittest
import mock
import six

from timex import expression


class TestTimestamp(unittest.TestCase):

    def setUp(self):
        super(TestTimestamp, self).setUp()
        self.dt = datetime.datetime(2014, 8, 1, 2 ,10, 23, 550)
        self.other_dt = datetime.datetime(2014, 8, 7, 2 ,0, 0, 0)
        self.timestamp = expression.Timestamp(self.dt)

    def test_timestamp_properties(self):
        self.assertEqual(self.dt, self.timestamp.begin)
        self.assertEqual(self.dt, self.timestamp.end)
        self.assertEqual(self.dt, self.timestamp.timestamp)

    def test_match(self):
        self.assertTrue(self.timestamp.match(self.dt))
        self.assertFalse(self.timestamp.match(self.other_dt))

    def test_in(self):
        self.assertTrue(self.dt in self.timestamp)
        self.assertFalse(self.other_dt in self.timestamp)

    def test_add(self):
        expected = datetime.datetime(2014, 8, 1, 2, 10, 23, 560)
        res = self.timestamp + expression.Duration(microsecond=10)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 2, 10, 33, 550)
        res = self.timestamp + expression.Duration(second=10)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 2, 17, 23, 550)
        res = self.timestamp + expression.Duration(minute=7)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 3, 10, 23, 550)
        res = self.timestamp + expression.Duration(hour=1)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 3, 2, 10, 23, 550)
        res = self.timestamp + expression.Duration(day=2)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2015, 2, 1, 2, 10, 23, 550)
        res = self.timestamp + expression.Duration(month=6)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2017, 8, 1, 2, 10, 23, 550)
        res = self.timestamp + expression.Duration(year=3)
        self.assertEqual(res.timestamp, expected)

    def test_sub(self):
        expected = datetime.datetime(2014, 8, 1, 2, 10, 23, 540)
        res = self.timestamp - expression.Duration(microsecond=10)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 2, 10, 13, 550)
        res = self.timestamp - expression.Duration(second=10)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 2, 3, 23, 550)
        res = self.timestamp - expression.Duration(minute=7)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 1, 10, 23, 550)
        res = self.timestamp - expression.Duration(hour=1)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 7, 30, 2, 10, 23, 550)
        res = self.timestamp - expression.Duration(day=2)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 2, 1, 2, 10, 23, 550)
        res = self.timestamp - expression.Duration(month=6)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2011, 8, 1, 2, 10, 23, 550)
        res = self.timestamp - expression.Duration(year=3)
        self.assertEqual(res.timestamp, expected)

    def test_replace(self):
        expected = datetime.datetime(2014, 8, 2, 2, 10, 23, 550)
        res = self.timestamp % expression.Duration(day=2)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 6, 1, 2, 10, 23, 550)
        res = self.timestamp % expression.Duration(month=6)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2017, 8, 1, 2, 10, 23, 550)
        res = self.timestamp % expression.Duration(year=2017)
        self.assertEqual(res.timestamp, expected)

        expected = datetime.datetime(2014, 8, 1, 0, 0, 0, 0)
        res = self.timestamp % expression.Duration(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(res.timestamp, expected)

    def test_handle_ambig_duration(self):
        d = expression.Duration(hour=10, unknown=2)
        self.assertRaises(expression.TimexExpressionError, self.timestamp.__add__, d)
        self.assertRaises(expression.TimexExpressionError, self.timestamp.__sub__, d)
        self.assertRaises(expression.TimexExpressionError, self.timestamp.__mod__, d)

    def test_total_seconds(self):
        self.assertFalse(self.timestamp.is_range)
        self.assertEqual(self.timestamp.total_seconds(), 0)


class TestTimeRange(unittest.TestCase):

    def setUp(self):
        super(TestTimeRange, self).setUp()
        self.begin_dt = datetime.datetime(2014, 8, 1, 2 ,10, 23, 550)
        self.end_dt = datetime.datetime(2014, 8, 2, 2 ,10, 23, 550)
        self.middle_dt = datetime.datetime(2014, 8, 1, 17 ,30, 10, 25)
        self.other_dt = datetime.datetime(2014, 8, 7, 2 ,0, 0, 0)
        self.timerange = expression.TimeRange(self.begin_dt, self.end_dt)

    def test_timerange_properties(self):
        self.assertEqual(self.begin_dt, self.timerange.begin)
        self.assertEqual(self.end_dt, self.timerange.end)
        self.assertEqual(self.begin_dt, self.timerange.timestamp)

    def test_match(self):
        #ranges include the beginning.
        self.assertTrue(self.timerange.match(self.begin_dt))
        self.assertTrue(self.timerange.match(self.middle_dt))

        #ranges *don`t* include the end.
        self.assertFalse(self.timerange.match(self.end_dt))
        self.assertFalse(self.timerange.match(self.other_dt))

    def test_in(self):
        #ranges include the beginning.
        self.assertTrue(self.begin_dt in self.timerange)
        self.assertTrue(self.middle_dt in self.timerange)

        #ranges *don`t* include the end.
        self.assertFalse(self.end_dt in self.timerange)
        self.assertFalse(self.other_dt in self.timerange)

    def test_add(self):
        expected_begin = datetime.datetime(2014, 8, 1, 2, 10, 23, 560)
        expected_end = datetime.datetime(2014, 8, 2, 2, 10, 23, 560)
        res = self.timerange + expression.Duration(microsecond=10)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 2, 10, 33, 550)
        expected_end = datetime.datetime(2014, 8, 2, 2, 10, 33, 550)
        res = self.timerange + expression.Duration(second=10)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 2, 17, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 2, 17, 23, 550)
        res = self.timerange + expression.Duration(minute=7)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 3, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 3, 10, 23, 550)
        res = self.timerange + expression.Duration(hour=1)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 3, 2, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 4, 2, 10, 23, 550)
        res = self.timerange + expression.Duration(day=2)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2015, 2, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2015, 2, 2, 2, 10, 23, 550)
        res = self.timerange + expression.Duration(month=6)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2017, 8, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2017, 8, 2, 2, 10, 23, 550)
        res = self.timerange + expression.Duration(year=3)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

    def test_sub(self):
        expected_begin = datetime.datetime(2014, 8, 1, 2, 10, 23, 540)
        expected_end = datetime.datetime(2014, 8, 2, 2, 10, 23, 540)
        res = self.timerange - expression.Duration(microsecond=10)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 2, 10, 13, 550)
        expected_end = datetime.datetime(2014, 8, 2, 2, 10, 13, 550)
        res = self.timerange - expression.Duration(second=10)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 2, 3, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 2, 3, 23, 550)
        res = self.timerange - expression.Duration(minute=7)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 1, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 1, 10, 23, 550)
        res = self.timerange - expression.Duration(hour=1)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 7, 30, 2, 10, 23, 550)
        expected_end = datetime.datetime(2014, 7, 31, 2, 10, 23, 550)
        res = self.timerange - expression.Duration(day=2)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 2, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2014, 2, 2, 2, 10, 23, 550)
        res = self.timerange - expression.Duration(month=6)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2011, 8, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2011, 8, 2, 2, 10, 23, 550)
        res = self.timerange - expression.Duration(year=3)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)


    def test_replace(self):
        expected_begin = datetime.datetime(2014, 8, 1, 6, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 6, 10, 23, 550)
        res = self.timerange % expression.Duration(hour=6)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 6, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2014, 6, 2, 2, 10, 23, 550)
        res = self.timerange % expression.Duration(month=6)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2017, 8, 1, 2, 10, 23, 550)
        expected_end = datetime.datetime(2017, 8, 2, 2, 10, 23, 550)
        res = self.timerange % expression.Duration(year=2017)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 0, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 2, 0, 0, 0, 0)
        res = self.timerange % expression.Duration(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

    def test_handle_ambig_duration(self):
        d = expression.Duration(unknown=1)

        expected_begin = datetime.datetime(2014, 8, 1, 3, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 3, 10, 23, 550)
        res = self.timerange + d
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 1, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 1, 10, 23, 550)
        res = self.timerange - d
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 1, 10, 23, 550)
        expected_end = datetime.datetime(2014, 8, 2, 1, 10, 23, 550)
        res = self.timerange % d
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

    def test_total_seconds(self):
        self.assertTrue(self.timerange.is_range)
        self.assertEqual(self.timerange.total_seconds(), 24*60*60)


class TestPinnedTimeRange(unittest.TestCase):

    def setUp(self):
        super(TestPinnedTimeRange, self).setUp()
        self.begin_dt = datetime.datetime(2014, 8, 1, 1, 0, 0, 0)
        self.end_dt = datetime.datetime(2014, 8, 2, 1, 0, 0, 0)
        self.middle_dt = datetime.datetime(2014, 8, 1, 17 ,30, 10, 25)
        self.other_dt = datetime.datetime(2014, 8, 7, 2 ,0, 0, 0)
        self.timerange = expression.PinnedTimeRange(self.begin_dt,
                                                    self.end_dt,
                                                    self.middle_dt,
                                                    'day')

    def test_add(self):
        expected_begin = datetime.datetime(2014, 8, 1, 2, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 2, 2, 0, 0, 0)
        res = self.timerange + expression.Duration(hour=1)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 7, 31, 19, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 1, 19, 0, 0, 0)
        res = self.timerange + expression.Duration(hour=18)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

    def test_sub(self):
        expected_begin = datetime.datetime(2014, 8, 1, 0, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 2, 0, 0, 0, 0)
        res = self.timerange - expression.Duration(hour=1)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 8, 1, 17, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 2, 17, 0, 0, 0)
        res = self.timerange - expression.Duration(hour=8)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

    def test_replace(self):
        expected_begin = datetime.datetime(2014, 8, 1, 2, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 2, 2, 0, 0, 0)
        res = self.timerange % expression.Duration(hour=2)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)

        expected_begin = datetime.datetime(2014, 7, 31, 18, 0, 0, 0)
        expected_end = datetime.datetime(2014, 8, 1, 18, 0, 0, 0)
        res = self.timerange % expression.Duration(hour=18)
        self.assertEqual(res.begin, expected_begin)
        self.assertEqual(res.end, expected_end)


class TestDuration(unittest.TestCase):

    def setUp(self):
        super(TestDuration, self).setUp()
        self.second = expression.Duration(second=1)
        self.minute = expression.Duration(minute=1)
        self.hour = expression.Duration(hour=1)
        self.day = expression.Duration(day=1)
        self.month = expression.Duration(month=1)
        self.year = expression.Duration(year=1)

    def test_gt(self):
        self.assertTrue(self.hour > self.second)
        self.assertFalse(self.second > self.hour)

    def test_lt(self):
        self.assertTrue(self.second < self.hour)
        self.assertFalse(self.hour < self.second)

    def test_add(self):
        d = self.second + self.hour + self.day
        self.assertEqual(d.second, 1)
        self.assertEqual(d.hour, 1)
        self.assertEqual(d.day, 1)
        self.assertIsNone(d.microsecond)
        self.assertIsNone(d.minute)
        self.assertIsNone(d.month)
        self.assertIsNone(d.year)
        self.assertIsNone(d.unknown)

    def test_as_dict(self):
        d = expression.Duration(second=1, hour=1, day=1)
        dd = d.as_dict
        for unit in ('second', 'hour', 'day'):
            self.assertIn(unit, dd)
            self.assertEqual(dd[unit], 1)
        for unit in ('microsecond', 'minute', 'month', 'year', 'unknown'):
            self.assertNotIn(unit, dd)

