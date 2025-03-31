from api_functions.vonage_api_functions import make_outbound_call
from config.config import VONAGE_PHONE_NUMBER, WEBSOCKET_URL, CUSTOMER_PHONE_NUMBER

if __name__ == "__main__":
    params = { "agent_id": "agent_001" }
    answer_url = f"https://{WEBSOCKET_URL}/webhooks/answer"
    event_url = f"https://{WEBSOCKET_URL}/webhooks/event"

    # will need to define a max duration for the call and pass it in as a param to answer query as well
    print(make_outbound_call(
                to_number=CUSTOMER_PHONE_NUMBER,
                from_number=VONAGE_PHONE_NUMBER,
                answer_url=answer_url,
                event_url=event_url,
                params=params))