import requests

from lg_provided_functions import *
from pprint import pprint
import json


def notification(title, content, recipients):
    url = f'{base()}/api/v1/web_notifications/notify'
    data = {
        "item": {
            "title": title,
            "content": content
        },
        "recipients": recipients,
        "token": token()
    }

    response = requests.post(url, json=data)

    # Check the response status code
    if response.status_code == 200:
        print("POST request successful!")
    else:
        print(f"POST request failed with status code {response.status_code}")
        print(response.text)  # Print the response content for debugging if needed


if __name__ == '__main__':
    creation_params = {
        "token": token(),
        "page_size": 10,
        "order": "id DESC",
        "filter": json.dumps({
            "action": ["update", "update (auto-save)"],
            "context_id": 665
        })
    }
    history_resp = requests.get(f"{base()}/api/v1/histories", params=creation_params)
    history_json = history_resp.json()[0]
    history_id = history_json['id']
    member_id = history_json['member_id']
    print(member_id)

    creation_notification = (f'A new form has been added to Experiment {history_json["context_id"]} '
                             f'({history_json["context_name"]}). Please refresh the page or '
                             f'<a href="{base()}{history_json["object"]["url"]}">click here</a>.')
    notification('New form created', creation_notification, [member_id])


