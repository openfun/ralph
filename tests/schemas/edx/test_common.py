"""Common function definitions for edx event tests"""

import operator


def check_error(excinfo, message, operator_type=operator.eq, error_key=None):
    """Compare error `excinfo` message with operator_type on `message`"""

    key = next(iter(excinfo.value.messages))
    if error_key:
        key = error_key
    if isinstance(excinfo.value.messages[key], dict):
        first_key = next(iter(excinfo.value.messages[key]))
        value = excinfo.value.messages[key][first_key][0]
    else:
        value = excinfo.value.messages[key][0]
    assert operator_type(value, message)
