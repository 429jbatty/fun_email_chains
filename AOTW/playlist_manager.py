from spotify import SpotifyClient
from communications import GmailAPI
from album import Album

class PlaylistManager:
    def __init__(self, spotify_client:SpotifyClient):
        self.spotify_client = spotify_client

    def update_playlist(self, aotw:Album):
        print("Adding AOTW to Playlist")
        print(f"AOTW details: {aotw}")


