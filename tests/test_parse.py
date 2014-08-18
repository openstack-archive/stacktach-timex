import datetime

#for Python2.6 compatability.
import unittest2 as unittest
import mock
import six

import timex


class TestParse(unittest.TestCase):

    def setUp(self):
        super(TestParse, self).setUp()
        self.dt = datetime.datetime(2014, 8, 1, 2 ,10, 23, 550)
        self.other_dt = datetime.datetime(2014, 8, 7, 3, 20, 0, 0)

    def test_var(self):
        exp = timex.parse("$test_thingy")
        t = exp(test_thingy=self.dt)
        self.assertFalse(t.is_range)
        self.assertEqual(t.timestamp, self.dt)

    def test_timestamp_add(self):
        result = datetime.datetime(2014, 8, 2, 4 ,10, 23, 550)
        exp = timex.parse("$test_thingy + 1d 2h")
        t = exp(test_thingy=self.dt)
        self.assertFalse(t.is_range)
        self.assertEqual(t.timestamp, result)

    def test_timestamp_sub(self):
        result = datetime.datetime(2014, 7, 31, 0 ,10, 23, 550)
        exp = timex.parse("$test_thingy - 1d 2h")
        t = exp(test_thingy=self.dt)
        self.assertFalse(t.is_range)
        self.assertEqual(t.timestamp, result)

    def test_timestamp_replace(self):
        result = datetime.datetime(2014, 8, 7, 6 ,10, 23, 550)
        exp = timex.parse("$test_thingy @ 7d 6h")
        t = exp(test_thingy=self.dt)
        self.assertFalse(t.is_range)
        self.assertEqual(t.timestamp, result)

    def test_timerange(self):
        exp = timex.parse("$test_thingy to $other")
        t = exp(test_thingy=self.dt, other=self.other_dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, self.dt)
        self.assertEqual(t.end, self.other_dt)

    def test_timerange_add(self):
        result_begin = datetime.datetime(2014, 8, 2, 4 ,10, 23, 550)
        result_end = datetime.datetime(2014, 8, 8, 5, 20, 0, 0)
        exp = timex.parse("($test_thingy to $other) + 1d 2h")
        t = exp(test_thingy=self.dt, other=self.other_dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_timerange_sub(self):
        result_begin = datetime.datetime(2014, 7, 31, 0 ,10, 23, 550)
        result_end = datetime.datetime(2014, 8, 6, 1, 20, 0, 0)
        exp = timex.parse("($test_thingy to $other) - 1d 2h")
        t = exp(test_thingy=self.dt, other=self.other_dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_timerange_replace(self):
        result_begin = datetime.datetime(2014, 8, 1, 6, 10, 23, 550)
        result_end = datetime.datetime(2014, 8, 7, 6, 20, 0, 0)
        exp = timex.parse("($test_thingy to $other) @ 6h")
        t = exp(test_thingy=self.dt, other=self.other_dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_special_range(self):
        result_begin = datetime.datetime(2014, 8, 1, 0, 0, 0, 0)
        result_end = datetime.datetime(2014, 8, 2, 0, 0, 0, 0)
        exp = timex.parse("day($test_thingy)")
        t = exp(test_thingy=self.dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

        exp = timex.parse("day")
        t = exp(timestamp=self.dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_special_range_wrap_replace(self):
        result_begin = datetime.datetime(2014, 7, 31, 6, 0, 0, 0)
        result_end = datetime.datetime(2014, 8, 1, 6, 0, 0, 0)
        exp = timex.parse("day @ 6h")
        t = exp(timestamp=self.dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_special_range_wrap_add(self):
        result_begin = datetime.datetime(2014, 7, 31, 6, 0, 0, 0)
        result_end = datetime.datetime(2014, 8, 1, 6, 0, 0, 0)
        exp = timex.parse("day + 6h")
        t = exp(timestamp=self.dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_special_range_wrap_sub(self):
        result_begin = datetime.datetime(2014, 8, 1, 18, 0, 0, 0)
        result_end = datetime.datetime(2014, 8, 2, 18, 0, 0, 0)
        exp = timex.parse("day - 6h")
        t = exp(timestamp=datetime.datetime(2014, 8, 1, 19, 45, 30, 225))
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

    def test_timerange_ambig_duration(self):
        # Ambiguous durations are a bit of a hack to make timex syntax
        # compatable with the (much less flexible) syntax for timeranges
        # used for some OpenStack projects. (mdragon)
        result_begin = datetime.datetime(2014, 8, 1, 2, 0, 0, 0)
        result_end = datetime.datetime(2014, 8, 2, 2, 0, 0, 0)
        exp = timex.parse("day @ 2")
        t = exp(timestamp=self.dt)
        self.assertTrue(t.is_range)
        self.assertEqual(t.begin, result_begin)
        self.assertEqual(t.end, result_end)

