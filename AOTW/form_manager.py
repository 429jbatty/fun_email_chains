import datetime
from communications import FormAPI
from album import Album
import os
import json


class FormManager:
    def __init__(self, config, form_handler: FormAPI):
        self.config = config
        self.form_handler = form_handler

    def _log_submissions(self, submissions):
        filename = f"AOTW/data/submissions.json"
        if os.path.exists(filename):
            print(f"{filename} already exists\nData will be overwritten")

        with open(filename, "w") as f:
            json.dump(
                submissions,
                f,
                indent=4,
            )

    def retrieve_and_log_submissions(self):
        submissions = self.form_handler.get_form_submissions(
            form_id=self.config.aotw_form_id
        )
        if not submissions:
            print(f"No submissions found")
            return None
        else:
            self._log_submissions(submissions)
        return submissions
