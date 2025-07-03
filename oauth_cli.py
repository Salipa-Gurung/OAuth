import click
import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

AUTH0_DOMAIN = ""
CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT_URI = "http://localhost:8080/callback"
AUTHORIZATION_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
SCOPE = "openid profile email offline_access"


# This will capture the code
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        if "code" in query:
            OAuthCallbackHandler.code = query["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorization successful. You can close this tab.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code.")


@click.command()
def oauth_login():
    # Build authorization URL
    auth_url = (
        f"{AUTHORIZATION_URL}?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}&"
        f"audience=https://secure-python-flask-api"  # Optional depending on setup
    )

    # Start temporary server to catch the code
    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    webbrowser.open(auth_url)

    print("Waiting for authorization...")
    server.handle_request()  # Handles one request, then stops
    code = OAuthCallbackHandler.code

    if not code:
        click.echo("Failed to get authorization code.")
        return

    # Exchange code for token
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, json=token_data)
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get("access_token")
        click.echo(f"\nAccess Token:\n{access_token}")
    else:
        click.echo(f"Token exchange failed: {response.text}")


if __name__ == "__main__":
    oauth_login()
