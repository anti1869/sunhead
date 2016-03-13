"""
Types to use in messaging stuff.
"""


from typing import TypeVar, Dict, List


Transferrable = TypeVar("Transferrable", Dict, List, str)
Serialized = TypeVar("Serialized", str, bytes)
