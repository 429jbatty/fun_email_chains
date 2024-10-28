import json
from spotipy.oauth2 import SpotifyOAuth

import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

class SpotifyClient:
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

    def __init__(self, env):
        """
        Initializes the Spotify client.

        Args:
            env: An instance of the Env class that specifies the environment (test or prod).
        """

        self.env = env
        self.sp = None

        if not self.env.is_test():
            self._authenticate()

    def _authenticate(self):
        """
        Authenticates to the Spotify API using OAuth 2.0.

        Raises:
            Exception: If authentication fails.
        """

        try:
            # Check for existing credentials
            if os.path.exists('spotify_token.json'):
                with open('spotify_token.json', 'r') as token_file:
                    credentials = json.load(token_file)
                self.sp = Spotify(auth_manager=SpotifyOAuth(**credentials))
            else:
                try:
                    with open('spotify_credentials.json', 'r') as f:
                        credentials = json.load(f)
                    self.sp = Spotify(
                        auth_manager=SpotifyOAuth(**credentials)
                    )
                except FileNotFoundError:
                    print("spotify_credentials.json not found. Please create it with your credentials.")
                    exit(1)
                except Exception as e:
                    print(f"Failed to authenticate with Spotify: {e}")
                    raise
                # Save credentials for future use (optional)
                with open('spotify_token.json', 'w') as token_file:
                    json.dump(self.sp.auth_manager.get_cached_token(), token_file)

        except Exception as e:
            print(f"Failed to authenticate with Spotify: {e}")
            raise

    def search_album(self, query):
        """
        Searches for an album on Spotify.

        Args:
            query: The search query for the album.

        Returns:
            A list of album results.
        """

        if not self.sp:
            raise Exception("Spotify client not authenticated")

        results = self.sp.search(q=query, type="album")
        return results["albums"]["items"]

    # Implement other methods like create_playlist, etc. (similar structure)

    def update_aotw_playlist(self, album_name):
        """
        Updates the AOTW playlist with the given album.

        Args:
            album_name: The name of the album to add to the playlist.

        Raises:
            Exception: If Spotify client is not authenticated or album is not found.
        """

        if not self.sp:
            raise Exception("Spotify client not authenticated")

        # Search for the album
        albums = self.search_album(album_name)
        if len(albums) == 0:
            print(f"Album '{album_name}' not found.")
            return

        album_uri = albums[0]["uri"]

        # Get the user's ID
        user_id = self.sp.current_user()["id"]

        # Find the "AOTW" playlist
        playlists = self.sp.current_user_playlists()
        aotw_playlist_id = None
        for playlist in playlists["items"]:
            if playlist["name"] == "AOTW":
                aotw_playlist_id = playlist["id"]
                break

        # If the playlist doesn't exist, create it
        if aotw_playlist_id is None:
            playlist = self.sp.user_playlist_create(user_id, "AOTW", public=False)
            aotw_playlist_id = playlist["id"]

        # Clear the existing playlist
        self.sp.playlist_replace_items(aotw_playlist_id, [])

        # Get the album's track URIs
        album_tracks = self.sp.album_tracks(album_uri)
        track_uris = [track["uri"] for track in album_tracks["items"]]

        # Add the tracks to the playlist
        self.sp.playlist_add_items(aotw_playlist_id, track_uris)
        print("AOTW playlist updated successfully!")
