import unittest
from unittest.mock import patch
from datetime import datetime
import pytz
import sys
import os

# Add project root to path so we can import pyrri
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyrri import time_utils


class TestTimeUtils(unittest.TestCase):
    @patch("pyrri.time_utils.datetime")
    def test_get_current_time_info(self, mock_datetime):
        # Create a fixed time in Berlin timezone
        berlin_tz = pytz.timezone("Europe/Berlin")
        # Monday (0), 14:30
        fixed_time = berlin_tz.localize(datetime(2023, 10, 23, 14, 30, 0))

        # Mock datetime.now to return our fixed time when called with timezone
        mock_datetime.now.return_value = fixed_time

        day, hour, minute = time_utils.get_current_time_info()

        self.assertEqual(day, 0)  # Monday
        self.assertEqual(hour, 14)
        self.assertEqual(minute, 30)

        # Verify it was called with the correct timezone
        args, _ = mock_datetime.now.call_args
        self.assertEqual(str(args[0]), "Europe/Berlin")


if __name__ == "__main__":
    unittest.main()
