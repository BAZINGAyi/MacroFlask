import time
from datetime import datetime


import time
from datetime import datetime, timedelta


class TimeUtils:
    @staticmethod
    def get_current_time(format='local'):
        """
        Get the current time based on the specified format.

        :param format: Desired format of the time ('local', 'utc', 'timestamp')
        :return: Formatted time string or Unix timestamp
        """
        now = datetime.now()
        if format == 'local':
            return now.strftime("%Y-%m-%d %H:%M:%S")
        elif format == 'utc':
            return int(time.time())
        elif format == 'timestamp':
            return int(now.timestamp())
        else:
            raise ValueError("Invalid format type. Use 'local', 'utc', or 'timestamp'.")

    @staticmethod
    def get_time_boundary(period='today', months_ago=0):
        """
        Get the Unix timestamp for the start of a specified time boundary.

        :param period: Time period ('today', 'month', 'year', 'prior_month')
        :return: Unix timestamp for the start of the specified time boundary
        """
        now = datetime.now()
        if period == 'today':
            return int(datetime.combine(now.date(), datetime.min.time()).timestamp())
        elif period == 'month':
            return int(datetime(now.year, now.month, 1).timestamp())
        elif period == 'year':
            return int(datetime(now.year, 1, 1).timestamp())
        elif period == 'months_ago':
            if months_ago < 1:
                raise ValueError("months_ago must be a positive integer.")
            # Calculate the start of the month N months ago
            first_day_of_current_month = datetime(now.year, now.month, 1)
            target_month = first_day_of_current_month - timedelta(days=(months_ago * 30))
            target_month = target_month.replace(day=1)  # Set to the first day of that month
            return int(target_month.timestamp())
        else:
            raise ValueError("Invalid period type. Use 'today', 'month', 'year', or 'prior_month'.")

    @staticmethod
    def convert_timestamp(timestamp, format_type='full'):
        """
        Convert a Unix timestamp to a formatted date string.

        :param timestamp: Unix timestamp to convert
        :param format_type: Type of formatting ('full' for 'YYYY-MM-DD HH:MM:SS', 'month' for 'YYYY-MM')
        :return: Formatted date string
        """
        if format_type == 'full':
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        elif format_type == 'month':
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m')
        else:
            raise ValueError("Invalid format type. Use 'full' or 'month'.")

    @staticmethod
    def format_filename_by_timestamp(timestamp):
        """
        Format a Unix timestamp into a filename-friendly date string.

        :param timestamp: Unix timestamp to convert
        :return: Formatted date string for filenames
        """
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H:%M:%S')

    @staticmethod
    def parse_utc_text(utc_text, from_format=None, is_china_time_zone=False):
        """
        Convert a UTC time string to a Unix timestamp.

        :param utc_text: UTC time string to convert
        :param from_format: Format of the UTC time string (default: '%H:%M:%S.%f UTC %a %b %d %Y')
        :param is_china_time_zone: If True, assume the input time is in China time zone (UTC+8)
        :return: Unix timestamp
        """
        from_format = from_format or '%H:%M:%S.%f UTC %a %b %d %Y'
        time_struct = time.strptime(utc_text, from_format)
        timestamp = int(time.mktime(time_struct))
        if not is_china_time_zone:
            timestamp -= 8 * 3600  # Convert from China time zone to UTC
        return timestamp


if __name__ == '__main__':
    # 1. Get the current time
    print("Current Local Time:", TimeUtils.get_current_time(format='local'))
    print("Current UTC Timestamp:", TimeUtils.get_current_time(format='utc'))
    print("Current Unix Timestamp:", TimeUtils.get_current_time(format='timestamp'))
    print('----')
    # 2. Get the Unix timestamp for specific time boundaries
    print("Start of Today:", TimeUtils.get_time_boundary(period='today'))
    print("Start of Current Month:", TimeUtils.get_time_boundary(period='month'))
    print("Start of Current Year:", TimeUtils.get_time_boundary(period='year'))
    print("Start of Prior Month:", TimeUtils.get_time_boundary(period='months_ago', months_ago=2))
    print('----')
    # 3. Convert Unix timestamp to formatted date string
    timestamp = TimeUtils.get_current_time(format='timestamp')  # Example timestamp
    print("Formatted Date String (Full):",
          TimeUtils.convert_timestamp(timestamp, format_type='full'))
    print("Formatted Date String (Month):",
          TimeUtils.convert_timestamp(timestamp, format_type='month'))
    print('----')
    # 4. Format a Unix timestamp into a filename-friendly date string
    print("Filename-friendly Date String:", TimeUtils.format_filename_by_timestamp(timestamp))

    # 5. Parse a UTC time string to Unix timestamp
    utc_text = "09:34:50.285 UTC Tue Nov 23 2021"  # Example UTC time string
    print("Parsed Unix Timestamp:", TimeUtils.parse_utc_text(utc_text))

    # If the UTC time is in China time zone (UTC+8), set `is_china_time_zone=True`
    print("Parsed Unix Timestamp (China Time Zone):",
          TimeUtils.parse_utc_text(utc_text, is_china_time_zone=True))