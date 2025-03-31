import os
from dotenv import load_dotenv

# Optional: Load .env file automatically
load_dotenv()

VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")
VONAGE_PATH_TO_PRIVATE_KEY = os.getenv("VONAGE_PATH_TO_PRIVATE_KEY")
VONAGE_APPLICATION_ID = os.getenv("VONAGE_APPLICATION_ID")
VONAGE_PHONE_NUMBER = os.getenv("VONAGE_PHONE_NUMBER")
CUSTOMER_PHONE_NUMBER = os.getenv("CUSTOMER_PHONE_NUMBER")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AUDIO_OUTPUT_FORMAT = "pcm_16000"

WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")

# Optional global state, though consider moving this to a better abstraction later
call_states = {}