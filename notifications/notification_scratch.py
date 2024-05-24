import requests

from lg_provided_functions import store_variable

TRIGGER_URL = 'https://us-flowguru.labguru.com/flows/6477/flow_runs/external_trigger.json?token=e62e86c39cef5a5fd24c0'

data = dict(
    title="I'm a title!",
    content="I'm some content!",
    user_id=9
)

resp = requests.get(TRIGGER_URL, params=data)
print(resp)

# for k, v in data.items():
#     store_variable(k, v)