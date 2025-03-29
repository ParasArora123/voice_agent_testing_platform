import threading
import uuid

from app import sock
from api_functions.deepgram_api_functions import start_deepgram_stream
from api_functions.openai_api_functions import generate_llm_response
from api_functions.elevenlabs_api_functions import convert_text_to_speech
from config.config import SYSTEM_PROMPTS, call_states, ELEVENLABS_AUDIO_OUTPUT_FORMAT
from queue import Queue
from flask import Blueprint, request, jsonify

main = Blueprint('main', __name__)

@main.route("/webhooks/answer", methods=["GET", "POST"])
def answer_call():
    """
    Vonage calls this endpoint when the call is answered.
    We return an NCCO instructing Vonage to connect the call audio via WebSocket.
    Then we will use the WebSocket to stream the call audio to do the deepgram/openai/11labs logic and send it back to Vonage.
    
    call_uuid = request.args.get("uuid")  # or from JSON depending on method
    # You might identify which system prompt you want by query param or internal logic
    agent_name = request.args.get("agent", "agent1")
    
    # Create a new call state
    call_state_id = str(uuid.uuid4())
    call_states[call_state_id] = {
        "vonage_uuid": call_uuid,
        "agent_name": agent_name,
        "system_prompt": SYSTEM_PROMPTS.get(agent_name, ""),
        "partial_text": "",
    }

    # Suppose your WebSocket server is wss://<your_host>:<ws_port>...
    # (Vonage expects wss, but for local dev you can do ws if you bypass TLS in the config)
    ws_url = f"wss://<your-public-websocket-domain>/stream/{call_state_id}"

    ncco = [
        {
            "action": "connect",
            "endpoint": [
                {
                    "type": "websocket",
                    "uri": ws_url,
                    "content-type": "audio/l16;rate=16000",
                    "headers": {
                        "callStateId": call_state_id
                    }
                }
            ]
        }
    ]
    return jsonify(ncco)

    TODO:
    - We need to add a unique ID and pass it as a header and query param to the web socket 
      since we could be dealing with multiple calls at once and need to know which system prompt
      to give the LLM.
    """

    ws_url = "wss://<your-domain>/ws/socket"
    ncco = [
        {
            "action": "connect",
            "endpoint": [
                {
                    "type": "websocket",
                    "uri": ws_url, # this needs to include the route to the websocket at the end
                    "content-type": "audio/l16;rate=16000",
                    "headers": {
                        "someCustomHeader": "testHeader"
                    }
                }
            ]
        }
    ]
    return jsonify(ncco)
    

@main.route("/webhooks/event", methods=["POST"])
def event_webhook():
    """
    Vonage sends call status updates here.
    
    data = request.json
    call_uuid = data.get("uuid")
    status = data.get("status")

    print(f"Call {call_uuid} status: {status}")
    return ("", 204)
    """
    print(f"Call status changed: {request.json}")
    return "200"

def process_transcripts(
        transcript_queue: str, 
        response_queue: str, 
        agent_persona_system_prompt: str, 
        voice_id: str, 
        output_format: str, 
        model_id: str):
    """
    Worker function that continuously processes complete transcripts from a TTS service.
    The LLM is called only once per complete utterance to generate a response.
    """
    while True:
        transcript = transcript_queue.get()
        if transcript is None:
            break  # Exit signal
        
        llm_response = generate_llm_response(agent_persona_system_prompt, transcript)
        audio_data = convert_text_to_speech(llm_response, voice_id, output_format, model_id)
        response_queue.put(audio_data)

def send_responses(ws, response_queue, send_lock):
    """
    Worker function that continuously sends audio responses from the response queue
    to the client via the WebSocket.
    """
    while True:
        audio_data = response_queue.get()
        if audio_data is None:
            break
        with send_lock:
            ws.send(audio_data)

@sock.route("/socket", methods=["GET"])
def websocket_stream(ws):
    # TODO: Get the agent_persona_system_prompt, voice_id, and model_id from the call_states dictionary. Needs to be from call_states dict since multiple calls could be streaming in at the same time and we have to know which one to use our system prompt for?

    audio_queue = Queue() # Queue of audio chunks from Vonage for TTS with Deepgram
    transcript_queue = Queue() # Queue of completed utterances (text) from Deepgram to send to the OpenAI LLM for inference
    response_queue = Queue() # Queue of responses from the OpenAI LLM for STT with ElevenLabs (and ultimately send to Vonage)

    # Lock for thread-safe sending via ws.send
    send_lock = threading.Lock()

    # Start the Deepgram stream thread which sends audio chunks from audio_queue to Deepgram and adds completed utterances into transcript_queue
    dg_thread = threading.Thread(target=start_deepgram_stream, args=(audio_queue, transcript_queue))
    dg_thread.start()

    # Start a thread to process full transcripts, generate a response from the LLM, and do STT with ElevenLabs
    transcript_thread = threading.Thread(target=process_transcripts, args=(
                                                                        transcript_queue, 
                                                                        response_queue, 
                                                                        agent_persona_system_prompt, 
                                                                        voice_id, 
                                                                        ELEVENLABS_AUDIO_OUTPUT_FORMAT, 
                                                                        model_id))
    transcript_thread.start()

    # Start response sending thread (sends TTS audio back to the Vonage client)
    response_thread = threading.Thread(target=send_responses, args=(ws, response_queue, send_lock))
    response_thread.start()

    while True:
        try:
            data = ws.receive()
            if data is None:
                print("WebSocket closed by client.")
                audio_queue.put(None)
                transcript_queue.put(None)
                response_queue.put(None)
                break
            
            # Put the received audio data into the audio queue, kicking off the Deepgram stream and rest of the pipeline
            audio_queue.put(data)

        except Exception as e:
            print(f"Error in WebSocket loop: {e}")
            audio_queue.put(None)
            transcript_queue.put(None)
            response_queue.put(None)
            break

    dg_thread.join()
    transcript_thread.join()
    response_thread.join()

    return ""