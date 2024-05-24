import click
from pathlib import Path
import json
import re
from datetime import datetime
import inspect
import lg_provided_functions.Custom._functions as cfx


@click.command()
@click.argument('fpath')
def make_yaml(fpath: str):
    template_path = Path(fpath)
    template_str = template_path.read_text()
    template_folder = template_path.parent
    output_folder = template_folder / template_path.stem
    output_folder.mkdir(exist_ok=True)

    #define the regular expressions
    output_regex = re.compile(r'store_variable\([\'\"](\w+)[\'\"]')
    lg_functions_regex = re.compile(r'(from lg_provided_functions import (.*))\n')
    custom_functions_regex = re.compile(r'(from lg_provided_functions.Custom import (.*)\n)')

    for py_file in template_folder.glob('*.py'):
        file_variable = '"{{' + py_file.name + '}}"'
        if file_variable in template_str:
            file_text = py_file.read_text()
            # remove the utility functions
            if m := lg_functions_regex.search(file_text):
                file_text = file_text.replace(m.group(1), 'DEBUG = False')

            # replace any custom functions
            if m := custom_functions_regex.search(file_text):
                fxn_strs = ['']

                cur_fxn_name: str
                for cur_fxn_name in m.group(2).split(','):
                    cur_fxn_name = cur_fxn_name.strip()
                    fxn_name = getattr(cfx, cur_fxn_name)
                    fxn_def = inspect.getsource(fxn_name)
                    fxn_strs.append(fxn_def)

                custom_fxn_text = '\n\n'.join(fxn_strs)
                file_text = file_text.replace(m.group(1), custom_fxn_text)

            escaped_file = json.dumps(file_text)
            template_str = template_str.replace(file_variable, escaped_file)

            outputs_variable = file_variable.replace('.py', '.outputs')
            stored_variables = output_regex.findall(file_text)
            template_str = template_str.replace(outputs_variable, ', '.join(stored_variables))

    outfile = output_folder / (template_path.stem + datetime.now().strftime('_%Y%m%d_%H%M%S.yaml'))
    outfile.write_text(template_str)

    print(f'Output YAML written to: {outfile}')

    if m := re.search(r'name: id\n\s+value_before_type_cast: (\d+)', template_str):
        print(f'It should be uploaded to: https://us-flowguru.labguru.com/flows/{m.group(1)}/edit')


if __name__ == '__main__':
    make_yaml()
