from abc import ABC, ABCMeta


class LanguageMeta(ABCMeta):
    """Metaclass to track subclasses"""
    _languages = []

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if bases != (ABC,):  # Don't register the base abstract class itself
            mcs._languages.append(cls)
        return cls

    @classmethod
    def get_languages(mcs):
        return mcs._languages
