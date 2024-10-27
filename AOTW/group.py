class Participant:
    def __init__(self, name, email):
        self.name = name
        self.email = email

class Group:
    def __init__(self, participant_emails):
        self.participants = [Participant(email.split("@")[0], email) for email in participant_emails]
