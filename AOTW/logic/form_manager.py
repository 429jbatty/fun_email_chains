import os
import json

from AOTW.logic.communications import FormAPI, GoogleCloudStorage


class FormManager:
    def __init__(self, config, form_handler: FormAPI):
        self.config = config
        self.form_handler = form_handler

    def _log_submissions(self, submissions):
        gcs_client = GoogleCloudStorage()
        gcs_client.write_to_json(submissions, "form_submissions/submissions.json")

    def retrieve_and_log_submissions(self):
        submissions = self.form_handler.get_form_submissions(
            form_id=self.config.aotw_form_id
        )
        if not submissions:
            print(f"No form submissions found")
            return None
        else:
            print("Logging google form submissions...")
            self._log_submissions(submissions)
            print(f"{len(submissions)} total submissions logged")
        return submissions
