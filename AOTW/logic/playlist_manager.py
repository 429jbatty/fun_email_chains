from AOTW.logic.communications import SpotifyAPI
from AOTW.logic.album import Album
from AOTW.logic.config import Config


class PlaylistManager:
    def __init__(self, config: Config, spotify_client: SpotifyAPI):
        self.config = config
        self.spotify_client = spotify_client

    def update_playlist(self, aotw: Album):
        album_uri = self.spotify_client.search_album(
            artist_name=aotw.artist, album_name=aotw.album
        )
        self.spotify_client.overwrite_playlist_with_album(
            playlist_id=self.config.playlist_id, album_uri=album_uri
        )
        print(f"Playlist updated to {aotw.album} by {aotw.artist}")
