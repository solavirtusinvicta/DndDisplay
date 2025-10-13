import json
import os
from typing import Any, Generator, Optional

import tornado.ioloop
import tornado.web
import tornado.websocket

from character import Character, WebpageData
from control import ControlHandler
from display import DisplayHandler
from utility import STATIC_DIR, get_options, Weather

clients = set()
assert os.path.isdir(STATIC_DIR)
webpage_data = WebpageData()


# TODO: Features:
# status effects (poisoned, stunned, etc)


def broadcast():
    for c in list(clients):
        c.write_message({"characters": webpage_data.get_roster()} | get_options() | webpage_data.get_selected_data())


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server running. Go to /control or /display.")


class WSHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.add(self)
        self.write_message({"characters": webpage_data.get_roster()} | get_options() | webpage_data.get_selected_data())

    def on_close(self):
        clients.discard(self)


class BaseCharacterHandler(tornado.web.RequestHandler):
    def json_parse(self, *key: str) -> Generator[Any, Any, None]:
        data = json.loads(self.request.body.decode())
        return (data.get(k, 0) for k in key)

    @staticmethod
    def get_character(name: str) -> Optional[Character]:
        return webpage_data.get_character_by_name(name)


class UpdateHpHandler(BaseCharacterHandler):
    def post(self):
        name, delta = self.json_parse("name", "delta")
        character = self.get_character(name)

        if character is not None:
            character.update_hp(name, character.hp + delta)
            broadcast()
        self.write({"status": "ok"})


class UpdateInitiativeHandler(BaseCharacterHandler):
    def post(self):
        name, initiative = self.json_parse("name", "initiative")
        character = webpage_data.get_character_by_name(name)

        if character is not None:
            character.update_initiative(initiative)
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


class AddHandler(BaseCharacterHandler):
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
        webpage_data.add_character(Character(name, hp, max_hp, image_url))
        broadcast()


class AddAbilityHandler(BaseCharacterHandler):
    def post(self):
        name, ability = self.json_parse("name", "ability")
        webpage_data.get_character_by_name(name).add_ability(ability)
        broadcast()


class RemoveAbilityHandler(BaseCharacterHandler):
    def post(self):
        name, ability = self.json_parse("name", "ability")
        webpage_data.get_character_by_name(name).remove_ability(ability)
        broadcast()


class SetWeatherHandler(BaseCharacterHandler):
    def post(self):
        weather = list(self.json_parse("weather"))[0]
        webpage_data.set_weather(Weather(weather))
        broadcast()


class SetBackgroundHandler(BaseCharacterHandler):
    def post(self):
        background = list(self.json_parse("background"))[0]
        webpage_data.set_background(background)
        broadcast()


class RemoveHandler(BaseCharacterHandler):
    def post(self):
        name = self.json_parse("name")
        webpage_data.remove_character_by_name(name)
        broadcast()

class SetAvailableAbilitiesHandler(BaseCharacterHandler):
    def post(self):
        name, ability = self.json_parse("name", "ability")
        character = webpage_data.get_character_by_name(name)
        if character is not None:
            character.toggle_ability(ability)
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
        (r"/update", UpdateHpHandler),
        (r"/updateInitiative", UpdateInitiativeHandler),
        (r"/setAvailableAbilities", SetAvailableAbilitiesHandler),
        (r"/setBg", SetBackgroundHandler),
        (r"/setWeather", SetWeatherHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_DIR}),
    ], debug=True)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
