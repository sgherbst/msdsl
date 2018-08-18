import json
from interval import interval

from marshmallow import Schema, fields, post_load

from msdsl.model import AnalogSignal, DigitalSignal, CaseLinearExpr, MixedSignalModel

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


class IntervalField(fields.Field):
    def _serialize(self, value, attr, obj):
        return [value[0].inf, value[0].sup]

    def _deserialize(self, value, attr, data):
        return interval[value[0], value[1]]


class CaseLinearExprSchema(Schema):
    num_cases = fields.Integer()
    coeffs = fields.Dict()
    const = fields.Number()

    @post_load
    def make_object(self, data):
        return CaseLinearExpr(**data)


class AnalogSignalSchema(Schema):
    name = fields.Str()
    range_ = IntervalField(allow_none=True)
    rel_tol = fields.Number(allow_none=True)
    abs_tol = fields.Number(allow_none=True)
    expr = fields.Nested(CaseLinearExprSchema, allow_none=True)

    @post_load
    def make_object(self, data):
        return AnalogSignal(**data)


class DigitalSignalSchema(Schema):
    name = fields.Str()
    signed = fields.Boolean()
    width = fields.Integer()
    expr = fields.Nested(CaseLinearExprSchema, allow_none=True)

    @post_load
    def make_object(self, data):
        return DigitalSignal(**data)


class MixedSignalModelSchema(Schema):
    mode = fields.List(fields.String())
    analog_inputs = fields.Nested(AnalogSignalSchema, many=True)
    digital_inputs = fields.Nested(DigitalSignalSchema, many=True)
    analog_outputs = fields.Nested(AnalogSignalSchema, many=True)
    analog_states = fields.Nested(AnalogSignalSchema, many=True)
    digital_states = fields.Nested(DigitalSignalSchema, many=True)

    @post_load
    def make_object(self, data):
        return MixedSignalModel(**data)