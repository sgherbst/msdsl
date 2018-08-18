import json
from interval import interval

from marshmallow import Schema, fields, post_load, pprint

from msdsl.model import AnalogSignal, DigitalSignal, CaseLinearExpr, MixedSignalModel


def dump_model(model):
    schema = MixedSignalModelSchema()
    pprint(schema.dump(model).data)


class IntervalField(fields.Field):
    def _serialize(self, value, attr, obj):
        return [value[0].inf, value[0].sup]

    def _deserialize(self, value, attr, data):
        range_ = json.loads(value)
        return interval[range_[0], range_[1]]


class CaseLinearExprSchema(Schema):
    num_cases = fields.Integer()
    coeffs = fields.Dict()
    const = fields.Number()

    @post_load
    def make_object(self, data):
        return CaseLinearExpr(**data)


class AnalogSignalSchema(Schema):
    name = fields.Str()
    range_ = IntervalField()
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
    mode = fields.Str(many=True)
    analog_inputs = fields.Nested(AnalogSignalSchema, many=True)
    digital_inputs = fields.Nested(DigitalSignalSchema, many=True)
    analog_outputs = fields.Nested(AnalogSignalSchema, many=True)
    analog_states = fields.Nested(AnalogSignalSchema, many=True)
    digital_states = fields.Nested(DigitalSignalSchema, many=True)

    @post_load
    def make_object(self, data):
        return MixedSignalModel(**data)