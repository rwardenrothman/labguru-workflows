import os
import requests

if os.environ.get('IS_LOCAL', False):
    from lg_provided_functions import base, token, variable, store_variable
    DEBUG = True
else:
    DEBUG = False

title = variable('title')
content = variable('content')
recipients = [variable('user_id')]

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