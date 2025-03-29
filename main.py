
from api_functions.vonage_api_functions import make_outbound_call
from config.config import VONAGE_PHONE_NUMBER

if __name__ == "__main__":
    print(make_outbound_call("16507014090", VONAGE_PHONE_NUMBER, "https://raw.githubusercontent.com/nexmo-community/ncco-examples/gh-pages/text-to-speech.json"))