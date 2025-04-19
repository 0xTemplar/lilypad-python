import os
import json

from typing import Callable

class ModuleDecorators:
    """Decorators for common module patterns"""
    
    @staticmethod
    def text_input(fn):
        """Decorator for text input handlers"""
        def wrapper(*args, **kwargs):
            input_text = os.getenv('MODEL_INPUT')
            return fn(input_text, *args, **kwargs)
        return wrapper
    
    @staticmethod
    def json_output(fn):
        """Decorator for JSON output formatting"""
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            output_path = '/outputs/results.json'
            with open(output_path, 'w') as f:
                json.dump(result, f)
            return output_path
        return wrapper