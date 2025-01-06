from AOTW.logic.config import Env
from AOTW.logic.communications import OpenAIAPI, GoogleCloudStorage
import re
import html


class EmailManager:
    def __init__(self, config, emailer):
        self.config = config
        self.emailer = emailer
        self.send_email_func = emailer.send_email

    def read_fun_fact_prompt_template(self):
        blob_name = f"reference/fun_fact_prompt.txt"
        gcs_client = GoogleCloudStorage()
        fun_fact_prompt = gcs_client.read_txt(blob_name)
        return fun_fact_prompt

    def get_fun_facts(self, album, artist):
        prompt = self.read_fun_fact_prompt_template()
        prompt = prompt.replace("$album", album).replace("$artist", artist)
        open_ai = OpenAIAPI(self.config.openai_api_key)
        fun_facts = open_ai.send_prompt(prompt)

        # conver to right html format
        fun_facts = html.escape(fun_facts)
        fun_facts = fun_facts.replace("\n", "<br>")
        fun_facts = re.sub(r"\\'", "'", fun_facts)
        fun_facts = re.sub(
            r"\s{2,}", " ", fun_facts
        )  # Replaces two or more spaces with a single space
        fun_facts = fun_facts.strip()
        # add spaces between fun facts and rest of introduction
        fun_facts = fun_facts.replace("1.", "<br><br>1.")
        fun_facts = re.sub(r"(<br>\s*){3,}", "<br><br>", fun_facts)

        return fun_facts

    def send_aotw_email(self, chooser_name):
        subject = "New AOTW!"

        body = f"""Time for a new AOTW! It is {chooser_name}'s turn to choose an album.<br><br>Please submit your AOTW here: {self.config.aotw_form_link}<br><br>Here's the playlist: {self.config.playlist_link}"""

        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def send_reminder_email(self, days_left: int):
        subject = f"AOTW Reminder - {days_left} Days Left to Listen"
        body = (
            f"Remember to listen to the AOTW! You have {days_left} days left to listen."
        )
        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def send_aotw_chosen_email(self, album: str, artist: str):
        subject = (
            f"Get ready to listen to {album.capitalize()} by {artist.capitalize()}!"
        )
        fun_facts = self.get_fun_facts(album, artist)
        body = f"A new AOTW has been chosen: {album.capitalize()} by {artist.capitalize()}.<br><br>Listen to it here: {self.config.playlist_link}!<br><br>{fun_facts}"
        self.send_email_func(self.config.get_participant_emails(), subject, body)

    def _print_email_to_terminal(recipients, subject, body):
        print(f"**MOCK EMAIL**")
        print(f"Recipients:{recipients}")
        print(f"Subject:{subject}")
        print(f"<br>{body}")
