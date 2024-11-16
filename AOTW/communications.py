import base64
import os
import json
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify


class Authentication:
    """
    A class for handling OAuth 2.0 authentication for Google and Spotify APIs.

    Takes an API name and scopes as arguments.
    """

    def __init__(self, api_name, scopes, token_filename):
        self.api_name = api_name
        self.scopes = scopes
        self.token_filename = token_filename
        self.service = None

    def _get_credentials(self):
        """
        Retrieves credentials from the token file or initiates a new authentication flow.

        Returns:
            A dictionary containing the cached credentials or None if not found.
        """

        if os.path.exists(self.token_filename):
            try:
                with open(self.token_filename, "r") as token_file:
                    return json.load(token_file)
            except:
                pass  # Continue to obtain new creds
        return None

    def _authenticate(self):

        creds = None
        if os.path.exists(self.token_filename):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_filename, self.scopes
                )
            except:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    self.scopes,
                    redirect_uri=f"http://localhost:{57738}/",
                )
                creds = flow.run_local_server(port=57738)

            with open(self.token_filename, "w") as token:
                token.write(creds.to_json())
        try:
            service = build(self.api_name, "v1", credentials=creds)
            self.service = service
            return service

        except HttpError as error:
            print(f"An error occurred during authentication: {error}")
            raise Exception(f"Authentication failed for {self.api_name}")

    def _authenticate_spotify(self):
        """
        Authenticates to the specified API using OAuth 2.0.

        Raises:
            Exception: If authentication fails.
        """

        # creds = self._get_credentials()
        creds = None
        if not creds:
            try:
                with open("spotify_credentials.json", "r") as f:
                    credentials = json.load(f)
                auth_manager = SpotifyOAuth(
                    client_id=credentials["client_id"],
                    client_secret=credentials["client_secret"],
                    redirect_uri=credentials["redirect_uri"],
                    scope=" ".join(self.scopes),  # Combine scopes into a single string
                )
                self.service = Spotify(auth_manager=auth_manager)
            except FileNotFoundError:
                print(
                    "spotify_credentials.json not found. Please create it with your credentials."
                )
                exit(1)
            except Exception as e:
                print(f"Failed to authenticate with Spotify: {e}")
                raise

            # Save credentials for future use (optional)
            with open(self.token_filename, "w") as token_file:
                json.dump(self.service.auth_manager.get_cached_token(), token_file)

        else:
            # Use existing credentials
            auth_manager = SpotifyOAuth(**creds)
            self.service = Spotify(auth_manager=auth_manager)

    def get_service(self):
        """
        Returns the authenticated service object.

        Raises:
            Exception: If authentication hasn't been performed yet.
        """

        if not self.service:
            if self.api_name == "spotify":
                self._authenticate_spotify()
            else:
                self._authenticate()

        return self.service


class SpotifyAPI:
    """
    A class for interacting with the Spotify API.

    Handles authentication and provides methods for searching albums, creating playlists,
    and updating the AOTW playlist.
    """

    SCOPES = [
        "playlist-modify-public",
        "playlist-modify-private",
        "user-library-read",
    ]

    def __init__(self):
        """
        Initializes the Spotify client.
        """

        self.auth = Authentication("spotify", self.SCOPES, "spotify_token.json")
        self.sp = self.auth.get_service()

    def search_album(self, artist_name, album_name):
        """
        Searches for an album on Spotify by artist and album name, prioritizing the most popular result.

        Args:
            artist_name: The name of the artist.
            album_name: The name of the album.

        Returns:
            The URI of the most popular matching album, or None if no match is found.

        Raises:
            Exception: If Spotify client is not authenticated.
        """

        if not self.sp:
            raise Exception("Spotify client not authenticated")

        query = f"{artist_name} {album_name}"
        results = self.sp.search(q=query, type="album")

        albums = results["albums"]["items"]

        if not albums:
            return None

        return albums[0]["uri"]

    def overwrite_playlist_with_album(self, playlist_id, album_uri):
        """
        Overwrites an existing playlist with the tracks of a given album.

        Args:
            playlist_id: The ID of the playlist to update.
            album_uri: The URI of the album to add to the playlist.

        Raises:
            Exception: If Spotify client is not authenticated or an error occurs.
        """

        if not self.sp:
            raise Exception("Spotify client not authenticated")

        # Clear the existing playlist
        self.sp.playlist_replace_items(playlist_id, [])

        # Get the album's track URIs
        album_tracks = self.sp.album_tracks(album_uri)
        track_uris = [track["uri"] for track in album_tracks["items"]]

        # Add the tracks to the playlist
        self.sp.playlist_add_items(playlist_id, track_uris)
        print(f"Playlist '{playlist_id}' updated with album '{album_uri}'")


class GmailAPI:
    """
    A class for interacting with the Gmail API.

    Handles authentication (using Authentication class), message creation, and email sending.
    """

    def __init__(self, sender_email):
        self.sender_email = sender_email
        self.auth = Authentication(
            "gmail",
            ["https://www.googleapis.com/auth/gmail.modify"],
            "gmail_token.json",
        )

    def create_message(self, sender, recipients, subject, body):
        """
        Creates a message for an email.

        Args:
            sender: Email address of the sender.
            recipients: List of email addresses of the recipients.
            subject: Subject of the email.
            body: Email body content.

        Returns:
            A message object encoded in base64url.
        """

        message_bytes = (
            f'To: {", ".join(recipients)}\r\n'
            f"From: {sender}\r\n"
            f"Subject: {subject}\r\n\r\n"
            f"{body}"
        ).encode("utf-8")

        return base64.urlsafe_b64encode(message_bytes).decode()

    def send_email(self, recipients, subject, body):
        """
        Sends an email using the Gmail API.

        Args:
            recipients: List of email addresses of the recipients.
            subject: Subject of the email.
            body: Email body content.

        Raises:
            Exception: If email sending fails or authentication fails.
        """

        try:
            service = self.auth.get_service()
            message = self.create_message(self.sender_email, recipients, subject, body)
            service.users().messages().send(
                userId="me", body={"raw": message}
            ).execute()
            print("Email sent!")
        except Exception as e:
            print(f"An error occurred: {e}")
            raise


class FormAPI:
    """
    A class for interacting with the Google Forms API.

    Handles authentication (using Authentication class), and reading responses.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/forms.responses.readonly",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self):
        self.auth = Authentication(
            "forms", self.SCOPES, "forms_token.json"
        )  # Use provided scopes and token filename

    def _log_response(response_data):
        with open("submissions.json", "a+") as f:
            json.dump(response_data, f, indent=4)
            f.write("\n")

    def _parse_aotw_response(self, response):
        response_data = {
            "user_email": response["respondentEmail"],
            "timestamp": response["lastSubmittedTime"],
            "album": response["answers"]["230e86f5"]["textAnswers"]["answers"][0][
                "value"
            ],
            "artist": response["answers"]["768e031c"]["textAnswers"]["answers"][0][
                "value"
            ],
        }
        return response_data

    def _read_responses(self, form_id):
        """
        Reads all responses to the specified Google Form.

        Args:
            form_id: The ID of the Google Form.

        Returns:
            A list of dictionaries, where each dictionary represents a response and contains metadata (e.g., user email, timestamp) and answers.

        Raises:
            Exception: If reading responses fails.
        """

        try:
            service = self.auth.get_service()
            response = service.forms().responses().list(formId=form_id).execute()
            responses = response.get("responses", [])

            response_list = []
            for r in responses:
                response_data = self._parse_aotw_response(r)
                response_list.append(response_data)

            return response_list
        except HttpError as error:
            print(f"An error occurred while reading responses: {error}")
            raise Exception("Failed to read responses")

    def get_form_submissions(
        self, form_id, user_filter=None, min_timestamp_filter=None
    ):
        """
        Gets the latest response based on specified filters.

        Args:
            form_id: The ID of the Google Form.
            user_filter: Optional email address to filter responses by user.
            min_timestamp_filter: Optional minimum timestamp to filter responses.

        Returns:
            A dictionary containing the extracted response data or None if no matching response is found.
        """

        responses = self._read_responses(form_id)
        filtered_responses = responses

        if user_filter:
            filtered_responses = [
                r for r in filtered_responses if r["user_email"] == user_filter
            ]

        if min_timestamp_filter:
            filtered_responses = [
                r
                for r in filtered_responses
                if datetime.datetime.fromisoformat(r["timestamp"])
                >= min_timestamp_filter
            ]

        if not filtered_responses:
            return None
        filtered_responses.sort(key=lambda x: x["timestamp"], reverse=True)
        return filtered_responses


# Example usage
# if __name__ == "__main__":
#     forms_api = FormAPI()
#     x = forms_api.read_responses(form_id="1xuOX73x4e9QzD_gSoPYUKln3eWdXoVsP2xFQbHJBsts")
