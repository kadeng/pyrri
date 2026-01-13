from dataclasses import dataclass
from typing import List, Tuple
import bisect

@dataclass(order=True, frozen=True)
class TimePoint:
    weekday: int  # 0=Monday, 6=Sunday
    hour: int     # 0-23
    minute: int   # 0-59

    def __post_init__(self):
        if not (0 <= self.weekday <= 6):
            raise ValueError("Weekday must be between 0 and 6")
        if not (0 <= self.hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
        if not (0 <= self.minute <= 59):
            raise ValueError("Minute must be between 0 and 59")

    def to_minutes(self) -> int:
        """Converts the time point to total minutes from the start of the week (Monday 00:00)."""
        return self.weekday * 24 * 60 + self.hour * 60 + self.minute

@dataclass(frozen=True)
class TimeSpan:
    start: TimePoint
    end: TimePoint

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("Start time must be strictly before end time")

    def contains(self, tp: TimePoint) -> bool:
        return self.start <= tp < self.end

    def overlaps(self, other: 'TimeSpan') -> bool:
        return max(self.start, other.start) < min(self.end, other.end)
    
    # Make TimeSpan comparable based on start time for bisect
    def __lt__(self, other):
        if isinstance(other, TimeSpan):
            return self.start < other.start
        # Allow comparison with TimePoint for bisect_right
        if isinstance(other, TimePoint):
            return self.start < other
        return NotImplemented

class WeeklyTimespans:
    def __init__(self, ranges: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]):
        """
        Initialize with a list of time ranges.
        Each range is a tuple: ((start_day, start_hour, start_min), (end_day, end_hour, end_min))
        """
        self.spans: List[TimeSpan] = []
        for start_tuple, end_tuple in ranges:
            start = TimePoint(*start_tuple)
            end = TimePoint(*end_tuple)
            new_span = TimeSpan(start, end)
            self._add_span(new_span)
        
        # Sort spans by start time
        self.spans.sort(key=lambda s: s.start)
        
        # Create a list of start points for bisect
        self.start_points = [span.start for span in self.spans]

    def _add_span(self, new_span: TimeSpan):
        for span in self.spans:
            if span.overlaps(new_span):
                raise ValueError(f"Overlapping timespans detected: {span} and {new_span}")
        self.spans.append(new_span)

    def is_in_timespan(self, weekday: int, hour: int, minute: int) -> bool:
        """
        Checks if the given time falls into any of the configured timespans.
        """
        current_tp = TimePoint(weekday, hour, minute)
        
        # Find the first span that starts AFTER the current time.
        # The candidate span that *might* contain current_tp is the one immediately before that.
        idx = bisect.bisect_right(self.start_points, current_tp)
        
        if idx == 0:
            # Current time is before the first span starts
            return False
            
        # Check the span at idx - 1
        candidate_span = self.spans[idx - 1]
        return candidate_span.contains(current_tp)
