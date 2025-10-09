import re
from typing import List


def remove_numbers(string: str) -> str:
    return re.sub(r'\d+', '', string)


def get_unique_name(name: str, name_list: List[str]) -> str:
    count_dict = {}

    for s in [remove_numbers(x) for x in name_list]:
        if s in count_dict:
            count_dict[s] += 1
        else:
            count_dict[s] = 0

    if name in count_dict:
        return name + str(count_dict[name] + 1)

    return name

