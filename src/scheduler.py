"""
Scheduler Module
Handles optimal upload timing for YouTube Shorts.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadScheduler:
    """Schedule uploads at optimal times for YouTube Shorts."""

    def __init__(self, timezone: str = "America/New_York"):
        self.timezone = pytz.timezone(timezone)
        
        # Optimal upload times for maximum engagement
        # These are based on when most people watch Shorts
        self.optimal_times = [
            "08:00",  # Breakfast time - people checking phones in morning
            "12:00",  # Lunch break - midday scrolling
            "19:00",  # Evening peak - after work/dinner relaxation
        ]

    def get_next_upload_time(self, videos_uploaded_today: int = 0) -> datetime:
        """
        Get the next optimal upload time.
        
        Args:
            videos_uploaded_today: Number of videos already uploaded today
            
        Returns:
            Next scheduled upload time as datetime object
        """
        now = datetime.now(self.timezone)
        
        # If we've already uploaded 3 videos today, schedule for tomorrow
        if videos_uploaded_today >= 3:
            return self.get_first_upload_time_tomorrow()
        
        # Get today's remaining upload times
        remaining_times = self.get_remaining_upload_times_today(now)
        
        if remaining_times and videos_uploaded_today < len(remaining_times):
            # Return the next scheduled time for today
            return remaining_times[videos_uploaded_today]
        else:
            # Schedule for tomorrow's first slot
            return self.get_first_upload_time_tomorrow()

    def get_remaining_upload_times_today(self, now: datetime) -> List[datetime]:
        """
        Get remaining upload times for today.
        
        Args:
            now: Current datetime
            
        Returns:
            List of remaining upload times today
        """
        remaining = []
        
        for time_str in self.optimal_times:
            hour, minute = map(int, time_str.split(":"))
            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Only include future times
            if scheduled_time > now:
                remaining.append(scheduled_time)
        
        return remaining

    def get_first_upload_time_tomorrow(self) -> datetime:
        """
        Get the first upload time for tomorrow.
        
        Returns:
            Tomorrow's first upload time as datetime
        """
        now = datetime.now(self.timezone)
        tomorrow = now + timedelta(days=1)
        
        # Set to first optimal time (8:00 AM)
        hour, minute = map(int, self.optimal_times[0].split(":"))
        first_time = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return first_time

    def should_upload_now(self, videos_uploaded_today: int = 0, tolerance_minutes: int = 30) -> bool:
        """
        Check if it's time to upload now.
        
        Args:
            videos_uploaded_today: Number of videos already uploaded today
            tolerance_minutes: Minutes of tolerance around scheduled time
            
        Returns:
            True if should upload now, False otherwise
        """
        now = datetime.now(self.timezone)
        next_upload = self.get_next_upload_time(videos_uploaded_today)
        
        # Check if we're within tolerance window
        time_diff = abs((next_upload - now).total_seconds()) / 60
        
        if time_diff <= tolerance_minutes:
            logger.info(f"Within upload window! Next scheduled time: {next_upload}")
            return True
        
        return False

    def get_upload_schedule_for_day(self, date: Optional[datetime] = None) -> List[datetime]:
        """
        Get all upload times for a specific day.
        
        Args:
            date: Date to get schedule for (defaults to today)
            
        Returns:
            List of scheduled upload times
        """
        if date is None:
            date = datetime.now(self.timezone)
        
        schedules = []
        for time_str in self.optimal_times:
            hour, minute = map(int, time_str.split(":"))
            scheduled_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            schedules.append(scheduled_time)
        
        return schedules

    def get_time_until_next_upload(self, videos_uploaded_today: int = 0) -> timedelta:
        """
        Get time duration until next upload.
        
        Args:
            videos_uploaded_today: Number of videos already uploaded today
            
        Returns:
            Timedelta until next upload
        """
        now = datetime.now(self.timezone)
        next_upload = self.get_next_upload_time(videos_uploaded_today)
        
        return next_upload - now

    def format_upload_schedule(self) -> str:
        """
        Format upload schedule as a readable string.
        
        Returns:
            Formatted schedule string
        """
        tz_name = self.timezone.zone
        
        schedule = f"Upload Schedule ({tz_name}):\n"
        schedule += "=" * 40 + "\n"
        
        for i, time_str in enumerate(self.optimal_times, 1):
            period = ""
            if i == 1:
                period = "🌅 Breakfast Time"
            elif i == 2:
                period = "☀️ Lunch Break"
            elif i == 3:
                period = "🌙 Evening Peak"
            
            schedule += f"  Video {i}: {time_str} - {period}\n"
        
        schedule += "=" * 40
        return schedule


def is_within_upload_window(timezone: str = "America/New_York", tolerance_minutes: int = 30) -> bool:
    """
    Quick function to check if current time is within an upload window.
    
    Args:
        timezone: User's timezone
        tolerance_minutes: Tolerance in minutes
        
    Returns:
        True if within upload window
    """
    scheduler = UploadScheduler(timezone)
    
    # We'll upload up to 3 videos per day
    # This function just checks if we're in any upload window
    for i in range(3):
        if scheduler.should_upload_now(i, tolerance_minutes):
            return True
    
    return False


if __name__ == "__main__":
    # Test the scheduler
    scheduler = UploadScheduler("America/New_York")
    
    print("\n" + scheduler.format_upload_schedule())
    
    print("\n=== Upload Time Tests ===")
    
    # Show next upload time
    next_upload = scheduler.get_next_upload_time()
    print(f"\nNext upload time: {next_upload}")
    
    # Show time until next upload
    time_until = scheduler.get_time_until_next_upload()
    print(f"Time until next upload: {time_until}")
    
    # Show today's schedule
    today_schedule = scheduler.get_upload_schedule_for_day()
    print(f"\nToday's schedule:")
    for time in today_schedule:
        print(f"  - {time}")
    
    # Check if should upload now
    should_upload = scheduler.should_upload_now()
    print(f"\nShould upload now: {should_upload}")
