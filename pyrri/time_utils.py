from datetime import datetime
import pytz

def get_current_time_info():
    """
    Returns the current day of week (0=Monday, 6=Sunday), hour, and minute
    in the CET/Berlin timezone.
    
    Returns:
        tuple: (day_of_week, hour, minute)
    """
    berlin_tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(berlin_tz)
    
    return now.weekday(), now.hour, now.minute
