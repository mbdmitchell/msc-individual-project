import argparse
from enum import Enum

# The code generated can take different forms: (1) the execution path is dictated by a global directions array, (2) the
# directions are "baked-in" to the program. E.g. the dir array resulting in looping 3x vs recognising it loops 3x and
# having a for loop iterated that number of times.
class CodeType(Enum):
    GLOBAL_ARRAY = 'global'
    STATIC = 'static'

    def __str__(self):
        return self.name

    @classmethod
    def from_str(cls, type_str):
        """Convert a string to a CodeType enum member."""
        try:
            return cls[type_str.upper()]
        except KeyError:
            valid_languages = ', '.join(l.name.lower() for l in cls)
            raise argparse.ArgumentTypeError(
                f"Invalid language: {type_str}. Choose from: {valid_languages}."
            )