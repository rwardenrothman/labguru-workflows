from collections import defaultdict
from typing import List, DefaultDict, Dict, Any
import yaml

from LGWorkflows._ruby_yaml_tags import use_lg_emitter
from LGWorkflows._step_base import PipelineStep, PropertyDict
from LGWorkflows.triggers import TriggerStep


class WorkflowPipeline:
    def __init__(self, title: str, trigger: TriggerStep):
        self.trigger = trigger
        self.trigger.pipeline = self
        self.steps: DefaultDict[str, List[PipelineStep]] = defaultdict(list)
        self.title = title
        self._last_step = trigger
        self._variables: Dict[str, Any] = {}


        self._base = 'https://my.labguru.com'
        self._token = 'TOKEN'

    def add_step(self, new_step: PipelineStep, prior_step: PipelineStep = None):
        self.steps[(prior_step or self._last_step).uuid].append(new_step)
        self._last_step = new_step

    def add_chain(self, *steps: PipelineStep):
        for i, step in enumerate(steps):
            self.add_step(step, steps[i-1] if i else None)


    def _base(self) -> str:
        return self._base

    def _token(self) -> str:
        return self._token

    def _get_var(self, variable_name: str):
        return self._variables[variable_name]

    def _set_var(self, variable_name: str, variable_value: Any):
        self._variables[variable_name] = variable_value

    def _get_step_yaml_dicts(self, step: PipelineStep) -> PropertyDict:
        step_dict = step.to_yaml_dict()
        for cur_child in self.steps[step.uuid]:
            step_dict['children'].append(self._get_step_yaml_dicts(cur_child))
        return step_dict

    def make_yaml(self) -> str:
        yaml_tree = {
            'title': self.title,
            'mode': 'workflow',
            'content': [self._get_step_yaml_dicts(s) for s in self.steps[self.trigger.uuid]]
        }

        with use_lg_emitter():
            return yaml.dump_all([yaml_tree], default_flow_style=False, sort_keys=False, explicit_start=True)

if __name__ == '__main__':
    from LGWorkflows.steps import ScriptStep, WorkflowHelperFunction

    class AdderFxn(WorkflowHelperFunction):
        def __call__(self, a: int, b: int) -> int:
            return a + b


    class TestClass(ScriptStep):
        @staticmethod
        def code_block(base, token, variable, store_variable, helper_test=AdderFxn()):
            test_result = helper_test(1, 3)
            store_variable('res', test_result)


    tc = TestClass('Simple Addition')

    pipeline = WorkflowPipeline('test5', TriggerStep('test5'))
    pipeline.add_step(tc)
    pipeline.add_step(TestClass('Simple Addition 2'))

    pipeline_make_yaml = pipeline.make_yaml()
    with open(r'C:\Users\RobertWarden-Rothman\PycharmProjects\lg_workflows\dummy_flow.yaml', 'w') as f:
        f.write(pipeline_make_yaml)
