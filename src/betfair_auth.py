"""
TennisTrader -- Betfair Authentication
Reuses same cert/credentials as ScoreTrader.
"""

import os
import betfairlightweight
from dotenv import load_dotenv

load_dotenv()


def get_client():
    """Authenticate with Betfair API. Returns authenticated client."""
    username  = os.getenv("BETFAIR_USERNAME")
    password  = os.getenv("BETFAIR_PASSWORD")
    app_key   = os.getenv("BETFAIR_APP_KEY")
    cert_path = os.getenv("BETFAIR_CERT_PATH")
    key_path  = os.getenv("BETFAIR_KEY_PATH")

    if not all([username, password, app_key, cert_path, key_path]):
        raise EnvironmentError(
            "Missing Betfair credentials. Check your .env file."
        )

    client = betfairlightweight.APIClient(
        username=username,
        password=password,
        app_key=app_key,
        cert_files=(cert_path, key_path),
    )
    client.login()
    return client


if __name__ == "__main__":
    try:
        client = get_client()
        print("Betfair authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
