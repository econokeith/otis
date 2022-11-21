def update_save_attributes_on_write(obj, local_dict):
    """
    updates keyword arguments for writing and saved if saved=True
    ===================== use it like =================================
    class AssetWriter:
        ...
        ...
        def write(self, frame, kw1=_kw1, kw2=_kw2, kw3=_kw3, saved=True):
            _kw1, _kw2, _kw3 = update...write(self, locals())
            ...
            ...
    """
    variable_keys = list(local_dict.keys())
    output = []
    save_it = local_dict['save']

    for key in variable_keys[2:-1]:
        value = local_dict[key]

        if value is not None:
            output.append(value)
            if save_it is True:
                obj.__setattribute__(key, value)
        else:
            output.append(obj.__getattribute__(key))

    return output
