import threading

from app import sock
from api_functions.deepgram_api_functions import start_deepgram_stream
from config.config import ELEVENLABS_AUDIO_OUTPUT_FORMAT, WEBSOCKET_URL
from flask import Blueprint, request, jsonify
from queue import Queue
from services.call_state_service import add_call_state, delete_call_state, get_call_state
from services.agent_service import get_agent
from services.audio_processing_service import process_transcripts, send_responses

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return 'Hello from Flask via Ngrok! Go to this route to confirm the server is running.'

@main.route("/webhooks/answer", methods=["GET", "POST"])
def answer_call():
    """
    Vonage calls this endpoint when the call is answered. We return an NCCO instructing Vonage to connect the call audio via WebSocket.
    Then we will use the WebSocket to stream the call audio to do the deepgram/openai/11labs logic and send it back to Vonage.
    """
    call_uuid = request.args.get("uuid")
    if not call_uuid:
         print("Error: Vonage UUID not found in request.")
         return jsonify({"error": "Vonage UUID missing"})
    
    test_agent_id = request.args.get("agent_id")
    if not test_agent_id:
        print("Error: Test agent ID not found in request.")
        return jsonify({"error": "Test agent ID missing"})

    call_state_id = add_call_state(call_uuid, test_agent_id)

    # Connect the call to the WebSocket passing in the call_state_id with agent info
    ws_url = f"wss://{WEBSOCKET_URL}/socket/{call_state_id}"
    ncco = [
        {
            "action": "connect",
            "endpoint": [
                {
                    "type": "websocket",
                    "uri": ws_url,
                    "content-type": "audio/l16;rate=16000",
                    "headers": {
                        "call_state_id": call_state_id
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
    """
    print(f"Call status changed: {request.json}")
    return "200"

@sock.route("/socket/<call_state_id>", methods=["GET"])
def websocket_stream(ws, call_state_id):
    print(f"WebSocket connection opened for call state: {call_state_id}")

    try:
        call_state = get_call_state(call_state_id)
        agent = get_agent(call_state.agent_id)
    except ValueError as e:
        print(f"Error: {e}")
        ws.close()
        return ""

    # Set up the queues for STT, LLM inference and TTS/responding to Vonage
    audio_queue = Queue() # Queue of audio chunks from Vonage for TTS with Deepgram
    transcript_queue = Queue() # Queue of completed utterances (text) from Deepgram to send to the OpenAI LLM for inference
    response_queue = Queue() # Queue of responses from the OpenAI LLM for STT with ElevenLabs (and ultimately send to Vonage)

    # Lock for thread-safe sending via ws.send
    send_lock = threading.Lock()

    # Start the Deepgram stream thread which sends audio chunks from audio_queue to Deepgram and adds completed utterances into transcript_queue
    dg_thread = threading.Thread(target=start_deepgram_stream, args=(audio_queue, transcript_queue, agent.stt_model_id))
    dg_thread.start()

    # Start a thread to process full transcripts, generate a response from the LLM, and do STT with ElevenLabs
    transcript_thread = threading.Thread(target=process_transcripts, args=(
                                                                        transcript_queue, 
                                                                        response_queue, 
                                                                        agent.system_prompt, 
                                                                        agent.voice_id, 
                                                                        agent.tts_model_id,
                                                                        agent.llm_model_id,
                                                                        ELEVENLABS_AUDIO_OUTPUT_FORMAT))
    transcript_thread.start()

    # Start response sending thread (sends TTS audio back to the Vonage client)
    response_thread = threading.Thread(target=send_responses, args=(ws, response_queue, send_lock))
    response_thread.start()

    try:
        # Continually receive audio chunks from Vonage and put them into the audio queue
        while True:
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

    finally:
        print(f"Cleaning up resources for call state: {call_state_id}")

        # Might need to be careful about how we join threads here, especially response_thread if ws is already closed
        dg_thread.join()
        transcript_thread.join()
        response_thread.join()

         # Remove the state for this call to prevent memory leaks
        delete_call_state(call_state_id)

    print(f"WebSocket connection closed for {call_state_id}")
    return ""
