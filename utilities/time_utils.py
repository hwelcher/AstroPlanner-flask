from astroplan import Observer, FixedTarget
from astroplan import time_grid_from_range, moon_illumination
from astropy.time import Time, TimeDelta
from astropy.coordinates import SkyCoord
from astropy import units as u, coordinates as coord
from flask import g
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
import numpy as np
import pytz
import time
from utilities import geo_utils

# time_utils.py

def get_first_day_of_month(input_datetime):
    """
    Returns the first day of the month for a given datetime.

    This function takes a datetime object as input and returns a new
    datetime object representing the first day of that month. The time
    component of the returned datetime will be set to midnight.

    Parameters:
        input_datetime (datetime): The datetime object for which the first
            day of the month is to be returned.

    Returns:
        datetime: A datetime object representing the first day of the month
            corresponding to the input datetime.

    Example:
        input_datetime = datetime.datetime(2023, 8, 16, 12, 0)
        first_day = get_first_day_of_month(input_datetime)
        print(first_day)  # Output: 2023-08-01 00:00:00
    """

    first_day_of_month = input_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return first_day_of_month


def get_first_day_of_next_month(input_datetime):
    """
    Returns the first day of the next month for a given datetime.

    This function takes a datetime object as input and returns a new
    datetime object representing the first day of the next month. If the
    input_datetime is in December, the year will be incremented. The time
    component of the returned datetime will be set to midnight.

    Parameters:
        input_datetime (datetime): The datetime object for which the first
            day of the next month is to be returned.

    Returns:
        datetime: A datetime object representing the first day of the next
            month corresponding to the input datetime.

    Example:
        input_datetime = datetime.datetime(2023, 12, 16, 12, 0)
        first_day_next_month = get_first_day_of_next_month(input_datetime)
        print(first_day_next_month)  # Output: 2024-01-01 00:00:00
    """

    if input_datetime.month == 12:
        first_day_of_next_month = input_datetime.replace(year=input_datetime.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        first_day_of_next_month = input_datetime.replace(month=input_datetime.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    return first_day_of_next_month

def get_first_days_of_month_for_time_range(start_date, end_date):
    """
    Returns a list of datetime objects representing the first day of each month
    in the given time range.

    This function takes two datetime objects representing a start date and an
    end date, and returns a list of datetime objects representing the first day
    of each month within that range. The time component of each datetime in the
    list will be set to midnight.

    Parameters:
        start_date (datetime): The starting datetime of the range.
        end_date (datetime): The ending datetime of the range.

    Returns:
        list[datetime]: A list of datetime objects representing the first day
            of each month in the specified time range.

    Example:
        start_date = datetime.datetime(2023, 2, 16)
        end_date = datetime.datetime(2023, 5, 20)
        first_days = get_first_days_of_month_for_time_range(start_date, end_date)
        for day in first_days:
            print(day)
        # Output:
        # 2023-02-01 00:00:00
        # 2023-03-01 00:00:00
        # 2023-04-01 00:00:00
        # 2023-05-01 00:00:00
    """

    current_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date_first_of_month = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    first_days = []

    while current_date <= end_date_first_of_month:
        first_days.append(current_date)

        # Move to the first day of the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    return first_days

def get_optimal_times(start_datetime, end_datetime, latitude, longitude):

    optimal_times_ref = g.db.collection("optimal_times")
    optimal_times_results = []

    latitude_course  = round(latitude, 2)
    longitude_course = round(longitude, 2)

    first_day_of_month_list = get_first_days_of_month_for_time_range(start_datetime, end_datetime)

    for first_day_of_month in first_day_of_month_list:

        print(f"first_day_of_month: {first_day_of_month}")
        print(f"latitude_course: {latitude_course}")
        print(f"longitude_course: {longitude_course}")
        # Check if we have results for the month
        query_ref = optimal_times_ref.where(filter=FieldFilter("start_date", "==", first_day_of_month)).where("latitude", "==", latitude_course).where("longitude", "==", longitude_course)

        results = query_ref.stream()
        results_list = list(results)

        print(len(results_list))

        for result in results_list:
            time_results = result.to_dict()["optimal_times"]
            astropy_times = [Time(time_string, format='isot') for time_string in time_results]

            optimal_times_results += astropy_times

    matching_times = []
    for time in optimal_times_results:
        if start_datetime < time and end_datetime > time:
            matching_times.append(time)

    return matching_times

def get_or_generate_optimal_times(start_datetime, end_datetime, latitude, longitude):
    """
    Retrieves or generates optimal times for a given time range and location.

    This function queries a database for pre-existing optimal times between
    the start and end dates for the specified latitude and longitude. If no
    results are found in the database, it calls a function to generate the
    optimal times for that month.

    Parameters:
        start_datetime (datetime): The starting datetime of the range.
        end_datetime (datetime): The ending datetime of the range.
        latitude (float): The latitude coordinate for the location.
        longitude (float): The longitude coordinate for the location.

    Returns:
        list[astropy.time.Time]: A list of astropy Time objects representing
            the optimal times within the specified time range and location.

    Example:
        start_datetime = datetime.datetime(2023, 2, 16)
        end_datetime = datetime.datetime(2023, 5, 20)
        latitude = 37.7749
        longitude = -122.4194
        optimal_times = get_or_generate_optimal_times(start_datetime, end_datetime, latitude, longitude)
        for time in optimal_times:
            print(time)
        # Output could include various astropy Time objects within the specified range.
    """

    optimal_times_ref = g.db.collection("optimal_times")
    optimal_times_results = []

    latitude_course  = round(latitude, 2)
    longitude_course = round(longitude, 2)

    first_day_of_month_list = get_first_days_of_month_for_time_range(start_datetime, end_datetime)

    for first_day_of_month in first_day_of_month_list:
        # Check if we have results for the month
        query_ref = optimal_times_ref.where(filter=FieldFilter("start_date", "==", first_day_of_month)).where("latitude", "==", latitude_course).where("longitude", "==", longitude_course)

        results = query_ref.stream()
        results_list = list(results)

        if not results_list:
            optimal_times_results += generate_optimal_times(first_day_of_month, get_first_day_of_next_month(first_day_of_month), latitude, longitude)
        else:
            for result in results_list:
                time_results = result.to_dict()["optimal_times"]
                astropy_times = [Time(time_string, format='isot') for time_string in time_results]

                optimal_times_results += astropy_times

    matching_times = []
    for time in optimal_times_results:
        if start_datetime < time and end_datetime > time:
            matching_times.append(time)

    return matching_times

def generate_optimal_times_full(start_datetime, end_datetime, latitude, longitude):
    optimal_times_ref = g.db.collection("optimal_times")
    optimal_times_results = []

    latitude_course  = round(latitude, 2)
    longitude_course = round(longitude, 2)

    first_day_of_month_list = get_first_days_of_month_for_time_range(start_datetime, end_datetime)

    for first_day_of_month in first_day_of_month_list:
        # Check if we have results for the month
        query_ref = optimal_times_ref.where(filter=FieldFilter("start_date", "==", first_day_of_month)).where("latitude", "==", latitude_course).where("longitude", "==", longitude_course)

        results = query_ref.stream()
        results_list = list(results)

        if not results_list:
            generate_optimal_times(first_day_of_month, get_first_day_of_next_month(first_day_of_month), latitude, longitude)

def generate_optimal_times(start_datetime_utc, end_datetime_utc, latitude, longitude):
    """
    Generates a list of optimal times for astronomical observation within a given time range and location.

    This function calculates the optimal times for astronomical observations, such as stargazing,
    based on specific criteria. These criteria include the Sun being more than 18 degrees below
    the horizon, and the Moon being either more than 5 degrees below the horizon or less than 10 percent illuminated.
    The calculated times are stored in a database for reuse.

    Parameters:
        start_datetime_utc (datetime): The starting datetime of the range in UTC timezone.
        end_datetime_utc (datetime): The ending datetime of the range in UTC timezone.
        latitude (float): The latitude coordinate for the observation location.
        longitude (float): The longitude coordinate for the observation location.

    Returns:
        list[astropy.time.Time]: A list of astropy Time objects representing
            the optimal times for astronomical observation within the specified
            time range and location.

    Example:
        start_datetime_utc = datetime.datetime(2023, 2, 16, tzinfo=pytz.utc)
        end_datetime_utc = datetime.datetime(2023, 5, 20, tzinfo=pytz.utc)
        latitude = 37.7749
        longitude = -122.4194
        optimal_times = generate_optimal_times(start_datetime_utc, end_datetime_utc, latitude, longitude)
        for time in optimal_times:
            print(time)
        # Output will include various astropy Time objects within the specified range,
        # satisfying the defined criteria for astronomical observation.

    Note:
        The implementation of this function relies on several external utilities and methods,
        such as getting elevation, location name, and timezone, that must be properly implemented.
    """

    # Define the location details
    location_latitude  = latitude
    location_longitude = longitude

    latitude_course  = round(latitude, 2)
    longitude_course = round(longitude, 2)

    # TODO: Need to implement these methods for real
    loc_elevation = geo_utils.get_elevation(location_latitude, location_longitude)
    loc_name      = geo_utils.get_location_name(location_latitude, location_longitude)

    loc_timezone_str  = geo_utils.get_timezone(location_latitude, location_longitude)
    loc_timezone = pytz.timezone(loc_timezone_str)

    utc_timezone = pytz.utc

    # Define the time range and intervals in local timezone

    # Convert the start and end times from UTC to the local timezone
    start_date_local = start_datetime_utc.astimezone(loc_timezone)
    end_date_local = end_datetime_utc.astimezone(loc_timezone)

    # Define the observer location
    observer = Observer(latitude=location_latitude * u.deg,
                        longitude=location_longitude * u.deg,
                        elevation=loc_elevation * u.m,
                        timezone=loc_timezone_str)

    # Convert local times to UTC for astropy
    start_date = Time(start_date_local.astimezone(pytz.UTC))
    end_date = Time(end_date_local.astimezone(pytz.UTC))

    # Define the 15-minute interval
    interval = TimeDelta(15*60, format='sec')

    # Create the time grid
    times = []
    current_time = start_date
    while current_time < end_date:
        times.append(current_time)
        current_time += interval

    times = Time(times)  # Convert list to Time object

    # Measure the altitude of the Sun at each time
    sun_alt = observer.altaz(times, coord.get_sun(times)).alt

    # Measure the altitude of the Moon at each time
    moon_alt = observer.altaz(times, coord.get_body("moon", times)).alt

    # Define "good" conditions:
    # * sun is more than 18 degress below horizon
    # * moon is more than 5 degrees below horizon or less than 10 percent illuminated
    sun_horizon = -18
    moon_horizon = -5
    max_moon_illum = 0.1

    # Create list of 'optimal_times'. These can be reused for future calculations from this location.
    optimal_times = []
    for index in range(len(times)):
        # Is the sun below 'sun_horizon'?
        if sun_alt[index].deg < sun_horizon:
            # Is the moon below `moon_horizon` or below illum threshold?
            if moon_alt[index].deg < moon_horizon or moon_illumination(times[index]) < max_moon_illum:
                optimal_times.append(times[index])
    
    # Convert to json to store in Firestore
    times_iso = [time.isot for time in optimal_times]

    data = {
        "start_date": start_datetime_utc,
        "end_date": end_datetime_utc,
        "latitude": latitude_course,
        "longitude": longitude_course,
        "optimal_times": times_iso
    }

    g.db.collection("optimal_times").add(data)

    # return optimal_times