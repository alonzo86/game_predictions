from typing import Optional


def safe_div(x, y):
    return 0 if y == 0 else x / y


def get_dictionary_item_by_property(source_dict: dict, by_property: str, expected_val) -> Optional:
    for k, v in source_dict.items():
        if getattr(v, by_property) == expected_val:
            return v
    return None
