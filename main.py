import json
import os
import re
from typing import Union, Dict, List, Optional, Tuple

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape

clients = set()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
assert os.path.isdir(STATIC_DIR)


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

    def update(self, name: Optional[str], hp: Optional[int]):
        if name is not None:
            self._name = name
        if hp is not None:
            self._hp = hp

    def entry(self) -> Dict[str, Union[str, int]]:
        return {"hp": self._hp, "maxHp": self._max_hp, "image": self._img, "abilities": ",".join(self._abilities.keys()), "abilityAvailable": ",".join(self._abilities.values())}


class Characters:
    def __init__(self) -> None:
        self._characters: List[Character] = []

    def get_character_names(self) -> List[str]:
        return [x.name for x in self._characters]

    def get_by_name(self, name: str) -> Optional[Character]:
        for character in self._characters:
            if name == character.name:
                return character

        return None

    def add(self, character: Character) -> None:
        new_char = character
        character_names = self.get_character_names()
        if new_char.name in character_names:
            new_char.update(name=get_unique_name(new_char.name, character_names), hp=None)

        self._characters.append(new_char)

    def remove(self, character: Character) -> None:
        self._characters.remove(character)

    def remove_by_name(self, character_name: str) -> None:
        if character_name in self.get_character_names():
            character = self.get_by_name(character_name)
            self._characters.remove(character)

    def to_json_formattable(self) -> Dict[str, Dict[str, Union[str, int]]]:
        return {y.name: y.entry() for y in self._characters}


chars = Characters()


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server running. Go to /control or /display.")


class DisplayWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("Display connected")
        clients.add(self)

    def on_close(self):
        print("Display disconnected")
        clients.remove(self)


class ControlHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <h1>Control Panel</h1>
        <form id="addForm" enctype="multipart/form-data">
            <input name="name" placeholder="Character Name" pattern="[A-Za-z]+">
            <input name="hp" type="number" placeholder="HP" size="5"><span> / </span>
            <input name="maxHp" type="number" placeholder="MaxHP" size="5">
            <input type="file" name="file">
            <button type="submit">Add Character</button>
        </form>
        <hr>
        <div id="charList"></div>

        <script>
        function refreshList(chars) {
            let div = document.getElementById("charList");
            div.innerHTML = "";
            for (let c in chars) {
                let char = chars[c];
                div.innerHTML += `<p>${c} (HP: ${chars[c].hp} / ${chars[c].maxHp})
                  <button onclick="updateChar('${c}', 1)">+1</button>
                  <button onclick="updateChar('${c}', -1)">-1</button>
                  <button onclick="removeChar('${c}')">Remove</button></p>
                  <input id="abilityInput${c}" name="ability" placeholder="Ability Name" pattern="[A-Za-z]+">
                  <button id="addAbilityBtn${c}">Add Ability</button>
                  <p>Abilities:</p>`;
                
                if (char.abilities.length !== 0) {
                    for (let a of char.abilities.split(",")) {
                        const checked = char.abilityAvailable.split(",")[char.abilities.split(",").indexOf(a)] === "1";
                        div.innerHTML += `<span>${a} | Available: </span>
                          <input type="checkbox" name="available${c}${a}" value="value1" ${checked ? "checked" : ""} onchange="setAvailableAbilities('${c}', '${a}')">
                          <button onclick="removeAbility('${c}', '${a}')">Remove Ability</button></p>`;
                    }
                }
            }
            
            div.addEventListener("click", function(e) {
                if (e.target.matches("button[id^='addAbilityBtn']")) {
                    const c = e.target.id.replace("addAbilityBtn", "");
                    const abilityName = document.getElementById("abilityInput" + c).value;
                    addAbility(c, abilityName);
                }
            });
        }
        
        function removeAbility(name, ability) {
            fetch("/removeAbility", {
                method:"POST", 
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name, ability:ability})
            });
        }     
        
        function addAbility(name, ability) {
            fetch("/addAbility", {
                method:"POST", 
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name, ability:ability})
            });
        }

        function removeChar(name) {
            fetch("/remove", {
                method:"POST", 
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name})
            });
        }
        
        function updateChar(name, delta) {
            fetch("/update", {
                method:"POST", 
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name, delta:delta})
            });
        }

        function setAvailableAbilities(charName, ability) {
            fetch("/setAvailableAbilities", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({name: charName, ability: ability})
            });
        }

        document.getElementById("addForm").addEventListener("submit", e=>{
            e.preventDefault();
            let formData = new FormData(e.target);
            fetch("/add", {method:"POST", body: formData});
        });

        let ws = new WebSocket("ws://" + location.host + "/ws");
        ws.onmessage = (msg)=>{
            let data = JSON.parse(msg.data);
            if (data.characters) refreshList(data.characters);
        };
        </script>
        """)


class DisplayHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <h1>Battlefield</h1>
        <div id="chars"></div>
        <style>
          body {
            font-family: sans-serif;
            background: grey;
            color: white;
            text-align: center;
            margin: 0;
            padding: 0;
          }
        
          #chars {
            display: flex;
            justify-content: center;
            align-items: flex-start;
            gap: 10px; 
            overflow: hidden;
            padding: 10px;
          }
        
          .char {
            margin: 10px;
            padding: 10px;
            border: 2px solid white;
            background: #111;
            flex: 1 1 180px;   
            max-width: 220px;
            text-align: center;
          }
        
          .name {
            font-size: 1.2em;
            margin-bottom: 5px;
          }
        
          .hp-bar-bg {
            width: 100%;
            height: 20px;
            background: #801401;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 5px;
          }
        
          .hp-bar {
            height: 100%;
            background: green;
            width: 100%;
            transition: width 0.3s;
          }
        
          .hp-text {
            font-size: 0.9em;
            margin-top: 5px;
          }
        
          img {
            max-width: 100%;
            max-height: 120px;
            display: block;
            margin: auto;
          }
        </style>

        <script>
        function render(chars) {
            let div = document.getElementById("chars");
            div.innerHTML = "";
            for (let c in chars) {
                let char = chars[c];
                let hpPercent = (Math.max(0, char.hp) / Math.max(char.hp, char.maxHp)) * 100;
                div.innerHTML += `<div class="char">
                  <div class="name">${c}</div>
                  <div class="hp-bar-bg">
                      <div class="hp-bar" style="width:${hpPercent}%;"></div>
                  </div>
                  ${char.image ? `<img src="${char.image}" width="150">` : ""}
                  <div class="hp-text">HP: ${char.hp} / ${char.maxHp}</div>
                  <div class="abilities">
                    Abilities: ${
                      console.log(char.abilities, char.abilityAvailable),
                      char.abilities && char.abilityAvailable
                        ? char.abilities
                            .split(",")
                            .filter((a, i) => char.abilityAvailable.split(",")[i] === "1")
                            .join(", ") || "None"
                        : "None"
                  }</div>                
                </div>`;
            }
        }

        let ws = new WebSocket("ws://" + location.host + "/ws");
        ws.onmessage = (msg)=>{
            let data = JSON.parse(msg.data);
            if (data.characters) render(data.characters);
        };
        </script>
        """)


class UpdateHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        delta = int(data.get("delta", 0))
        character = chars.get_by_name(name)

        if character is not None:
            character.update(name, character.hp + delta)

        broadcast()
        self.write({"status": "ok"})


class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        file1 = self.request.files['file'][0]
        filename = file1['filename']
        filepath = os.path.join(STATIC_DIR, filename)

        with open(filepath, 'wb') as f:
            f.write(file1['body'])

        image_url = f"/static/{filename}"
        update = {"image": image_url}
        for c in clients:
            c.write_message(update)

        self.write(f"Uploaded. <a href='/control'>Back to control</a>")


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.add(self)
        self.write_message({"characters": chars.to_json_formattable()})

    def on_close(self):
        clients.discard(self)


def broadcast():
    for c in list(clients):
        c.write_message({"characters": chars.to_json_formattable()})


class AddHandler(tornado.web.RequestHandler):
    def post(self):
        name = self.get_body_argument("name")
        hp = int(self.get_body_argument("hp"))
        max_hp = int(self.get_body_argument("maxHp"))
        image_url = ""
        if "file" in self.request.files:
            fileinfo = self.request.files["file"][0]
            filepath = os.path.join(STATIC_DIR, fileinfo["filename"])
            with open(filepath, "wb") as f:
                f.write(fileinfo["body"])
            image_url = f"/static/{fileinfo['filename']}"
        chars.add(Character(name, hp, max_hp, image_url))
        broadcast()


class AddAbilityHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        ability = data["ability"]
        chars.get_by_name(name).add_ability(ability)
        broadcast()


class RemoveAbilityHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        ability = data["ability"]

        chars.get_by_name(name).remove_ability(ability)
        broadcast()


class RemoveHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        chars.remove_by_name(name)
        broadcast()

class SetAvailableAbilitiesHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        ability = data["ability"]  # list of ability names
        char = chars.get_by_name(name)
        if char:
            char.toggle_ability(ability)
            broadcast()

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/control", ControlHandler),
        (r"/display", DisplayHandler),
        (r"/ws", WSHandler),
        (r"/add", AddHandler),
        (r"/addAbility", AddAbilityHandler),
        (r"/removeAbility", RemoveAbilityHandler),
        (r"/remove", RemoveHandler),
        (r"/update", UpdateHandler),
        (r"/setAvailableAbilities", SetAvailableAbilitiesHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_DIR}),
    ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
