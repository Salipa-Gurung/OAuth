import base64
import hashlib
import os
import click
import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

AUTH0_DOMAIN = "dev-it18xixeeb14m8xg.us.auth0.com"
CLIENT_ID = "Yall6OfLtalawUhezKETd6Nh0YaQO9zY"
REDIRECT_URI = "http://localhost:8080/callback"
AUTHORIZATION_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
SCOPE = "openid profile email offline_access"
AUDIENCE = "https://oauth-with-pkce"


def generate_pkce_pair():
    # Create high-entropy code_verifier
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
    # Create code_challenge
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


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
    code_verifier, code_challenge = generate_pkce_pair()

    # Build authorization URL with PKCE
    auth_url = (
        f"{AUTHORIZATION_URL}?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={SCOPE}&"
        f"audience={AUDIENCE}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )

    # Start local server to catch the code
    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    webbrowser.open(auth_url)
    print("Waiting for authorization...")
    server.handle_request()
    code = OAuthCallbackHandler.code

    if not code:
        click.echo("Failed to get authorization code.")
        return

    # Exchange code for token using PKCE (no client_secret)
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }

    response = requests.post(TOKEN_URL, json=token_data)
    if response.status_code == 200:
        token_info = response.json()
        print("\n\ntoken_info:", token_info)

        access_token = token_info.get("access_token")
        click.echo(f"\nAccess Token:\n{access_token}")
    else:
        click.echo(f"Token exchange failed: {response.text}")


if __name__ == "__main__":
    oauth_login()
