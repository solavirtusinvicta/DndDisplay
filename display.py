import tornado


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

          .initiative {
            font-size: 1.5em;
            font-weight: bold;
            text-align: right;
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
                  <div class="name">${c}<div class="initiative">${char.initiative}</div></div>
                  <div class="hp-bar-bg">
                      <div class="hp-bar" style="width:${hpPercent}%;"></div>
                  </div>
                  ${char.image ? `<img src="${char.image}" width="150">` : ""}
                  <div class="hp-text">HP: ${char.hp} / ${char.maxHp}</div>
                  <div class="abilities">
                    Abilities: ${
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

