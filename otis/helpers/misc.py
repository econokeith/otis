def update_save_attributes_on_write(obj, local_dict, skip=2):
    """
    updates keyword arguments for writing and saved if saved=True
    will not work with functions that use **kwargs
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

    for key in variable_keys[skip:-1]:
        value = local_dict[key]

        if value is not None:
            output.append(value)
            if save_it is True:
                obj.__setattribute__(key, value)
        else:
            output.append(obj.__getattribute__(key))

    return output

def update_save_keywords(self, local_dict, attributes=()):
    """
    updates keyword arguments for writing and saved if saved=True
    will not work with functions that use **kwargs
    attributes = the list of string attribute names
    ===================== use it like =================================
    class AssetWriter:
        ...
        ...
        def write(self, frame, kw1=_kw1, kw2=_kw2, kw3=_kw3, saved=True):
            _kw1, _kw2, _kw3 = update...write(self, locals())
            ...
            ...
    """

    output = []
    # sometimes we don't care about saving or don't have save in the kwargs
    try:
        save_it = local_dict['save']
    except:
        save_it = False

    for key in attributes:
        # unsure the attribute is available from named keyword arguments
        try:
            value = local_dict[key]
        except:
            raise ValueError(f"keyword : '{key}' is not a named argument in this function")

        if value is not None:
            output.append(value)
            # if we're saving, we're saving
            if save_it is True:
                self.__setattribute__(key, value)
        else:
            output.append(self.__getattribute__(key))

    return output