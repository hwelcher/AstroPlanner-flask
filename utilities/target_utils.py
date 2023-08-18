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
from utilities import time_utils

def get_optimal_target_times(start_date_str, end_date_str, latitude, longitude, location_name, target_id, target_name, min_altitude, min_session_length):

    timezone = geo_utils.get_timezone(float(latitude), float(longitude))
    local_timezone = pytz.timezone(timezone)
    start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

    # Add one day to end date since we want the start/end to be inclusive
    end_date_obj += datetime.timedelta(days=1)

    # Assume start_date_obj and end_date_obj are in UTC
    start_time_utc = pytz.utc.localize(start_date_obj)
    end_time_utc = pytz.utc.localize(end_date_obj)

    latitude = float(latitude)
    longitude = float(longitude)

    latitude_course = round(latitude, 2)
    longitude_course = round(longitude, 2)

    location_elevation = geo_utils.get_elevation(latitude, longitude)
    location_timezone = geo_utils.get_timezone(latitude, longitude)

    # Define the timezone object
    timezone = pytz.timezone(location_timezone)

    # Define the observer location
    observer = Observer(latitude=latitude * u.deg,
                        longitude=longitude * u.deg,
                        elevation=location_elevation * u.m,
                        name=location_name,
                        timezone=location_timezone)

    # Create the SkyCoord object from target_id
    target_coord = SkyCoord.from_name(target_id)

    # Create the target
    target = FixedTarget(coord=target_coord, name=target_name)

    # Optimal times to observe any potential target
    optimal_times = time_utils.get_optimal_times(start_time_utc, end_time_utc, latitude, longitude)

    if len(optimal_times) == 0:
        return []

    # Measure the altitude of the target at each time
    target_alt = observer.altaz(optimal_times, target)

    time_list = []

    for time, alt in zip(optimal_times, target_alt.alt):
        if alt.deg >= float(min_altitude):
            time_list.append(time.to_datetime(timezone=timezone))

    if len(time_list) == 0:
        return []

    blocks = []
    current_block = [time_list[0]]

    # Iterate through the datetimes, combining those that are less than 20 minutes apart
    for i in range(1, len(time_list)):
        if (time_list[i] - time_list[i - 1]).seconds <= 20 * 60:
            current_block.append(time_list[i])
        else:
            blocks.append(current_block)
            current_block = [time_list[i]]

    # Append the last block
    blocks.append(current_block) # TODO: I feel like the '1440' bug has something to do with this line

    sessions = []

    # Print the start and end datetimes for each contiguous block
    for block in blocks:
        start_date = block[0]
        end_date = block[-1]
        duration = (end_date - start_date).total_seconds() / 60  # Convert duration from seconds to minutes
        if duration >= float(min_session_length) and duration < 1440: # TODO: Remove this '1440' hack
            sessions.append({'start': start_date.astimezone(local_timezone).strftime('%Y-%m-%d %H:%M:%S'), 'end': end_date.astimezone(local_timezone).strftime('%Y-%m-%d %H:%M:%S'), 'duration': duration})

    return sessions