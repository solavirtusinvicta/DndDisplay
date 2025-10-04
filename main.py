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

    @property
    def hp(self) -> int:
        return self._hp

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
                  <button onclick="updateChar('${c}', 1)">+1</button>
                  <button onclick="updateChar('${c}', -1)">-1</button>
                  <button onclick="removeChar('${c}')">Remove</button></p>`;
            }
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
        
          /* container for all characters */
          #chars {
            display: flex;
            justify-content: center; /* center rows */
            align-items: flex-start;
            gap: 10px;               /* space between cards */
            overflow: hidden;        /* no scrollbars */
            padding: 10px;
          }
        
          .char {
            margin: 10px;
            padding: 10px;
            border: 2px solid white;
            background: #111;
            flex: 1 1 180px;         /* allow shrink/grow with min width */
            max-width: 220px;        /* prevent cards from being huge */
            text-align: center;
          }
        
          .name {
            font-size: 1.2em;
            margin-bottom: 5px;
          }
        
          .hp-bar-bg {
            width: 100%;
            height: 20px;
            background: #555;
            border-radius: 5px;
            overflow: hidden;
            margin-bottom: 5px;
          }
        
          .hp-bar {
            height: 100%;
            background: red;
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
                let hpPercent = Math.max(0, char.hp);
                div.innerHTML += `<div class="char">
                  <div class="name">${c}</div>
                  <div class="hp-bar-bg">
                      <div class="hp-bar" style="width:${hpPercent}%;"></div>
                  </div>
                  ${char.image ? `<img src="${char.image}" width="150">` : ""}
                  <div class="hp-text">HP: ${char.hp}</div>
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
