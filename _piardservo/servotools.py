from collections.abc import Iterable

def linear_transform(x, range_0, range_1, flip=0):

    min0, max0 = range_0

    if flip == 0:
        min1, max1 = range_1
    else:
        max1, min1 = range_1

    return (x - min0)/(max0-min0)*(max1-min1) + min1

#todo turn the asserts into raises
def servo_param_setter(n,
                       param_values,
                       old_values=None
                       ):

    if not isinstance(param_values, (float, int, list, tuple, bool, type(None))):
        raise ValueError("param_values but be float, int, list, tuple, bool, or None")
    # if max_max is a number
    if not isinstance(param_values, Iterable):
        return [param_values] * n

    elif isinstance(param_values, Iterable) and len(param_values)==n:
        for p_value in param_values:
            assert isinstance(p_value, (float, int))
        return param_values

    elif isinstance(param_values, Iterable) and not isinstance(param_values[0], Iterable):
        out = [param_values[0]] * n
        for p_value in param_values[1:]:
            assert len(p_value) == 2 and isinstance(p_value[1], (float, int))
            out[p_value[0]] = p_value[1]
        return out

    elif isinstance(param_values, Iterable) and old_values is not None:
        for p_value in param_values:
            old_values[p_value[0]] = old_values[p_value[1]]
        return old_values

    else:
        raise Exception('Inputs not of the proper form')
