from sentinelhub import SHConfig
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from src.utils.sentinel_secrets import client_name, client_secret


def authenticate_session():
    client_id = client_name

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)

    # Fetch token
    token = oauth.fetch_token(
        token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        client_secret=client_secret,
        include_client_id=True
    )

    return oauth, token


def load_config():
    config = SHConfig()

    # Add your Sentinel Hub API credentials
    config.sh_client_id = client_name
    config.sh_client_secret = client_secret
    config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
    config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    # Get the OAuth2 token
    oauth, token = authenticate_session()

    # Set the access token in the configuration
    config.instance_id = None  # If no instance ID is used
    config.sh_token = token['access_token']  # Set the token manually

    return config
