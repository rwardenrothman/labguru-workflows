from contextlib import contextmanager

from yaml import YAMLObject, SafeDumper, SequenceEndEvent, Dumper
from yaml.emitter import Emitter
from yaml.representer import SafeRepresenter
from yaml.resolver import Resolver
from yaml.serializer import Serializer


class ParameterMapping(YAMLObject):
    yaml_tag = '!ruby/hash:ActiveSupport::HashWithIndifferentAccess'
    def __init__(self, property_dict: dict):
        self.__dict__.update(property_dict)

class PropertyMapping(YAMLObject):
    yaml_tag = '!ruby/object:ActionController::Parameters'

    def __init__(self, property_dict: dict):
        super().__init__()
        self.parameters = ParameterMapping(property_dict)


def _lg_expect_block_sequence_item(self: Emitter, first=False):
    if not first and isinstance(self.event, SequenceEndEvent):
        self.indent = self.indents.pop()
        self.state = self.states.pop()
    else:
        self.write_indent()
        if hasattr(self, 'needs_indicator'):
            self.write_indicator('-', True, indention=True)
        else:
            setattr(self, 'needs_indicator', True)
        self.states.append(self.expect_block_sequence_item)
        self.expect_node(sequence=True)

@contextmanager
def use_lg_emitter():
    _default_fxn = Emitter.expect_block_sequence_item
    Dumper.expect_block_sequence_item = _lg_expect_block_sequence_item
    yield
    Dumper.expect_block_sequence_item = _default_fxn


if __name__ == '__main__':
    from io import StringIO
    import yaml

    fo = PropertyMapping({
        'action': 'continue',
        'a': "{{trigger_attachment.equipment_id}}",
        'condition': "=",
        'b': '4',
        'when_stopped_archive': 'true'
    })
    stream = StringIO()
    full_dict = dict(title='title', content={
        'step': 'SimpleCondition',
        'children': [],
        'properties': fo
    }, mode='workflow')
    print(yaml.dump_all([full_dict], stream))
    print(stream.getvalue())