import json
import collections
from marshmallow import Schema, fields, post_load

from msdsl.model import AnalogSignal, DigitalSignal, MixedSignalModel, ModelAssignment
from msdsl.expr import ModelExpr

def load_model(data):
    schema = MixedSignalModelSchema()
    return schema.load(json.loads(data)).data

def dump_model(model, pretty=True):
    schema = MixedSignalModelSchema()

    kwargs = {}
    if pretty:
        kwargs['sort_keys'] = True
        kwargs['indent'] = 2

    data = schema.dump(model).data
    print(json.dumps(data, **kwargs))


class ModelExprField(fields.Field):
    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        elif isinstance(value, str):
            return value
        else:
            operands = [self._serialize(operand, None, None) for operand in value.operands]
            return {'operator': value.operator, 'operands': operands}

    def _deserialize(self, value, attr, data):
        if value is None:
            return None
        elif isinstance(value, str):
            return value
        else:
            operands = [self._deserialize(operand, None, None) for operand in value['operands']]
            return ModelExpr(operator=value['operator'], operands=operands)


class AnalogSignalSchema(Schema):
    name = fields.Str()
    range_ = fields.List(fields.Float(), allow_none=True)
    rel_tol = fields.Float(allow_none=True)
    abs_tol = fields.Float(allow_none=True)
    value = fields.Float(allow_none=True)
    array = fields.List(fields.Float(), allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)

    @post_load
    def make_object(self, data):
        return AnalogSignal(**data)


class DigitalSignalSchema(Schema):
    name = fields.Str()
    signed = fields.Boolean()
    width = fields.Integer()
    value = fields.Integer(allow_none=True)
    array = fields.List(fields.Integer(), allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)

    @post_load
    def make_object(self, data):
        return DigitalSignal(**data)


class ModelAssignmentSchema(Schema):
    lhs = fields.Str()
    rhs = ModelExprField()

    @post_load
    def make_object(self, data):
        return ModelAssignment(**data)


class MixedSignalModelSchema(Schema):
    analog_signals = fields.Nested(AnalogSignalSchema, many=True)
    digital_signals = fields.Nested(DigitalSignalSchema, many=True)
    assignment_groups = fields.List(fields.Nested(ModelAssignmentSchema, many=True))

    @post_load
    def make_object(self, data):
        return MixedSignalModel(**data)