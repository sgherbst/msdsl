import pytest
from msdsl import MixedSignalModel, VerilogGenerator


@pytest.mark.parametrize(
    'in_type,in_opt,out_type,out_opt,check_format,cycle,expected_result,init_val', [
        # this cycle: normal
        ('uint', 8, 'uint', 8, True, 'this', None, 0),
        ('sint', 8, 'sint', 8, True, 'this', None, 0),
        ('real', 10.0, 'real', 10.0, True, 'this', None, 0),

        # next cycle: normal
        ('uint', 8, 'uint', 8, True, 'next', None, 0),
        ('sint', 8, 'sint', 8, True, 'next', None, 0),
        ('real', 10.0, 'real', 10.0, True, 'next', None, 0),

        # this cycle: exception
        ('sint', 8, 'uint', 8, True, 'this', 'formats do not match', 0),
        ('real', 8, 'uint', 8, True, 'this', 'formats do not match', 0),
        ('uint', 8, 'sint', 8, True, 'this', 'formats do not match', 0),
        ('real', 8, 'sint', 8, True, 'this', 'formats do not match', 0),
        ('uint', 8, 'real', 8, True, 'this', 'formats do not match', 0),
        ('sint', 8, 'real', 8, True, 'this', 'formats do not match', 0),

        # this cycle: block exception
        ('sint', 8, 'uint', 8, False, 'this', None, 0),
        ('uint', 8, 'sint', 8, False, 'this', None, 0),

        # next cycle: format exception
        ('sint', 8, 'uint', 8, True, 'next', 'formats do not match', 0),
        ('real', 8, 'uint', 8, True, 'next', 'formats do not match', 0),
        ('uint', 8, 'sint', 8, True, 'next', 'formats do not match', 0),
        ('real', 8, 'sint', 8, True, 'next', 'formats do not match', 0),
        ('uint', 8, 'real', 8, True, 'next', 'formats do not match', 0),
        ('sint', 8, 'real', 8, True, 'next', 'formats do not match', 0),

        # next cycle: block format exception
        ('sint', 8, 'uint', 8, False, 'next', None, 0),
        ('uint', 8, 'sint', 8, False, 'next', None, 0),

        # next cycle: width exception
        ('uint', 8, 'uint', 7, True, 'next', 'does not match the width', 0),
        ('sint', 8, 'sint', 7, True, 'next', 'does not match the width', 0),

        # next cycle: block width exception
        ('uint', 8, 'uint', 7, False, 'next', None, 0),
        ('sint', 8, 'sint', 7, False, 'next', None, 0),

        # next cycle: init value exception
        ('uint', 8, 'uint', 8, True, 'next', 'does not fit in the range', 256),
        ('sint', 8, 'sint', 8, True, 'next', 'does not fit in the range', 128),

        # next cycle: block init value exception
        ('uint', 8, 'uint', 8, False, 'next', None, 256),
        ('sint', 8, 'sint', 8, False, 'next', None, 128),
    ]
)
def test_check_format(in_type, in_opt, out_type, out_opt, check_format,
                      cycle, expected_result, init_val):
    # declare model I/O
    m = MixedSignalModel('model')

    if in_type == 'uint':
        m.add_digital_input('a', width=in_opt)
    elif in_type == 'sint':
        m.add_digital_input('a', width=in_opt, signed=True)
    elif in_type == 'real':
        m.add_analog_input('a')
    else:
        raise Exception(f'Invalid in_type: {in_type}')

    if out_type == 'uint':
        m.add_digital_state('y', width=out_opt, init=init_val)
    elif out_type == 'sint':
        m.add_digital_state('y', width=out_opt, signed=True, init=init_val)
    elif out_type == 'real':
        m.add_analog_state('y', range_=out_opt)
    else:
        raise Exception(f'Invalid out_type: {out_type}')

    if cycle == 'this':
        m.set_this_cycle(m.y, m.a, check_format=check_format)
    elif cycle == 'next':
        m.set_next_cycle(m.y, m.a, check_format=check_format)
    else:
        raise Exception(f'Invalid cycle type: {cycle}')

    # compile to a file
    if expected_result is not None:
        with pytest.raises(Exception) as e:
            m.compile(VerilogGenerator())
        assert expected_result in str(e.value)
    else:
        m.compile(VerilogGenerator())
