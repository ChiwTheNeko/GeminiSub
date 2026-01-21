# # Written by Chiw the Neko <chiwtheneko@gmail.com>
from pathlib import Path
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps



# Use a global variable to store the model once loaded
_vad_model = None



def get_vad_model():
  print("Loading VAD model...")
  global _vad_model
  if _vad_model is None:
    _vad_model = load_silero_vad()
  return _vad_model



def find_speech_timestamps(audio_path: Path):
  model = get_vad_model()
  wav = read_audio(str(audio_path))
  speech_timestamps = get_speech_timestamps(
    wav,
    model,
    return_seconds = True,  # Return speech timestamps in seconds (default is samples)
  )
  return speech_timestamps



def find_optimal_split_points(speech_timestamps, total_duration, max_duration):
  splits = []

  # Identify all gaps between speech
  gaps = []
  for i in range(len(speech_timestamps) - 1):
    gap_start = speech_timestamps[i]['end']
    gap_end = speech_timestamps[i + 1]['start']
    gaps.append({
      'start'   : gap_start,
      'end'     : gap_end,
      'duration': gap_end - gap_start,
      'midpoint': (gap_start + gap_end) / 2
    })

  # Find split points
  current_search_start = 0
  video_end = total_duration

  while (current_search_start + max_duration) < video_end:
    window_end = current_search_start + max_duration

    # Filter gaps that fall within this 10-minute segment
    valid_gaps = [g for g in gaps if current_search_start < g['midpoint'] <= window_end]

    if not valid_gaps:
      # Fallback if no speech gap is found (unlikely for a large enough max_duration)
      splits.append(window_end)
      current_search_start = window_end
    else:
      # Pick the longest gap among the three last
      best_gap = valid_gaps[-1]
      if len(valid_gaps) > 1 and valid_gaps[-2]['duration'] > best_gap['duration']:
        best_gap = valid_gaps[-2]
      if len(valid_gaps) > 2 and valid_gaps[-3]['duration'] > best_gap['duration']:
        best_gap = valid_gaps[-3]

      # Add gap midpoint to splits
      splits.append(best_gap['midpoint'])
      current_search_start = best_gap['midpoint']

  return splits
