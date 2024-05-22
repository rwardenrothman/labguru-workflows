import json
import os
from collections import defaultdict
import requests

if os.environ.get('IS_LOCAL', False):
    from lg_provided_functions import base, token, variable, store_variable
    DEBUG = True
else:
    DEBUG = False


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


submitted_info = variable('item')
element_data = requests.get(f"{base()}/api/v1/elements/{submitted_info['element_id']}?token={token()}").json()
store_variable('element', element_data)

element_form_data = json.loads(element_data['form_data_json'])
# pprint(element_form_data)

# Get standard curve info
sc_info = {}
for i, cur_row in enumerate(element_form_data['tables'][0]['table_1']):
    cur_info_dict = {}
    sc_protein_id = cur_row['fields'][0]['value']
    # print(f"{sc_protein_id=}")
    if sc_protein_id:
        detection_ab_id = cur_row['fields'][4]['value']

        cur_info_dict['protein_id'] = sc_protein_id
        cur_info_dict['protein_api_url'] = f"{base()}/api/v1{cur_row['fields'][0]['url']}/{sc_protein_id}"
        cur_info_dict['max_concentration'] = float(cur_row['fields'][1]['value'])
        cur_info_dict['dilution_factor'] = float(cur_row['fields'][2]['value'])
        cur_info_dict['num_points'] = int(cur_row['fields'][3]['value'])
        cur_info_dict['detection_ab_id'] = detection_ab_id
        cur_info_dict['detection_api_url'] = f"{base()}/api/v1{cur_row['fields'][4]['url']}/{detection_ab_id}"
        sc_info[f"sc_{i+1}"] = cur_info_dict

store_variable('sc_info', sc_info)

# Get Dilution Options
dilution_options = {f"dil_{i+1}": float(d) for i in range(6) if (d := submitted_info[f"dil_opt_{i+1}"])}
store_variable('dilution_options', dilution_options)

# Get Sample info
section_id = element_data['container_id']
section_info = requests.get(f"{base()}/api/v1/sections/{section_id}?token={token()}").json()
expt_id = section_info['container_id']
store_variable('section', section_info)
sample_element_id = 0
for cur_element in section_info['elements']:
    if cur_element['element_type'] == 'samples':
        sample_element_id = cur_element['id']
        break
if not sample_element_id:
    raise ValueError(f'Sample element {sample_element_id} not found')

sample_element_info = requests.get(f"{base()}/api/v1/elements/{sample_element_id}?token={token()}").json()
sample_element_data = json.loads(sample_element_info['data'])

sample_info = defaultdict(dict)
for i, c_sample in enumerate(sample_element_data['samples']):
    s_key = f"sample_{i}"
    sample_info[s_key]['collection'] = c_sample['collection_name']
    sample_info[s_key]['name'] = c_sample['name']
    sample_info[s_key]['api_url'] = c_sample['data']['api_url']
store_variable('sample_info', sample_info)

# Generate Form
hidden_input_values = ([(k, json.dumps(v)) for k, v in dilution_options.items()] +
                       [(k, '|'.join(map(str, v.values()))) for k, v in sc_info.items()] +
                       [(k, v['api_url']) for k, v in sample_info.items()])

hidden_inputs = [f'<input type="hidden" name="{k}" value="{v}" />' for k, v in hidden_input_values]

diln_cells = [f'<td>{dil_val:0.1f}</td>' for dil_val in dilution_options.values()]
# sc_cells = [f'<td>{sc_prot["protein_id"]}/{sc_prot["detection_ab_id"]}</td>' for sc_prot in sc_info.values()]
sc_cells = []
for sc_prot in sc_info.values():
    prot_info = requests.get(sc_prot['protein_api_url'], params=dict(token=token())).json()
    detection_info = requests.get(sc_prot['detection_api_url'], params=dict(token=token())).json()
    sc_cells.append(f'<td>Protein: {prot_info["name"]}<br>'
                    f'Detection: {detection_info["name"]}</td>')

header_rows = [f'<tr><td rowspan="2">Sample</td>'
               f'<td colspan="{len(diln_cells)}">Dilutions</td>'
               f'<td colspan="{len(sc_cells)}">Std. Curves</td></tr>',
               f"<tr>{''.join(diln_cells + sc_cells)}</tr>"]

table_rows = []
for s_key, s_info in sample_info.items():
    row_cells = [f'<td>{s_info["name"]}</td>']
    for dil_key, dil_val in dilution_options.items():
        row_cells.append(f'<td><input type="checkbox" class="no_reason form_element_input" '
                         f'name="{s_key}_{dil_key}" value="{s_key}_{dil_key}" /></td>')
    for sc_key in sc_info.keys():
        row_cells.append(f'<td><input type="checkbox" class="no_reason form_element_input" '
                         f'name="{s_key}_{sc_key}" value="{s_key}_{sc_key}" /></td>')
    table_rows.append(f"<tr>{''.join(row_cells)}</tr>")

table_html = (f"<table><thead>"
              f"{''.join(header_rows)}"
              f"</thead><tbody>"
              f"{''.join(table_rows)}"
              f"</tbody></table>")

button_html = ('<p><em>Save the senction and then click</em> <button '
               'class="workflow-trigger lg-button secondary small no-shadow" '
               'data-workflow-id="undefined" '
               'data-workflow-token="undefined" '
               'data-workflow-url="https://us-flowguru.labguru.com/flows/6353/flow_runs/'
               'external_trigger.json?token=62e9b18f1283cfc15a2c2">'
               'Generate Plate'
               '<i class="fa fa-spinner fa-spin spinner" style="display:none;">&nbsp;</i>'
               '</button></p>')

form_html = (f'<form class="ng-pristine ng-valid">\n'
             f'{"".join(hidden_inputs)}\n'
             f'{table_html}\n'
             f'{button_html}\n'
             f'</form>')

# Add new element to the section
item_json = {
    "token": token(),
    "item": {
        "container_id": section_id,
        "container_type": "ExperimentProcedure",
        "element_type": "form",
        "data": form_html,
        "name": 'Dilution and Standard Curve Selection Form'
    }
}
new_ele_resp = requests.post(f"{base()}/api/v1/elements", json=item_json)
store_variable('new_ele_resp', new_ele_resp.json())

# Sort the sections
sorted_element_ids = [e['id'] for e in section_info['elements']] + [new_ele_resp.json()['id']]
sorted_element_ids = list(map(int, sorted_element_ids))
sort_resp = requests.post(f"{base()}/api/v1/elements/sort", json={
    "token": token(),
    "container_id": expt_id,
    "container_type": section_info['container_type'],
    "list": sorted_element_ids
})

# Send refresh notification
creation_params = {
    "token": token(),
    "page_size": 10,
    "order": "id DESC",
    "filter": json.dumps({
        "action": ["update", "update (auto-save)"],
        "context_id": expt_id
    })
}
history_resp = requests.get(f"{base()}/api/v1/histories", params=creation_params)
history_json = history_resp.json()[0]
history_id = history_json['id']
member_id = history_json['member_id']
print(member_id)

creation_notification = (f'A new form has been added to Experiment {history_json["context_id"]} '
                         f'({history_json["context_name"]}). Please refresh the page or '
                         f'<a href="{base()}/knowledge/experiments/{expt_id}?section_id={section_id}">click here</a>.')
notification('New form created', creation_notification, [member_id])
