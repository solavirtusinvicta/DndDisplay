import os

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape

clients = set()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
assert os.path.isdir(STATIC_DIR)


class Character:
    name: str = ""
    hp: int = 0
    initiative: int = 0


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
        <html>
            <head><title>DM Control</title></head>
            <body>
                <h1>DM Control Panel</h1>
                <form id="form">
                    Enemy Name: <input id="enemy" type="text"><br>
                    HP: <input id="hp" type="number"><br>
                    <button type="submit">Update</button>
                </form>
                <br>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <label>Enemy Image:</label>
                    <input type="file" name="file">
                    <input type="submit" value="Upload">
                </form>
                <script>
                const form = document.getElementById("form");
                form.addEventListener("submit", async (e) => {
                    e.preventDefault();
                    const enemy = document.getElementById("enemy").value;
                    const hp = document.getElementById("hp").value;
                    fetch("/update", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({enemy, hp})
                    });
                });
                </script>
            </body>
        </html>
        """)


class DisplayHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <html>
            <head>
                <title>Display</title>
                <style>
                    body { font-family: sans-serif; background: black; color: white; text-align: center; }
                    #enemy { font-size: 4em; }
                    #hp { font-size: 6em; color: red; }
                    img { max-width: 80%; max-height: 60vh; margin-top: 20px; }
                </style>
            </head>
            <body>
                <div id="enemy">No enemy</div>
                <div id="hp">--</div>
                <img id="enemyImg" src="" style="display:none;">
                <script>
                const ws = new WebSocket("ws://" + location.host + "/ws");
                ws.onmessage = (msg) => {
                    const data = JSON.parse(msg.data);
                    if (data.enemy) document.getElementById("enemy").textContent = data.enemy;
                    if (data.hp) document.getElementById("hp").textContent = "HP: " + data.hp;
                    if (data.image) {
                        const img = document.getElementById("enemyImg");
                        img.src = data.image + "?t=" + Date.now(); // cache-bust
                        img.style.display = "block";
                    }
                };
                </script>
            </body>
        </html>
        """)


class UpdateHandler(tornado.web.RequestHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        for c in clients:
            c.write_message(data)
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


def make_app():
    return tornado.web.Application([
        (r"/control", ControlHandler),
        (r"/display", DisplayHandler),
        (r"/update", UpdateHandler),
        (r"/upload", UploadHandler),
        (r"/ws", DisplayWebSocket),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_DIR}),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Server started at http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()