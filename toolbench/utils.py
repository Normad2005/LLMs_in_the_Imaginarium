import re

def standardize(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_]', '_', name).lower()

def change_name(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z_]', '_', name)
