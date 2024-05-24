import os
from pathlib import Path
import json


def base():
    return os.environ['LG_BASE']


def token():
    return os.environ['LG_TOKEN']


def _get_json_path(var_name: str) -> Path:
    var_path = Path(os.environ['VAR_PATH'])
    var_path.mkdir(parents=True, exist_ok=True)
    json_path = var_path / f'{var_name}.json'
    return json_path


def variable(var_name: str):
    return json.loads(_get_json_path(var_name).read_text())


def store_variable(out_name: str, out_value):
    _get_json_path(out_name).write_text(json.dumps(out_value))
