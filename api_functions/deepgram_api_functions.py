from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from config.config import DEEPGRAM_API_KEY

deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

def start_deepgram_stream(audio_queue, transcript_queue, model):
    """
    This function starts a Deepgram websocket connection and listens for audio chunks.
    Using audio_queue it sends audio chunks to Deepgram and receives transcript chunks.
    These transcript chunks are combined until a speech_final or utterance_end is detected.
    Once combined, the full question/utterance is put in the transcript queue (to eventually 
    be used by the LLM to generate an answer in the inference layer).
    
    Note that speech_final and utterance_end is just a heuristic and not a perfect way to determine
    when the user is done speaking.
    """
    # Create a websocket connection (API v1)
    dg_connection = deepgram.listen.websocket.v("1")

    # Accumulate transcript parts for the current utterance/sentence
    current_utterance = []

    def on_transcript(self, result, **kwargs):
        # We use nonlocal and not a parameter for current_utterance because these functions are 
        # event_handlers used by deepgram so we don't get to control the function signatures 
        # (they are predetermined by deepgram API) but we need to modify current_utterance here.
        # I've never had an actual use case for nonlocal before, so this is kind of cool
        nonlocal current_utterance

        # Extract the transcript part from the result
        transcript_part = result.channel.alternatives[0].transcript
        if transcript_part:
            current_utterance.append(transcript_part)

        # Check if Deepgram marks this part as final (speech_final true)
        is_final = getattr(result.channel.alternatives[0], "speech_final", False)
        if is_final:
            full_transcript = " ".join(current_utterance).strip()
            print(f"Final transcript (speech_final): {full_transcript}")
            transcript_queue.put(full_transcript)
            current_utterance.clear()  # Reset for the next utterance

    def on_utterance_end(self, utterance_end, **kwargs):
        nonlocal current_utterance

        # If an UtteranceEnd event arrives and we have accumulated transcript parts, treat that as the end of the utterance
        if current_utterance:
            full_transcript = " ".join(current_utterance).strip()
            #print(f"UtteranceEnd detected transcript: {full_transcript}")
            transcript_queue.put(full_transcript)
            current_utterance.clear()

    # Register event handlers
    # Transcript events (which include interim and final transcript parts)
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)
    # Register the UtteranceEnd event; Deepgram will send this when a gap in speech is detected.
    dg_connection.on("UtteranceEnd", on_utterance_end)

    # Configure Deepgram with the necessary options for endpointing
    options = LiveOptions(
        model=model,
        language="en-US",
        smart_format=True,
        encoding="linear16",
        channels=1,
        sample_rate=16000,
        interim_results=True,
        utterance_end_ms="1000",  # Wait for 1000ms of silence before signaling end of utterance
        vad_events=True,
        endpointing=300  # Endpoint after 300ms of silence (if applicable)
    )

    if not dg_connection.start(options):
        print("Failed to start Deepgram connection")
        return

    # Continuously send audio chunks from the audio_queue to Deepgram
    while True:
        chunk = audio_queue.get()
        if chunk is None:
            break
        dg_connection.send(chunk)

    dg_connection.finish()
    print("Deepgram stream finished.")
