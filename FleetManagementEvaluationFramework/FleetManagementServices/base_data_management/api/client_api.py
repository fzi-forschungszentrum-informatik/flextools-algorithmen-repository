import os
import requests


def reset_database_api_call():
    return requests.post(os.environ['BASEDATAMANAGEMENT_URL'] + "reset", data={})

