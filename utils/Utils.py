import os
import time
import re
import calendar
from datetime import datetime

class Utils():
    # Return list of all files in specified backup folder
    @classmethod
    def list_local_files(cls, local_path):
        return os.listdir(local_path)

    # Get last modification timestamp from local file
    @classmethod
    def get_local_file_timestamp(cls, path):
        unix_timestamp = os.path.getmtime(path)
        utc_datetime = cls.convert_timestamp_datetime(unix_timestamp)
        utc_timestamp = cls.convert_datetime_timestamp(utc_datetime)

        return int(unix_timestamp)

    # Convert Google Drive's datetime to local timestamp
    @classmethod
    def convert_datetime_timestamp(cls, date):
        date = re.sub(r'\.\d+', '', date)
        time_object = time.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
        timestamp = calendar.timegm(time_object)
        
        return int(timestamp)

    # Convert local timestamp to Google Drive's datetime
    @classmethod
    def convert_timestamp_datetime(cls, timestamp):
        datetime_object = datetime.utcfromtimestamp(timestamp)
        
        return datetime_object.isoformat("T") + "Z"