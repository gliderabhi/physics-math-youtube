from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from . import config


def run_auth_flow(channel: str, port: int = 8080) -> None:
    """Runs on a headless server: binds the OAuth callback to a fixed port (so it can be
    reached via an SSH tunnel: `ssh -L <port>:localhost:<port> <server>`), prints the consent
    URL instead of trying to open a local browser, and waits for the redirect to come back
    through the tunnel once you finish the Google login in a browser on your own machine."""
    secret_path = config.client_secret_path(channel)
    token_path = config.token_path(channel)
    if not secret_path.exists():
        raise FileNotFoundError(
            f"Missing {secret_path}. Follow docs/YOUTUBE_SETUP.md to download it from Google Cloud Console "
            f"for the '{channel}' channel first."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), config.YOUTUBE_SCOPES)
    print(f"Open an SSH tunnel from your browser machine first: ssh -L {port}:localhost:{port} <this host>")
    print("Then open the URL below in a browser there — it will show an account/channel picker "
          "(if it doesn't, Google defaults to your personal channel, not a Brand Account):\n")
    # Without prompt=select_account, Google silently skips the Brand Account picker and
    # authorizes whichever channel is "default" (usually your personal one) — a known issue,
    # not specific to this app. This forces the picker to actually appear every time.
    creds = flow.run_local_server(port=port, open_browser=False, prompt="consent select_account")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Saved credentials for channel '{channel}' to {token_path}")


def get_credentials(channel: str) -> Credentials:
    token_path = config.token_path(channel)
    if not token_path.exists():
        raise FileNotFoundError(f"No token for channel '{channel}'. Run `python main.py auth --channel {channel}` first.")
    creds = Credentials.from_authorized_user_file(str(token_path), config.YOUTUBE_SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    return creds
