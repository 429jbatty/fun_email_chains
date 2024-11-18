from main import daily_email, search_for_new_aotw, update_playlist

env = "prod"
test_date = None


def run_daily_email():
    daily_email(env, test_date)


def run_search_for_new_aotw():
    search_for_new_aotw(env, test_date)


def run_update_playlist():
    update_playlist(env, test_date)
