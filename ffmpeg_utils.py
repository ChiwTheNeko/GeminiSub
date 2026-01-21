# Written by Chiw the Neko <chiwtheneko@gmail.com>
import subprocess
from pathlib import Path
from datetime import time
from path_utils import generate_temporary_path



class FFmpegError(Exception):
  """Custom exception raised when an FFmpeg command fails."""
  pass



def format_ffmpeg_time(t: time):
  """Converts a python time object to HH:MM:SS.mmm string"""
  return t.strftime("%H:%M:%S.%f")[:-3]



def extract_all_audio(video_path: Path, working_dir: Path):
  # Generate a unique filename for this specific clip
  output_path = generate_temporary_path(working_dir, "mp3")

  command = [
    "ffmpeg", "-hide_banner", "-loglevel", "level+error",
    "-i", video_path,
    "-vn",  # No video
    "-ac", "1",  # <--- FORCED MONO
    "-ar", "16000",  # <--- FORCED 16kHz
    "-c:a", "libmp3lame",
    "-af", "loudnorm",  # Normalize volume
    "-q:a", "2",  # High quality VBR
    "-y",  # Overwrite output
    output_path
  ]

  try:
    subprocess.run(command, capture_output = True, text = True, check = True)
    return output_path
  except subprocess.CalledProcessError as e:
    print(f"FFmpeg Error: {e.stderr}")
    error_message = e.stderr.strip() or "Unknown FFmpeg error"
    raise FFmpegError(f"FFmpeg failed with exit code {e.returncode}: {error_message}")



def get_file_duration(file_path: Path):
  command = [
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1",
    file_path
  ]
  result = subprocess.run(command, capture_output = True, text = True, check = True)
  return float(result.stdout.strip())



def extract_audio(audio_path: Path, start_time: float, end_time: float, working_dir: Path):
  # Generate a unique filename for this specific clip
  output_path = generate_temporary_path(working_dir, "mp3")

  command = [
    "ffmpeg", "-hide_banner", "-loglevel", "level+error",
    "-ss", str(start_time),
    "-to", str(end_time),
    "-i", audio_path,
    output_path
  ]

  try:
    subprocess.run(command, capture_output = True, text = True, check = True)
    return output_path
  except subprocess.CalledProcessError as e:
    print(f"FFmpeg Error: {e.stderr}")
    error_message = e.stderr.strip() or "Unknown FFmpeg error"
    raise FFmpegError(f"FFmpeg failed with exit code {e.returncode}: {error_message}")



def extract_audio_as_video(audio_path: Path, start_time: float, end_time: float, working_dir: Path):
  # Generate a unique filename for this specific clip
  output_path = generate_temporary_path(working_dir, "mp4")
  
  print("generate ", start_time, end_time)

  command = [
    "ffmpeg", "-hide_banner", "-loglevel", "level+error",
    "-ss", str(start_time),
    "-to", str(end_time),
    "-i", audio_path,
    "-f", "lavfi",
    "-i", "color=c=black:s=640x480:r=24",
    "-tune", "stillimage",
    "-pix_fmt", "yuv420p",
    "-shortest",
    output_path
  ]

  try:
    subprocess.run(command, capture_output = True, text = True, check = True)
    return output_path
  except subprocess.CalledProcessError as e:
    print(f"FFmpeg Error: {e.stderr}")
    error_message = e.stderr.strip() or "Unknown FFmpeg error"
    raise FFmpegError(f"FFmpeg failed with exit code {e.returncode}: {error_message}")
