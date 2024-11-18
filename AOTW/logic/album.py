from AOTW.logic.communications import GoogleCloudStorage


class Album:
    def __init__(
        self,
        album: str,
        artist: str,
        spotify_link: str = None,
        playlist_updated: bool = None,
        week: int = None,
        **kwargs,
    ):
        self.album = album
        self.artist = artist
        self.spotify_link = spotify_link
        self.playlist_updated = playlist_updated
        self.week = week

        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def _update_playlist(self):
        self.playlist_updated = True

    def _set_week(self, week: int):
        self.week = week

    def log_data(self):
        """
        Writes the AOTW data to a JSON file in Google Cloud Storage.

        Args:
            gcs_client: An instance of the GoogleCloudStorage class.
        """

        blob_name = f"albums/aotw_{self.week}.json"
        data = {
            "week": self.week,
            "album": self.album,
            "artist": self.artist,
            "spotify_link": self.spotify_link,
            "playlist_updated": self.playlist_updated,
        }
        gcs_client = GoogleCloudStorage()
        gcs_client.write_to_json(data, blob_name)

    def __str__(self):
        return f"Album: {self.album}\nArtist: {self.artist}"
