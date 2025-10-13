from typing import Dict, Tuple, Optional, Union, List

from utility import get_unique_name, Weather


class Character:
    def __init__(self, name: str, hp: int, max_hp: int, img: str) -> None:
        self._name = name
        self._hp = hp
        self._max_hp = max_hp
        self._img = img
        self._initiative = 0
        self._abilities: Dict[str, str] = {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def initiative(self) -> int:
        return self._initiative

    @property
    def abilities(self) -> Tuple[str, ...]:
        return tuple(self._abilities)

    def add_ability(self, name: str) -> None:
        if name not in self._abilities:
            self._abilities[name] = "1"

    def remove_ability(self, name: str) -> None:
        if name in self._abilities:
            del self._abilities[name]

    def toggle_ability(self, name: str) -> None:
        if name in self._abilities:
            self._abilities[name] = "0" if self._abilities[name] == "1" else "1"

    def update_hp(self, name: Optional[str], hp: Optional[int]):
        if name is not None:
            self._name = name
        if hp is not None:
            self._hp = hp

    def update_initiative(self, initiative: int) -> None:
        self._initiative = initiative

    def entry(self) -> Dict[str, Union[str, int]]:
        return {
            "hp": self._hp,
            "maxHp": self._max_hp,
            "image": self._img,
            "initiative": self._initiative,
            "abilities": ",".join(self._abilities.keys()),
            "abilityAvailable": ",".join(self._abilities.values())
        }


class WebpageData:
    def __init__(self) -> None:
        self._characters: List[Character] = []
        self._background = "village.png"
        self._weather = Weather.CLEAR

    @property
    def background(self) -> str:
        return self._background

    @property
    def weather(self) -> Weather:
        return self._weather

    def set_background(self, background: str) -> None:
        self._background = background

    def set_weather(self, weather: Weather) -> None:
        self._weather = weather

    def get_character_names(self) -> List[str]:
        return [x.name for x in self._characters]

    def get_character_by_name(self, name: str) -> Optional[Character]:
        for character in self._characters:
            if name == character.name:
                return character

        return None

    def add_character(self, character: Character) -> None:
        new_char = character
        character_names = self.get_character_names()
        if new_char.name in character_names:
            new_char.update_hp(name=get_unique_name(new_char.name, character_names), hp=None)

        self._characters.append(new_char)

    def remove_character(self, character: Character) -> None:
        self._characters.remove(character)

    def remove_character_by_name(self, character_name: str) -> None:
        if character_name in self.get_character_names():
            character = self.get_character_by_name(character_name)
            self._characters.remove(character)

    def get_roster(self) -> Dict[str, Dict[str, Union[str, int]]]:
        return {y.name: y.entry() for y in self._characters}

    def get_selected_data(self) -> dict[str, str]:
        return  {"weather": str(self.weather.name.lower()), "background": self.background}
