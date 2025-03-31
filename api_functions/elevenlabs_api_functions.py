from elevenlabs import ElevenLabs
from config.config import ELEVENLABS_API_KEY

eleven_labs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def convert_text_to_speech(
        text: str, 
        voice_id: str, 
        output_format: str, 
        model_id: str):
    """
    Convert text to speech using ElevenLabs API.
    """
    return eleven_labs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format=output_format,
            text=text,
            model_id=model_id,
    )