from queue import Queue
from api_functions.openai_api_functions import generate_llm_response
from api_functions.elevenlabs_api_functions import convert_text_to_speech

def process_transcripts(
        transcript_queue: Queue, 
        response_queue: Queue, 
        agent_persona_system_prompt: str, 
        voice_id: str, 
        tts_model_id: str,
        llm_model_id: str,
        output_format: str
    ):
    """
    Worker function that continuously processes complete transcripts from the TTS service:
      - For each transcript:
         1) Call the LLM to generate a response.
         2) Call ElevenLabs TTS to convert that response to audio bytes.
         3) Chunk those bytes and place them onto response_queue.
    """
    while True:
        transcript = transcript_queue.get()
        if transcript is None:
            break  # Exit signal
        
        print(f"\n\n\nProcessing transcript: {transcript}")
        llm_response = generate_llm_response(agent_persona_system_prompt, transcript, llm_model_id) # TODO: need to make sure we also add the context of the previous parts of the conversation to the GPT
        print(f"LLM response: {llm_response}")
        
        # Get a generator of audio bytes from ElevenLabs
        audio_generator = convert_text_to_speech(
            text=llm_response,
            voice_id=voice_id,
            output_format=output_format,
            model_id=tts_model_id,
        )

        # Send the audio data to the response queue in 640-byte frames
        for audio_chunk in audio_generator:
            # We must ensure each piece is exactly 640 bytes (20ms at 16kHz, 16-bit) to work with Vonage
            for frame in chunk_bytes(audio_chunk, chunk_size=640):
                response_queue.put(frame) # If we ever have a large amount of TTS data, we can add a short sleep here to control playback rate for Vonage (20ms)

def chunk_bytes(data: bytes, chunk_size: int = 640):
    """
    Yield successive chunk_size-length chunks from data.
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def send_responses(ws, response_queue, send_lock):
    """
    Worker function that continuously sends audio responses from the response queue
    to the client via the WebSocket.
    """
    while True:
        audio_data = response_queue.get()
        #print(f"Sending audio data: {audio_data}")
        if audio_data is None:
            break
        with send_lock:
            ws.send(audio_data)