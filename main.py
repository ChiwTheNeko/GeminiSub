# Written by Chiw the Neko <chiwtheneko@gmail.com>
import os
import time
import copy
import argparse
import tempfile
import logging
from pathlib import Path
from ffmpeg_utils import extract_all_audio, extract_audio_as_video, get_file_duration, FFmpegError
from gemini_utils import display_available_models, transcribe, translate
from vad_utils import find_speech_timestamps, find_optimal_split_points
from srt_utils import merge_srt, write_srt_file
from exception_utils import get_fqn



def main():
  # Setup the argument parser
  parser = argparse.ArgumentParser(description = "Extract audio from a video file.")

  # Define arguments
  parser.add_argument("input", type = str, nargs = '?', help = "Path to the source video file")
  parser.add_argument("--list-models", action = "store_true", help = "Display all available Gemini models and exit")

  # Parse args
  args = parser.parse_args()

  # Retrieve the key
  api_key = os.environ.get("GEMINI_API_KEY")
  if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables!")

  # Display models and exit if --list-models was given on the command line
  if args.list_models:
    display_available_models(api_key)
    return

  # Convert the input string into a Path object
  video_path = Path(args.input)

  # Make sure the file exist
  if not video_path.exists():
    print(f"Error: The file '{video_path}' was not found.")
    return

  print(f"Processing: {video_path.name}...")

  # Temporary work directory
  with tempfile.TemporaryDirectory() as tmp_dir_name:
    working_dir = Path(tmp_dir_name)

    try:
      # Extract all the audio in the video file
      print("Extracting audio...")
      audio_path = extract_all_audio(video_path, working_dir)

      # Total audio duration
      duration = get_file_duration(audio_path)
      print(f"Audio duration: {duration}")

      # Find speech gaps
      print("Finding speech gaps...")
      speech_timestamps = find_speech_timestamps(audio_path)

      # Find split points
      print("Finding optimal split points...")
      splits = find_optimal_split_points(speech_timestamps, duration, 120)
      splits.append(duration)

      # Split into chunks
      chunks = []
      start = 0
      for split in splits:
        # chunk = extract_audio(audio_path, start, split, working_dir)
        chunk = extract_audio_as_video(audio_path, start, split, working_dir)
        chunks.append({
          'start': start,
          'audio': chunk
        })
        start = split

      # Transcribe audio chunks
      transcriptions = []
      for chunk in chunks:
        subtitles = transcribe(chunk['audio'], api_key)
        print("-------------------------------------------")
        print(subtitles)
        transcriptions.append({
          'start': chunk['start'],
          'data' : subtitles
        })
        time.sleep(30)  # Be polite

      # Translated transcriptions
      translations = []
      for transcription in transcriptions:
        subtitles = translate(transcription['data'], api_key)
        print("-------------------------------------------")
        print(subtitles)
        translations.append({
          'start': transcription['start'],
          'data' : subtitles
        })
        time.sleep(30)  # Be polite

      # Parse and merge transcriptions
      transcribed_subtitles = merge_srt(transcriptions)

      # Save transcribed subtitle
      write_srt_file(video_path, "jp", transcribed_subtitles)

      # Parse and merge translations
      translated_subtitles = merge_srt(translations)

      # Save translated subtitle
      write_srt_file(video_path, "en", translated_subtitles)

    except FFmpegError as err:
      # This specifically catches our FFmpeg errors
      print(f"An error occurred during processing: {err}")

    except Exception as e:
      # This catches other issues (like file permissions or missing ffmpeg)
      logging.exception(f"A general error occurred. {get_fqn(e)}")



if __name__ == "__main__":
  main()
