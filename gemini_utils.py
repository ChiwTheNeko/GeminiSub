# Written by Chiw the Neko <chiwtheneko@gmail.com>
import time
import random
import google.api_core.exceptions
from pathlib import Path
from google import genai
from google.genai import errors
from google.genai import types
from exception_utils import get_fqn
from path_utils import generate_temporary_path



gemini_model = "gemini-3-flash-preview"

transcription_instruction = """
You are a high-accuracy Japanese subtitle generator.
"""

translation_instruction = """
You are an expert Japanese-to-English subtitle translator.

Your goal is to provide natural, idiomatic English translations while preserving Japanese naming conventions and honorifics to maintain cultural authenticity.

SPECIFIC INSTRUCTIONS:
1. HONORIFIC RETENTION: DO NOT translate or remove Japanese honorifics. Keep suffixes such as "-san", "-kun", "-chan", "-sama", "-senpai", "-kohai", and "-dono" attached to the names.
   - Example: "田中さん" should remain as "Tanaka-san".
   - Always maintain the original Japanese name order (Surname first) when followed by an honorific.
2. TITLES: Keep titles like "Sensei" or "Bucho" if used as a form of address after a name.
3. CONTEXTUAL FLOW: Even though you are keeping Japanese honorifics, ensure the rest of the sentence is natural English.
   - Example: "佐藤くん、どこに行くの？" -> "Sato-kun, where are you going?"
4. IDIOMS: Do not translate literally. If a character says "Otsukaresama," translate it contextually as "Good job today," "I'm heading out," or "See you later.
5. SUBTITLE FORMATTING:
   - Keep translations concise. Subtitles should be easy to read in 2-3 seconds.
   - Maintain the EXACT index numbers and timestamps from the source.
   - Do NOT add any notes, explanations, or "Translator's Notes" in the output.
"""

safety_settings = [
  types.SafetySetting(
    category = types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    threshold = types.HarmBlockThreshold.OFF,
  ),
  types.SafetySetting(
    category = types.HarmCategory.HARM_CATEGORY_HARASSMENT,
    threshold = types.HarmBlockThreshold.OFF,
  ),
  types.SafetySetting(
    category = types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    threshold = types.HarmBlockThreshold.OFF,
  ),
  types.SafetySetting(
    category = types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    threshold = types.HarmBlockThreshold.OFF,
  ),
]



def generate_with_retry(client: genai.Client, config: types.GenerateContentConfig, content, max_retries = 10):
  def wait_a_little(nb_attempt):
    # Exponential backoff: 2, 4, 8, 16, 32... seconds
    # Plus "jitter" (a random decimal) to smooth out traffic spikes
    wait_time = (2 ** nb_attempt) + random.random()

    print(f"Retrying in {wait_time:.2f} seconds (Attempt {nb_attempt + 1}/{max_retries})...")

    time.sleep(wait_time)


  # Try several times if needed
  for attempt in range(max_retries):
    try:
      response = client.models.generate_content(
        model = gemini_model,
        config = config,
        contents = content
      )

      # Try again if response was None
      if response is None:
        print("No response received.")
        wait_a_little(attempt)

      # If text is None then check the reason
      elif response.text is None or response.text == "":
        print(f"Empty response received.")

        # Check the finish reason
        if len(response.candidates) > 0:
          finish_reason = response.candidates[0].finish_reason
          safety_ratings = response.candidates[0].safety_ratings
          citation_metadata = response.candidates[0].citation_metadata
          print(f"Response reason: {finish_reason}")
          print(f"Safety rating: {safety_ratings}")
          print(f"Citation metadata: {citation_metadata}")
          if finish_reason == "SAFETY":
            print("The content was blocked by safety filters.")
          elif finish_reason == "RECITATION":
            print("The model started quoting copyrighted material and stopped.")
          elif finish_reason == "OTHER":
            print("The model collapsed or the server cut the connection.")
        wait_a_little(attempt)

      # Done
      else:
        return response

    except google.genai.errors.ServerError as e:
      # Model not found
      if e.code == 404:
        print(f"Model {gemini_model} was not found.")
        raise

      # Permission denied
      elif e.code == 403:
        print("Model denied permission.")
        raise

      # Resource exhausted
      elif e.code == 429:
        print("Resource exhausted. Waiting longer...")
        time.sleep(65 + (random.random() * 10))

      # Other error, treat it as temporary and try again
      else:
        print(f"Temporary GenAI Error ({e.code}): {e.message}")
        wait_a_little(attempt)

    # Other possible temporary errors
    except (google.api_core.exceptions.ServiceUnavailable,
            google.api_core.exceptions.InternalServerError,
            google.api_core.exceptions.TooManyRequests) as e:
      print(f"Temporary Google Error ({e.code}): {e.message}")
      wait_a_little(attempt)

    except google.api_core.exceptions.InvalidArgument as e:
      print(f"Fatal Error: Your prompt or file is invalid. Check your parameters. {e}")
      raise

    except google.api_core.exceptions.Unauthenticated as e:
      print(f"Fatal Error: API Key is invalid or missing. {e}")
      raise

    except Exception as e:
      print(f"Unexpected error occurred: {get_fqn(e)}: {e}")
      raise

  raise Exception(f"Max retries ({max_retries}) exceeded. The server is likely down for a longer period.")



def display_available_models(api_key: str):
  client = genai.Client(api_key = api_key)
  print("--- Available Models ---")
  for model in client.models.list():
    # 'name' is what you use in your generate_content calls
    # 'display_name' is the human-readable version
    print(f"ID: {model.name:40} | Name: {model.display_name}")



def upload(client: genai.Client, file_path: Path):
  # Upload the file to the Media API
  print(f"Uploading {file_path.name}...")
  path_str = str(file_path.resolve())
  uploaded_file = client.files.upload(file = path_str)

  # Wait for the file to be processed
  while uploaded_file.state.name == "PROCESSING":
    print(".", end = "", flush = True)
    time.sleep(2)
    uploaded_file = client.files.get(name = uploaded_file.name)

  # If uploading failed
  if uploaded_file.state.name == "FAILED":
    raise ValueError("File processing failed on Google servers.")

  return uploaded_file



def transcribe_audio(audio_path: Path, api_key: str):
  client = genai.Client(api_key = api_key)

  # Upload audio clip to Google server
  audio_file = upload(client, audio_path)

  # Request Transcription
  try:
    print("Transcribing...")

    # Reply schema
    subtitle_schema = {
      "type"      : "OBJECT",
      "properties": {
        "subtitles": {
          "type" : "ARRAY",
          "items": {
            "type"      : "OBJECT",
            "properties": {
              "start": {
                "type"       : "NUMBER",
                "description": "Time at which the segment begins in seconds (e.g., 12.45)",
                "minimum"    : 0
              },
              "end"  : {
                "type"       : "NUMBER",
                "description": "End at which the segment ends in seconds (e.g., 15.10)",
                "minimum"    : 0
              },
              "text" : {
                "type"       : "STRING",
                "description": "The transcribed text for this segment"
              }
            },
            "required"  : ["start", "end", "text"]
          }
        }
      },
      "required"  : ["subtitles"]
    }

    # Config
    config = types.GenerateContentConfig(
      response_mime_type = "application/json",
      response_schema = subtitle_schema,
      safety_settings = safety_settings,
      system_instruction = transcription_instruction,
      media_resolution = types.MediaResolution.MEDIA_RESOLUTION_LOW,
      top_p = 0.9,
      temperature = 0.0
    )

    # Content
    content = [
      "Generate highly accurate Japanese transcription of this video clip into JSON subtitles.",
      audio_file
    ]

    # Send request to Gemini
    response = generate_with_retry(client, config, content)

  # Delete audio file from server
  finally:
    client.files.delete(name = audio_file.name)

  return response.text



def translate_srt(text: str, working_dir: Path, api_key: str):
  client = genai.Client(api_key = api_key)

  # Save text into a temporary file
  srt_path = generate_temporary_path(working_dir, "srt")
  srt_path.write_text(text, encoding = 'utf-8')

  # Upload the file to the Media API
  srt_file = upload(client, srt_path)

  # Request Transcription
  try:
    print("Translating...")

    # Config
    config = types.GenerateContentConfig(
      safety_settings = safety_settings,
      system_instruction = translation_instruction,
      top_p = 0.9,
      temperature = 0.3
    )

    # Content
    content = [
      "Translate this SRT file from Japanese to English.",
      srt_file
    ]

    # Send request to Gemini
    response = generate_with_retry(client, config, content)

  # Delete audio file from server
  finally:
    client.files.delete(name = srt_file.name)

  return response.text
