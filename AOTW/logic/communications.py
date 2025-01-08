import base64
import os
import json
import datetime

from google.auth import default
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google.cloud import secretmanager_v1 as secrets
from google.auth.exceptions import DefaultCredentialsError
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from google.cloud import storage
from openai import OpenAI
from email.mime.text import MIMEText


class CredentialsManager:
    """Manages credentials, handling local files and Google Secret Manager."""

    def __init__(self):
        pass

    def get_gcp_credentials(scopes=None):
        """Gets Google Cloud credentials, handling refresh and validation."""
        try:
            credentials, _ = default(scopes=scopes)
        except DefaultCredentialsError as e:
            print(f"Error getting default credentials: {e}")
            print(
                "Check GOOGLE_APPLICATION_CREDENTIALS or 'gcloud auth application-default login'."
            )
            raise

        try:
            storage.Client(credentials=credentials).list_buckets(
                max_results=1
            )  # Validate with API call
            return credentials
        except Exception as e:
            if (
                hasattr(credentials, "expired")
                and credentials.expired
                and hasattr(credentials, "refresh_token")
                and credentials.refresh_token
            ):
                try:
                    credentials.refresh(Request())
                    storage.Client(credentials=credentials).list_buckets(
                        max_results=1
                    )  # Validate with API call after refresh
                    return credentials
                except Exception as refresh_err:
                    print(f"Credentials refresh failed: {refresh_err}")
            print(f"API call failed: {e}")
            raise

    def get_spotify_credentials(self, local_credentials: dict = None, scopes=None):
        # use local credentials file
        if local_credentials:
            credentials = local_credentials
        else:
            # Use GCP secrets
            credentials = json.loads(self.get_secret_value("spotify_credentials"))
        if all(
            key in credentials for key in ["client_id", "client_secret", "redirect_uri"]
        ):
            return credentials
        else:
            raise ValueError(
                "Missing required Spotify credentials in local_credentials"
            )

    def get_spotify_client(self, scopes, local_credentials):
        """Creates a Spotify client, handling local and GCP environments."""

        credentials = self.get_spotify_credentials(local_credentials, scopes)
        client_id = credentials["client_id"]
        client_secret = credentials["client_secret"]
        redirect_uri = credentials["redirect_uri"]

        try:
            try:
                # no Oauth
                sp_oauth = SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                )
            except:
                # Oauth
                sp_oauth = SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scope=" ".join(scopes),
                )

            # Get the token information. This will handle the OAuth flow if needed.
            token_info = sp_oauth.get_cached_token()

            if not token_info:
                # If no cached token, prompt the user to authorize
                auth_url = sp_oauth.get_authorize_url()
                print(f"Please visit this URL to authorize: {auth_url}")
                response = input("Enter the URL you were redirected to: ")
                code = sp_oauth.parse_response_code(response)
                token_info = sp_oauth.get_access_token(code)

            if not token_info:
                raise Exception("Failed to get Spotify token.")

            # Create the Spotify client using the access token
            sp = Spotify(auth=token_info["access_token"])
            print("Spotify client created successfully.")
            return sp

        except SpotifyException as e:
            print(f"Spotify API error: {e}")
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            raise

    def get_gmail_creds(self, scopes):
        """Retrieves Gmail service using refresh token from Secret Manager or local file."""
        try:
            # Try to get credentials from Secret Manager (GCP)
            token = self.get_secret_value(secret_name="GMAIL_TOKEN")
            token_data = json.loads(token)
        except DefaultCredentialsError:
            print("Secret Manager credentials not found. Trying local token file.")
            try:
                with open("token.json", "r") as f:
                    token_data = json.load(f)
                    print("Using refresh token from token.json")
            except FileNotFoundError:
                print(
                    "token.json file not found. Please run authentication locally first."
                )
                raise
            except json.JSONDecodeError:
                print("Invalid JSON in token.json")
                raise
        except Exception as e:
            print(f"Error getting refresh token from Secret Manager: {e}")
            raise

        creds = Credentials(
            token=None,
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data["client_id"],
            client_secret=token_data["client_secret"],
            scopes=scopes,
        )
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Error refreshing token: {e}")
            raise

        return creds

    def get_secret_value(self, secret_name):
        credentials, project_id = default()
        client = secrets.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        return secret_value


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

    def __init__(self, local_credentials: dict):
        """
        Initializes the Spotify client.
        """
        self.sp = CredentialsManager().get_spotify_client(
            self.SCOPES, local_credentials
        )

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

        query = f"{artist_name} {album_name} -deluxe"
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
        scopes = [
            # "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify",
            # "https://www.googleapis.com/auth/gmail.compose",
            # "https://www.googleapis.com/auth/gmail.readonly",
        ]
        credentials = CredentialsManager().get_gmail_creds(scopes=scopes)
        self.sp = build("gmail", "v1", credentials=credentials)

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

    def create_message_html(self, sender, recipients, subject, body):
        msg = MIMEText(body, "html")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        # Convert the string to bytes before encoding
        raw_message = base64.urlsafe_b64encode(msg.as_string().encode("utf-8")).decode(
            "utf-8"
        )
        return raw_message

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
            message = self.create_message_html(
                self.sender_email, recipients, subject, body
            )
            self.sp.users().messages().send(
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
        credentials = CredentialsManager.get_gcp_credentials(scopes=FormAPI.SCOPES)
        self.sp = build("forms", "v1", credentials=credentials)

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
            response = self.sp.forms().responses().list(formId=form_id).execute()
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


class GoogleCloudStorage:
    BUCKET_NAME = "batty-bot-aotw"
    SECRET = "storage_credentials"
    """
    A class for interacting with Google Cloud Storage.

    Uses service account credentials for authentication.
    """

    def __init__(self):
        """
        Initializes the Google Cloud Storage client using credentials from Secret Manager.
        """

        credentials = CredentialsManager.get_gcp_credentials()
        self.client = storage.Client(credentials=credentials)  # Cloud Storage client

    def upload_file(self, source_file_path, destination_blob_name):
        """
        Uploads a file to a Google Cloud Storage bucket.

        Args:
            source_file_path: The path to the local file to upload.
            destination_blob_name: The desired name for the uploaded file in the bucket.

        Raises:
            Exception: If uploading the file fails.
        """

        bucket = self.client.bucket(GoogleCloudStorage.BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)

        try:
            blob.upload_from_filename(source_file_path)
            print(f"File '{source_file_path}' uploaded to '{destination_blob_name}'")
        except Exception as e:
            print(f"Failed to upload file: {e}")
            raise

    def download_file(self, source_blob_name, destination_file_path):
        """
        Downloads a file from a Google Cloud Storage bucket.

        Args:
            source_blob_name: The name of the file to download from the bucket.
            destination_file_path: The local path where the downloaded file should be saved.

        Raises:
            Exception: If downloading the file fails.
        """

        bucket = self.client.bucket(GoogleCloudStorage.BUCKET_NAME)
        blob = bucket.blob(source_blob_name)

        try:
            blob.download_to_filename(destination_file_path)
            print(f"File '{source_blob_name}' downloaded to '{destination_file_path}'")
        except Exception as e:
            print(f"Failed to download file: {e}")
            raise

    def get_bucket(self):
        """
        Retrieves a specific bucket object.

        Args:
            GoogleCloudStorage.BUCKET_NAME: The name of the bucket to retrieve.

        Returns:
            A bucket object or None if the bucket doesn't exist.
        """

        return self.client.bucket(GoogleCloudStorage.BUCKET_NAME)

    def read_json(self, blob_name):
        """Reads JSON data from a GCS blob and returns it as a Python object.

        Args:
            GoogleCloudStorage.BUCKET_NAME: The name of the bucket.
            blob_name: The name of the blob.

        Returns:
            The parsed JSON data as a Python object.
        """

        bucket = self.client.bucket(GoogleCloudStorage.BUCKET_NAME)
        blob = bucket.blob(blob_name)
        if blob.exists():
            blob_bytes = blob.download_as_bytes()
            return json.loads(blob_bytes)
        else:
            print(f"File {blob_name} does not exist, returning None")
            return None

    def write_to_json(self, data, blob_name):
        bucket = self.client.bucket(GoogleCloudStorage.BUCKET_NAME)
        blob = bucket.blob(blob_name)
        json_data = json.dumps(data, indent=4)
        blob.upload_from_string(json_data, content_type="application/json")

    def read_txt(self, blob_name):
        """Reads the content of a GCS blob (text file) and returns it as a string.

        Args:
            blob_name: The name of the text file blob.

        Returns:
            The content of the text file as a string.
        """

        bucket = self.client.bucket(GoogleCloudStorage.BUCKET_NAME)
        blob = bucket.blob(blob_name)
        if blob.exists():
            return blob.download_as_text()
        else:
            print(f"File {blob_name} does not exist, returning None")
            return None


class OpenAIAPI:
    client = None
    default_model = "gpt-4o-mini"
    default_context = "You are a helpful assistant."

    def __init__(self, api_key):
        if not OpenAIAPI.client:
            OpenAIAPI.client = OpenAI(api_key=api_key)

    def send_prompt(self, prompt):
        """
        Sends a prompt to the OpenAI API and returns the generated text.

        Args:
            prompt: The prompt to send to the model.
            model: The OpenAI model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: Controls the randomness of the generated text.

        Returns:
            The generated text.
        """

        message = [
            {"role": "system", "content": OpenAIAPI.default_context},
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=OpenAIAPI.default_model, messages=message
        )

        return response.choices[0].message.content.strip()
