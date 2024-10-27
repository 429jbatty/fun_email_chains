import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-modify-public, playlist-modify-private, user-library-read",
            )
        )

    def search_album(self, query):
        results = self.sp.search(q=query, type="album")
        albums = results["albums"]["items"]
        return albums

    def create_playlist(self, user_id, playlist_name, public=False):
        playlist = self.sp.user_playlist_create(user_id, playlist_name, public=public)
        return playlist["id"]

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        self.sp.playlist_add_items(playlist_id, track_uris)

    def create_playlist_from_album(self, album_name, playlist_name, public=False):
        # Search for the album
        results = self.sp.search(q=album_name, type="album")
        albums = results["albums"]["items"]

        if len(albums) == 0:
            print(f"Album '{album_name}' not found.")
            return

        album_uri = albums[0]["uri"]

        # Create a new playlist
        playlist = self.sp.user_playlist_create(
            self.sp.current_user()["id"], playlist_name, public=public
        )
        playlist_id = playlist["id"]

        # Get the album's track URIs
        album_tracks = self.sp.album_tracks(album_uri)
        track_uris = [track["uri"] for track in album_tracks["items"]]

        # Add the tracks to the playlist
        self.sp.playlist_add_items(playlist_id, track_uris)
        print(f"Playlist '{playlist_name}' created successfully!")

    def update_aotw_playlist(self, album_name):
        # Search for the album
        results = self.sp.search(q=album_name, type="album")
        albums = results["albums"]["items"]

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
