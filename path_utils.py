# Written by Chiw the Neko <chiwtheneko@gmail.com>
import re
import uuid
from pathlib import Path



def generate_unique_path(video_path: Path, suffix: str):
  # Define the pattern to look for
  # This matches: filename.jp.srt AND filename.jp(ANY_NUMBER).srt
  base_stem = f"{video_path.stem}.{suffix}"
  extension = ".srt"

  # Get all existing files in the directory that start with our base name
  # We use glob to find only relevant files
  existing_files = list(video_path.parent.glob(f"{base_stem}*{extension}"))

  if not existing_files:
    return video_path.with_name(f"{base_stem}{extension}")

  # Use regex to find the highest number
  # This pattern looks for '(number)' right before the extension
  pattern = re.compile(rf"{re.escape(base_stem)}\((\d+)\){re.escape(extension)}")

  max_num = 0
  found_any_numbered = False

  for file in existing_files:
    # Check if it's the base file (no number)
    if file.name == f"{base_stem}{extension}":
      found_any_numbered = True  # We found at least the base file
      continue

    # Check for numbered versions
    match = pattern.search(file.name)
    if match:
      num = int(match.group(1))
      if num > max_num:
        max_num = num
      found_any_numbered = True

  # Determine the next path
  if not found_any_numbered:
    return video_path.with_name(f"{base_stem}{extension}")
  next_num = max_num + 1
  return video_path.with_name(f"{base_stem}({next_num}){extension}")



def generate_temporary_path(working_dir: Path, extension: str):
  unique_filename = f"{uuid.uuid4()}.{extension}"
  unique_path = working_dir / unique_filename
  return unique_path
