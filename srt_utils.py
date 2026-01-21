# Written by Chiw the Neko <chiwtheneko@gmail.com>
from pathlib import Path
from path_utils import generate_unique_path



def extract_subtitle_list(data):
  # Get array of subtitles
  subtitle_list = data["subtitles"]

  # Add indices
  i = 1
  for subtitle in subtitle_list:
    subtitle['index'] = i
    i += 1

  return subtitle_list



def shift_srt(start_time: float, start_index: int, subtitle_list):
  for sub in subtitle_list:
    sub['index'] = sub['index'] + start_index
    sub['start'] = sub['start'] + start_time
    sub['end'] = sub['end'] + start_time



def merge_srt(transcriptions):
  subtitles = []
  i = 0
  for transcription in transcriptions:
    transcription_subtitles = extract_subtitle_list(transcription['data'])
    print("index:", i, "start:", transcription['start'])
    shift_srt(transcription['start'], i, transcription_subtitles)
    subtitles.extend(transcription_subtitles)
    i += len(transcription_subtitles)
  return subtitles



def write_srt_file(video_path: Path, suffix: str, subtitle_list):
  def format_timestamp(seconds_float):
    # Calculate hours, minutes, seconds
    hrs = int(seconds_float // 3600)
    mins = int((seconds_float % 3600) // 60)
    secs = int(seconds_float % 60)

    # Calculate milliseconds (3 decimal places)
    msecs = int(round((seconds_float - int(seconds_float)) * 1000))

    # Handle overflow from rounding (e.g., 59.9999 -> 60.000)
    if msecs == 1000:
      return format_timestamp(seconds_float + 0.001)

    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


  lines = []
  for sub in subtitle_list:
    start_str = format_timestamp(sub['start'])
    end_str = format_timestamp(sub['end'])

    # Format the block: Index, Timestamp, Text, followed by an empty line
    block = f"{sub['index']}\n{start_str} --> {end_str}\n{sub['text']}\n"
    lines.append(block)

  # Join blocks with an extra newline to ensure double-spacing between entries
  content = "\n".join(lines)

  # Generate unique path for the file
  output_path = generate_unique_path(video_path, suffix)

  # Write to file
  output_path.write_text(content, encoding = 'utf-8')
