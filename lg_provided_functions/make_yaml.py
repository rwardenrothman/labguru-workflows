import click
from pathlib import Path
import json
import re
from datetime import datetime


@click.command()
@click.argument('fpath')
def make_yaml(fpath: str):
    template_path = Path(fpath)
    template_str = template_path.read_text()
    template_folder = template_path.parent
    output_folder = template_folder / template_path.stem
    output_folder.mkdir(exist_ok=True)
    output_regex = re.compile(r'store_variable\([\'\"](\w+)[\'\"]')

    for py_file in template_folder.glob('*.py'):
        file_variable = '"{{' + py_file.name + '}}"'
        if file_variable in template_str:
            file_text = py_file.read_text()
            escaped_file = json.dumps(file_text)
            template_str = template_str.replace(file_variable, escaped_file)

            outputs_variable = file_variable.replace('.py', '.outputs')
            stored_variables = output_regex.findall(file_text)
            template_str = template_str.replace(outputs_variable, ', '.join(stored_variables))

    outfile = output_folder / (template_path.stem + datetime.now().strftime('_%Y%m%d_%H%M%S.yaml'))
    outfile.write_text(template_str)

    print(f'Output YAML written to: {outfile}')
    print(f'It should be uploaded to: https://us-flowguru.labguru.com/flows/6477/edit')


if __name__ == '__main__':
    make_yaml()
