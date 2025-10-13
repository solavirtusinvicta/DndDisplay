import os
import re
from enum import Enum
from pathlib import Path
from typing import List, Union

STATIC_DIR = Path(os.path.join(os.path.dirname(__file__), "static"))
BG_DIR = STATIC_DIR / "backgrounds"


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

def get_options() -> dict[str, List[Union[str]]]:
    return {"weatherOptions": [str(weather.name.lower()) for weather in Weather], "backgroundOptions": os.listdir(BG_DIR)}

class Weather(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    FOG = "fog"
