import json
import os
from dataclasses import dataclass
from itertools import product, cycle, chain
from pprint import pprint
from typing import List

import pandas as pd
import requests

if os.environ.get('IS_LOCAL', False):
    from lg_provided_functions import base, token, variable, store_variable
    DEBUG = True
else:
    DEBUG = False


@dataclass
class StandardCurveInfo:
    protein_id: int
    protein_url: str
    max_conc: float
    diln_factor: float
    num_steps: int
    detection_id: int
    detection_url: str

    def __post_init__(self):
        self.protein_id = int(self.protein_id)
        self.max_conc = float(self.max_conc)
        self.diln_factor = float(self.diln_factor)
        self.num_steps = int(self.num_steps)
        self.detection_id = int(self.detection_id)

    @property
    def conc_values(self) -> List[float]:
        return [self.max_conc * ((1 / self.diln_factor)**i) for i in range(self.num_steps)]

    @property
    def conc_values_with_zero(self) -> List[float]:
        return self.conc_values + [0]


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


def get_well_dict():
    all_wells_by_col = [f'{row}{col+1:02d}' for col, row in product(range(24), 'ABCDEFGHIJKLMNOP')]
    c = cycle([1, 2]*8 + [3, 4]*8)
    quadrant_df = pd.DataFrame([dict(well=w, position=i+1, quadrant=q) for w, i, q in
                                zip(all_wells_by_col, range(384), c)])

    quadrant_df['row'] = quadrant_df['well'].str[0]
    quadrant_df['col'] = quadrant_df['well'].str[1:].astype(int)
    quadrant_df = quadrant_df.sort_values(['quadrant', 'position'])
    return quadrant_df.reset_index()['well'].to_dict()


submitted_info = variable('item')
replicates = int(submitted_info['replicates'])
element_data = requests.get(f"{base()}/api/v1/elements/{submitted_info['element_id']}?token={token()}").json()
store_variable('element', element_data)

# Read standard curve parameters
sc_items = {k: StandardCurveInfo(*v.split('|')) for k, v in submitted_info.items() if k.startswith('sc_')}
sc_count = sum(v.num_steps + 1 for v in sc_items.values())

# Get sample and dilution keys
sample_keys = [k for i in range(384) if (k := f'sample_{i}') in submitted_info]
diln_keys = [k for i in range(384) if (k := f'dil_{i}') in submitted_info]

# Determine what samples need to be made
element_form_data = json.loads(element_data['form_data_json'])
all_checkboxes = chain.from_iterable(chain(v['fields'] for v in element_form_data['tables'][0]['table_1']))
checked_boxes = [checkbox['name'] for checkbox in all_checkboxes if checkbox['checked']]

needed_wells = []
for cur_sample_key, cur_sc_key in product(sample_keys, sc_items.keys()):
    if f'{cur_sample_key}_{cur_sc_key}' in checked_boxes:
        for cur_diln_key in diln_keys:
            if f'{cur_sample_key}_{cur_diln_key}' in checked_boxes:
                needed_wells.append((cur_sample_key, cur_diln_key, cur_sc_key))

if len(needed_wells) + sc_count > 384/replicates:
    print('oh no!')
    exit()



