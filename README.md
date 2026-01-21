# GeminiSub
A throwaway script to generate translated subtitles with Gemini API.

**THIS IS NOT PRODUCTION READY!**

# What it does
- Extract audio from the given video file, resample it and normalize noise for easier processing.
- Use VAD to detect speech gaps.
- Split the audio into chunks no longer than 10 minutes, cutting within the gaps.
- Feed chunks to the Gemini API to generate transcription.
- Feed transcriptions to the Gemini API to generate English translation.
- Merge transcriptions and translations into SRT subtitle files.

# How to use
- Set your Gemini API key into the GEMINI_API_KEY environment variable.
- Execute `python main.py <path to your video file>`
- Pray.
