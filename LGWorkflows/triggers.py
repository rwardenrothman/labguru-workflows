from typing import Optional, TYPE_CHECKING

from LGWorkflows._step_base import PipelineStep, PropertyDict
from LGWorkflows._type_defs import BaseFxn, TokenFxn, GetVarFxn, StoreVarFxn

if TYPE_CHECKING:
    from LGWorkflows._pipeline import WorkflowPipeline


class TriggerStep(PipelineStep):
    def __init__(self, name: str, **properties: str):
        super().__init__(name, **properties)
        self.pipeline: Optional[WorkflowPipeline] = None

    def run(self, base: BaseFxn, token: TokenFxn, variable: GetVarFxn, store_variable: StoreVarFxn):
        pass

    @property
    def step_type_name(self) -> str:
        return 'Trigger'


class ManualTrigger(TriggerStep):
    def __init__(self):
        super().__init__('manual_trigger')
