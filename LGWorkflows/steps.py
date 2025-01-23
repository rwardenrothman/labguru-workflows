import inspect
import json
import re
from abc import abstractmethod
from typing import Dict, Any, Union, Literal

from LGWorkflows._ruby_yaml_tags import PropertyMapping
from LGWorkflows._step_base import PipelineStep, WorkflowHelperFunction, PropertyValue
from LGWorkflows._type_defs import BaseFxn, TokenFxn, GetVarFxn, StoreVarFxn


class FailedConditionError(AssertionError):
    pass


class ScriptStep(PipelineStep):
    _default_properties = {'code_template': 'none', 'lang': 'Python', 'scripter_version': 'v3'}

    @staticmethod
    @abstractmethod
    def code_block(base: BaseFxn, token: TokenFxn, variable: GetVarFxn, store_variable: StoreVarFxn,
                   **kwargs: WorkflowHelperFunction):
        pass

    def run(self, base: BaseFxn, token: TokenFxn, variable: GetVarFxn, store_variable: StoreVarFxn):
        self.code_block(base, token, variable, store_variable)

    def get_helper_functions(self) -> Dict[str, WorkflowHelperFunction]:
        return {n: p.default for n, p in inspect.signature(self.code_block).parameters.items()
                if isinstance(p.default, WorkflowHelperFunction)}

    @property
    def step_type_name(self) -> str:
        return 'ExternalScriptFunction'

    def format_code(self):
        source_lines = inspect.getsourcelines(self.code_block)[0]
        if '@staticmethod' in source_lines[0]:
            source_lines = source_lines[1:]
        if 'def code_block' in source_lines[0]:
            source_lines = source_lines[1:]

        indentation = 0
        for cur_char in source_lines[0]:
            if cur_char == ' ':
                indentation += 1
            else:
                break

        source_lines = ''.join([l[indentation:] for l in source_lines])

        out_blocks = [f.format_code(n) for n, f in self.get_helper_functions().items()] + [source_lines]

        return '\n'.join(out_blocks)

    def _compile_properties(self) -> PropertyMapping:
        properties = self.properties.copy()
        properties['explanation'] = self.name
        script_code = self.format_code()
        properties['code'] = script_code
        output_vars = re.findall(r'store_variable\([\'\"](\w+)[\'\"]', properties['code'])
        properties['custom_properties'] = ', '.join(output_vars)
        return PropertyMapping(properties)


def _evaluate_inputs(input_str: str, variable: GetVarFxn) -> Any:
    in_str = input_str.strip('{}')
    if in_str == 'null':
        in_str = 'None'
    try:
        return eval(in_str)
    except (NameError, SyntaxError):
        root, *path = in_str.split('.')
        try:
            obj = variable(root)
            p: str
            for p in path:
                if isinstance(obj, dict):
                    if p.isnumeric():
                        obj = obj.get(int(p), obj[p])
                    else:
                        obj = obj[p]
                elif isinstance(obj, list):
                    obj = obj[int(p)]
                else:
                    obj = getattr(obj, p)
            return obj
        except (KeyError, IndexError, AttributeError):
            raise ValueError(f'Invalid input string: {input_str}')


class BetweenConditionStep(PipelineStep):
    a: Any
    b: Any
    x: Any
    action: Literal['stop', 'continue']
    condition: Literal['a < x < b', 'a <= x < b', 'a < x <= b', 'a <= x <= b']
    when_stopped_archive: bool

    def __init__(self, name: str, a: str, x: str, b: str, action='stop', condition='a < x < b', when_stopped_archive=True):
        super().__init__(name, action=action, condition=condition, a=str(a), b=str(b), x=str(x),
                         when_stopped_archive=when_stopped_archive)

    @property
    def step_type_name(self) -> str:
        return 'SimpleConditionBetween'

    def run(self, base: BaseFxn, token: TokenFxn, variable: GetVarFxn, store_variable: StoreVarFxn):
        a = _evaluate_inputs(self.properties['a'], variable)
        b = _evaluate_inputs(self.properties['b'], variable)
        x = _evaluate_inputs(self.properties['x'], variable)
        condition = self.properties['condition']
        action = self.properties['action']

        if condition == 'a < x < b':
            result = a < x < b
        elif condition == 'a <= x < b':
            result = a <= x < b
        elif condition == 'a < x <= b':
            result = a < x <= b
        elif condition == 'a <= x <= b':
            result = a <= x <= b
        else:
            raise ValueError(f'Invalid condition: {condition}')

        if result and action == 'stop':
            raise FailedConditionError(f'Condition {condition} failed for {self.name}')

        if not result and action == 'continue':
            raise FailedConditionError(f'Condition {condition} failed for {self.name}')


if __name__ == '__main__':
    d = {'a': [dict(b=1, c=2), dict(b=2, c=str(3.2)), dict(b=3, c=4)]}
    evaluation = _evaluate_inputs('null', lambda x: d[x])
    print(type(evaluation), evaluation)