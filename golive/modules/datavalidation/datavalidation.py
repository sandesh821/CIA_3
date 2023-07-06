#Copyright (c) Microsoft. All rights reserved.
# Import libraries
from dateutil.parser import parse
from datetime import datetime

def check_datetime_columns(df):
    """
    Returns a list of column names from a pandas DataFrame that contain datetime values.

    Args:
        df (pandas.DataFrame): The DataFrame to search for datetime columns.
        file_type: Validate the file type by checking the number of datetime columns.

    Returns:
        list: A list of column names that contain datetime values.
    """

    def detect_datetime(item):
        """
        Helper function to detect whether an item is a datetime.

        Args:
            item: The item to check for datetime.

        Returns:
            bool: True if the item is a datetime, False otherwise.
        """
        try:
            dt = parse(item)
            if isinstance(dt, datetime):
                return True
            else:
                return False
        except ValueError:
            return False
        except TypeError:
            return False

    datetime_columns = []
    for col in df.columns:
        is_datetime = False
        for item in df[col]:
            if detect_datetime(item):
                is_datetime = True
                break
        if is_datetime:
            datetime_columns.append(col)

        assert len(datetime_columns) == 1
    return datetime_columns

def basicDataValidation(dataFrame):
    check = True
    if len(dataFrame) == 0:
        check = False
    # Check if datetime column is present
    if len(dataFrame.columns)<2:
        check = False
    
    # if len(check_datetime_columns(dataFrame)) < 1:
    #     check = False

    return check