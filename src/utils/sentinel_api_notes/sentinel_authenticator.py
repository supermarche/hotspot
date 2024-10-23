from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import secrets

def authenticate_session():
    # Replace with your client ID and client secret
    client_id = secrets.client_name  # e.g., 'your_client_id'
    client_secret = secrets.client_secret  # e.g., 'your_client_secret'

    # OAuth session setup
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    # Obtain the access token
    token = oauth.fetch_token(
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        client_secret=client_secret,
        include_client_id=True
    )

    return oauth, token
