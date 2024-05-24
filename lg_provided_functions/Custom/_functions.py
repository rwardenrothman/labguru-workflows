import requests


def notify_user(title: str, message: str, *user_ids: int):
    url = 'https://us-flowguru.labguru.com/flows/6477/flow_runs/external_trigger.json?token=e62e86c39cef5a5fd24c0'
    for uid in user_ids:
        data = dict(
            title=title,
            content=message,
            user_id=uid
        )

        requests.get(url, params=data)
