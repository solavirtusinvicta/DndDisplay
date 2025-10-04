import json
import os
import re
from dataclasses import dataclass
from typing import Union, Dict, List, Optional

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
    def __init__(self, name: str, hp: int, img: str) -> None:
        self._name = name
        self._hp = hp
        self._img = img
        self._initiative: int = 0

    @property
    def name(self) -> str:
        return self._name

    def update(self, name: Optional[str], hp: Optional[int]):
        if name is not None:
            self._name = name
        if hp is not None:
            self._hp = hp

    def entry(self) -> Dict[str, Union[str, int]]:
        return {"hp": self._hp, "image": self._img}


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


# characters: Dict[str, Dict[str, Union[str, int]]] = {}  # { "Alice": {"hp": 20, "image": "/static/foo.png"}, ... }


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
            <input name="name" placeholder="Character Name">
            <input name="hp" type="number" placeholder="HP">
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
                div.innerHTML += `<p>${c} (HP: ${chars[c].hp})
                  <button onclick="removeChar('${c}')">Remove</button></p>`;
            }
        }

        function removeChar(name) {
            fetch("/remove", {method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name})});
        }
        
        function updateChar(name) {
            fetch("/update", {method:"POST", headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name})});
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
        <script>
        function render(chars) {
            let div = document.getElementById("chars");
            div.innerHTML = "";
            for (let c in chars) {
                let char = chars[c];
                div.innerHTML += `<div>
                  <h2>${c} (HP: ${char.hp})</h2>
                  ${char.image ? `<img src="${char.image}" width="150">` : ""}
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
        name = self.get_body_argument("name")
        hp = int(self.get_body_argument("hp"))
        character = chars.get_by_name(name)
        if character is not None:
            character.update(name, hp)
        broadcast()
        self.write("ok")


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
        image_url = ""
        if "file" in self.request.files:
            fileinfo = self.request.files["file"][0]
            filepath = os.path.join(STATIC_DIR, fileinfo["filename"])
            with open(filepath, "wb") as f:
                f.write(fileinfo["body"])
            image_url = f"/static/{fileinfo['filename']}"
        chars.add(Character(name, hp, image_url))
        broadcast()


class RemoveHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode())
        name = data["name"]
        chars.remove_by_name(name)
        broadcast()


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/control", ControlHandler),
        (r"/display", DisplayHandler),
        (r"/ws", WSHandler),
        (r"/add", AddHandler),
        (r"/remove", RemoveHandler),
        (r"/update", UpdateHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_DIR}),
    ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
