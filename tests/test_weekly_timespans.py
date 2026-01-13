import unittest
import sys
import os

# Add project root to path so we can import pyrri
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyrri.weekly_timespans import WeeklyTimespans, TimePoint, TimeSpan


class TestWeeklyTimespans(unittest.TestCase):
    def test_timepoint_validation(self):
        with self.assertRaises(ValueError):
            TimePoint(7, 0, 0)  # Invalid weekday
        with self.assertRaises(ValueError):
            TimePoint(0, 24, 0)  # Invalid hour
        with self.assertRaises(ValueError):
            TimePoint(0, 0, 60)  # Invalid minute

    def test_timespan_validation(self):
        tp1 = TimePoint(0, 10, 0)
        tp2 = TimePoint(0, 11, 0)

        # Valid
        TimeSpan(tp1, tp2)

        # Invalid: start >= end
        with self.assertRaises(ValueError):
            TimeSpan(tp2, tp1)
        with self.assertRaises(ValueError):
            TimeSpan(tp1, tp1)

    def test_overlap_detection(self):
        # Monday 10:00 - 12:00
        range1 = ((0, 10, 0), (0, 12, 0))
        # Monday 11:00 - 13:00 (Overlaps)
        range2 = ((0, 11, 0), (0, 13, 0))

        with self.assertRaises(ValueError):
            WeeklyTimespans([range1, range2])

    def test_is_in_timespan(self):
        # Mon 10:00-12:00, Tue 14:00-16:00
        ranges = [((0, 10, 0), (0, 12, 0)), ((1, 14, 0), (1, 16, 0))]
        wt = WeeklyTimespans(ranges)

        # Inside first span
        self.assertTrue(wt.is_in_timespan(0, 11, 0))
        # Boundary check (inclusive start)
        self.assertTrue(wt.is_in_timespan(0, 10, 0))
        # Boundary check (exclusive end)
        self.assertFalse(wt.is_in_timespan(0, 12, 0))

        # Inside second span
        self.assertTrue(wt.is_in_timespan(1, 15, 30))

        # Outside
        self.assertFalse(wt.is_in_timespan(0, 9, 59))
        self.assertFalse(wt.is_in_timespan(2, 10, 0))

    def test_sorting(self):
        # Input in reverse order
        ranges = [((1, 14, 0), (1, 16, 0)), ((0, 10, 0), (0, 12, 0))]
        wt = WeeklyTimespans(ranges)

        self.assertEqual(wt.spans[0].start.weekday, 0)
        self.assertEqual(wt.spans[1].start.weekday, 1)

        # Verify start_points are also sorted
        self.assertEqual(wt.start_points[0].weekday, 0)
        self.assertEqual(wt.start_points[1].weekday, 1)


if __name__ == "__main__":
    unittest.main()
