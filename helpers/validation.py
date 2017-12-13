"""Validation decorator

This module contains a decorator that will validate input to functions/methods.
"""

from functools import wraps
from typing import Dict

from cerberus import Validator, ValidationError

def validate(schema: Dict):
    """ Validation decorator. 
    :param schema: a Cerberus-compatible schema dictionary
    """
    validator = Validator(schema=schema, allow_unknown=True)
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args):
            document = dict(enumerate(args))
            if not validator(document):
                raise ValidationError(validator.errors)
            if isinstance(func, staticmethod):
                return func.__func__(*args)
            else:
                return func(*args)
        return _wrapper
    return _decorator
