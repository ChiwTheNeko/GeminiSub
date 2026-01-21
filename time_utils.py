# Written by Chiw the Neko <chiwtheneko@gmail.com>
import argparse
from datetime import datetime



def parse_timestamp(ts_str):
  """Converts HH:MM:SS.mmm string to a datetime.time object."""
  try:
    # If the user didn't provide milliseconds, try a shorter format
    if "." not in ts_str:
      return datetime.strptime(ts_str, "%H:%M:%S").time()

    # Parse full format with milliseconds/microseconds
    return datetime.strptime(ts_str, "%H:%M:%S.%f").time()
  except ValueError:
    raise argparse.ArgumentTypeError(f"Invalid time format: '{ts_str}'. Use HH:MM:SS or HH:MM:SS.mmm")
