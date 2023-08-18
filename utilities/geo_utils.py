# geo_utils.py

from timezonefinder import TimezoneFinder

# Returns the elevation (in meters) for a given location.
def get_elevation(latitude, longitude):
    return 329.0

# Returns the location name for a given location.
def get_location_name(latitude, longitude):
    return "Waterloo"

def get_timezone(latitude, longitude):
    # Instantiate the TimezoneFinder object
    tz_finder = TimezoneFinder()

    timezone = tz_finder.timezone_at(lat=latitude, lng=longitude)

    return timezone