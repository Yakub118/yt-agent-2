"""
Get YouTube Refresh Token Script
Run this locally once to get your YouTube OAuth refresh token.
"""
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import webbrowser
from google.oauth2.webserver import ClientConfig
from google_auth_oauthlib.flow import Flow

# Configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = "http://localhost:8080/"
CLIENT_CONFIG = None


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback."""

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        global CLIENT_CONFIG
        
        if self.path.startswith("/?"):
            query_params = parse_qs(self.path[2:])
            code = query_params.get("code", [None])[0]
            
            if code:
                # Exchange code for tokens
                flow.fetch_token(code=code)
                credentials = flow.credentials
                
                print("\n" + "=" * 60)
                print("SUCCESS! Your credentials:")
                print("=" * 60)
                print(f"\nRefresh Token: {credentials.refresh_token}")
                print(f"Client ID: {CLIENT_CONFIG['web']['client_id']}")
                print(f"Client Secret: {CLIENT_CONFIG['web']['client_secret']}")
                print("\n" + "=" * 60)
                print("Save these values in your GitHub Secrets:")
                print("  YOUTUBE_CLIENT_ID:", CLIENT_CONFIG['web']['client_id'])
                print("  YOUTUBE_CLIENT_SECRET:", CLIENT_CONFIG['web']['client_secret'])
                print("  YOUTUBE_REFRESH_TOKEN:", credentials.refresh_token)
                print("=" * 60 + "\n")
                
                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                    <html>
                        <body>
                            <h1>Success!</h1>
                            <p>You can close this window and return to the terminal.</p>
                            <p>Your refresh token has been displayed in the terminal.</p>
                        </body>
                    </html>
                """)
                
                # Stop server after successful callback
                import threading
                threading.Thread(target=self.server.shutdown).start()
            else:
                self.send_error(400, "No code received")
        else:
            self.send_error(404, "Not found")


def get_refresh_token(client_secret_file: str = "client_secret.json"):
    """
    Get YouTube OAuth refresh token.
    
    Args:
        client_secret_file: Path to client_secret.json from Google Cloud Console
    """
    global CLIENT_CONFIG
    
    # Check if client secret file exists
    if not os.path.exists(client_secret_file):
        print(f"Error: {client_secret_file} not found!")
        print("\nPlease download your OAuth 2.0 credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to APIs & Services > Credentials")
        print("4. Create OAuth 2.0 Client ID (Desktop app)")
        print("5. Download the JSON file and save it as 'client_secret.json'")
        return None
    
    # Load client configuration
    with open(client_secret_file, "r") as f:
        CLIENT_CONFIG = json.load(f)
    
    print("Starting OAuth flow...")
    print(f"Scopes: {SCOPES}")
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt="consent")
    
    print(f"\nOpening browser for authentication...")
    print(f"If browser doesn't open, visit: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    print(f"\nListening on {REDIRECT_URI}...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.serve_forever()
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube OAuth Refresh Token Generator")
    print("=" * 60)
    print()
    print("This script will help you get a YouTube OAuth refresh token.")
    print("You'll need a client_secret.json file from Google Cloud Console.")
    print()
    
    # Try to get refresh token
    result = get_refresh_token()
    
    if result:
        print("OAuth flow completed!")
    else:
        print("Failed to get refresh token.")
