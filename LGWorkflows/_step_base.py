from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Optional, Dict, TYPE_CHECKING, List, Union, Any
from uuid import uuid4
import inspect

from LGWorkflows._ruby_yaml_tags import PropertyMapping
from LGWorkflows._type_defs import BaseFxn, TokenFxn, GetVarFxn, StoreVarFxn

if TYPE_CHECKING:
    pass

PropertyValue = Union[str, int, float, bool, None, "PipelineStep", "PropertyList", "PropertyDict", PropertyMapping]
PropertyList = List[PropertyValue]
PropertyDict = Dict[str, PropertyValue]


class PipelineStep(ABC):
    _default_properties: Optional[Dict[str, str]] = None

    def __init__(self, name: str, **properties: PropertyValue):
        self.name: str = name
        self.uuid: str = str(uuid4())
        self.properties: PropertyDict = {**(self._default_properties or {}), **properties}

    @abstractmethod
    def run(self, base: BaseFxn, token: TokenFxn, variable: GetVarFxn, store_variable: StoreVarFxn):
        raise NotImplementedError(
            f"run not implemented for {self.__class__.__name__}")

    @property
    @abstractmethod
    def step_type_name(self) -> str:
        raise NotImplementedError(
            f"step_type_name not implemented for {self.__class__.__name__}")

    def _compile_properties(self) -> PropertyMapping:
        return PropertyMapping(self.properties)

    def to_yaml_dict(self) -> PropertyDict:
        return {
            "step": self.step_type_name,
            "children": [],
            "properties": self._compile_properties()
        }

class WorkflowHelperFunction(Callable):
    def __call__(self, *args, **kwargs):
        raise NotImplementedError(
            f"__call__ not implemented for {self.__class__.__name__}")

    def format_code(self, fxn_name: str):
        source_lines = inspect.getsourcelines(self.__call__)[0]
        indentation = len(source_lines[0].split('def')[0])
        source_lines = [l[indentation:] for l in source_lines]
        source_lines[0] = (source_lines[0]
                           .replace('def __call__(self, ', f'def {fxn_name}(')
                           .replace('def __call__(self,', f'def {fxn_name}('))
        return ''.join(source_lines)


