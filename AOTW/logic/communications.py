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
from google.cloud import storage
from openai import OpenAI
from email.mime.text import MIMEText
from google.cloud import secretmanager_v1 as secrets


class Authentication:
    """
    A class for handling OAuth 2.0 authentication for Google and Spotify APIs.

    Takes an API name and scopes as arguments.
    """


    api_to_secret_key = {
        "spotify":"spotify_credentials",
        "forms": "forms_credentials",
        "gmail": "credentials"
    }

    def __init__(self, api_name, scopes, token_filename):
        self.api_name = api_name
        self.scopes = scopes
        self.token_filename = token_filename
        self.service = None

    def _get_access_credentials(self):
        """
        Retrieves credentials from Secret Manager or the token file.

        Returns:
            A dictionary containing the cached credentials or None if not found.
        """

        try:
            # Get credentials from Secret Manager with the secret name and version
            secret_client = secrets.SecretManagerServiceClient()
            secret_key = self.api_to_secret_key[self.api_name]
            secret_name = f"projects/{os.getenv('PROJECT_ID')}/secrets/{secret_key}-credentials/versions/latest"            
            response = secret_client.access_secret_version(name=secret_name)
            access_creds = json.loads(response.payload.data.decode("UTF-8"))
            return access_creds
        except Exception as e:
            print(f"Error retrieving credentials from Secret Manager: {e}")
            pass

        # If Secret Manager fails, attempt to read from the fallback token file (optional)
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
                print(f"Authenticating to {self.api_name} with prior token")
            except:
                creds = None

        if not creds or not creds.valid:
            print("Obtaining refresh token for authentication")
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

        access_creds = self._get_access_credentials()
        if not access_creds:
            # Must go through Oauth
            with open("spotify_credentials.json", "r") as f:
                credentials = json.load(f)
            print("Authenticating Spotify with Oauth")
            auth_manager = SpotifyOAuth(
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                redirect_uri=credentials["redirect_uri"],
                scope=" ".join(self.scopes),  # Combine scopes into a single string
            )
            self.service = Spotify(auth_manager=auth_manager)

            # write token info
            with open(self.token_filename, "w") as token_file:
                json.dump(self.service.auth_manager.get_cached_token(), token_file)
        else:
            with open(self.token_filename, "r") as token_file:
                access_creds = json.load(token_file)
                # Check token expiration
                expires_at = datetime.datetime.fromtimestamp(access_creds["expires_at"])
                if expires_at < datetime.datetime.now():
                    print("Authenticating spotify with refresh token")
                    with open("spotify_credentials.json", "r") as f:
                        credentials = json.load(f)
                    auth_manager = SpotifyOAuth(
                        client_id=credentials["client_id"],
                        client_secret=credentials["client_secret"],
                        redirect_uri=credentials["redirect_uri"],
                    )
                    self.service = Spotify(auth_manager=auth_manager)
                    self.service.auth_manager.refresh_access_token(
                        access_creds["refresh_token"]
                    )
                    access_creds = self.service.auth_manager.get_cached_token()
                    with open(self.token_filename, "w") as token_file:
                        json.dump(access_creds, token_file)
                else:
                    # Use existing credentials
                    print("Authenticating spotify with saved token")
                    self.service = Spotify(auth=access_creds["access_token"])
                return access_creds

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
        self.auth = Authentication(
            "gmail",
            ["https://www.googleapis.com/auth/gmail.modify"],
            "gmail_token.json"
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
            service = self.auth.get_service()
            message = self.create_message_html(
                self.sender_email, recipients, subject, body
            )
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

        project_id = os.environ.get("PROJECT_ID")
        if not project_id:
            raise ValueError("PROJECT_ID environment variable not set.")

        try:
            secret_client = secrets.SecretManagerServiceClient()
            secret_name = f"projects/{project_id}/secrets/{self.SECRET}/versions/latest"
            response = secret_client.access_secret_version(name=secret_name)
            credentials_json = json.loads(response.payload.data.decode("UTF-8"))
            self.client = storage.Client.from_service_account_info(credentials_json)
            print("Google Cloud Storage client initialized using Secret Manager.")

        except:
            self.client = storage.Client.from_service_account_json(
                "storage_credentials.json", project=project_id
            )
            print("Google Cloud Storage client initialized using local credentials.")



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
