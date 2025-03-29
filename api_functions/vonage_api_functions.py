from vonage import Auth, Vonage
from vonage_jwt import JwtClient
from vonage_voice.models import CreateCallRequest, Phone, ToPhone

from config.config import VONAGE_APPLICATION_ID, VONAGE_PATH_TO_PRIVATE_KEY

def generate_vonage_jwt_token(application_id: str, path_to_private_key: str, paths: dict, claims: dict):
    """
    Generate a Vonage JWT token for the given application ID and private key path with the given paths and claims.
    """
    jwt_client = JwtClient(application_id, path_to_private_key)

    # Build the full claims dictionary
    full_claims = claims or {}
    if paths:
        full_claims['paths'] = paths

    return jwt_client.generate_application_jwt(full_claims)

def make_outbound_call(to_number: str, from_number: str, answer_url: str):
    """
    Make an outbound call to the given number with the given answer URL.
    """
    with open(VONAGE_PATH_TO_PRIVATE_KEY, "r") as key_file:
        private_key = key_file.read()

    client = Vonage(
        Auth(
            application_id=VONAGE_APPLICATION_ID,
            private_key=private_key,
        )
    )

    response = client.voice.create_call(
        CreateCallRequest(
            answer_url=[answer_url],
            to=[ToPhone(number=to_number)],
            from_=Phone(number=from_number),
        )
    )

    return response