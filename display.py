import tornado


class DisplayHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <h1>Battlefield</h1>
        <div id="header"></div>
        <div id="weather-effects"></div>
        <div id="weather"></div>
        <div id="chars"></div>
        <style>
          body {
            font-family: sans-serif;
            background: grey;
            color: white;
            text-align: center;
            margin: 0;
            padding: 0;
            overflow: hidden;
          }
          
          #weather-effects {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 0;
          }
          
          #header, #weather, #chars {
            position: relative;
            z-index: 1;
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
          
          .raindrop {
            width: 2px;
            height: 20px;
            background-color: white;
            animation: fall linear infinite;
            position: absolute;
            top: 0;
          }
          
          .fog {
            width: 1600px;
            height: 1000px;
            background-image: url('static/utility/fog.png');
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            animation: simmerLeft 100000s linear infinite;
            position: absolute;
            top: 0;
          }

          @keyframes fall {
            from { top: -20px; }
            to { top: 100vh; }
          }
          
          @keyframes simmerLeft {
            from { left: -1600px; }
            to { left: 20vw; }
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

        function rerenderBackground(data) {
            if (!data || !data.background) {
                document.body.style.background = ``;
                return;
            };
            document.body.style.backgroundImage = `url('static/backgrounds/${data.background}')`;
            document.body.style.backgroundRepeat = 'no-repeat';
            document.body.style.backgroundPosition = 'center center';
        }
        
        function rain() {
            const raindrop = document.createElement('div');
            raindrop.classList.add('raindrop');
            raindrop.style.left = Math.random() * window.innerWidth + 'px';
            raindrop.style.animationDuration = (0.5 + Math.random()) + 's';
            document.getElementById('weather-effects').appendChild(raindrop);
            setTimeout(() => {
                raindrop.remove();
            }, 2000);
        }

        function fog() {
            const fog = document.createElement('div');
            fog.classList.add('fog');
            fog.style.left = '-1600px';
            fog.style.animationDuration = (0.5 + Math.random()) + 's';
            document.getElementById('weather-effects').appendChild(fog);
            setTimeout(() => {
                fog.remove();
            }, 3000);
        }
        
        function startRain() {
            if (rainInterval === null) {
                rainInterval = setInterval(rain, 100);
            }
        }
        
        function startFog() {
            if (fogInterval === null) {
                fogInterval = setInterval(fog, 3000);
            }
        }

        function clearRaindrops() {
            document.querySelectorAll('.raindrop').forEach(drop => drop.remove());
            clearInterval(rainInterval);
            rainInterval = null;
        }

        function clearFog() {
            document.querySelectorAll('.fog').forEach(cloud => cloud.remove());
            clearInterval(fogInterval);
            fogInterval = null;
        }
        
        function updateWeather(weather) {
            if (weather === "rain") {
                console.log("Starting rain");
                document.getElementById("weather").innerText = "🌧️ Raining";
                clearFog();
                startRain();
            } else if (weather === "fog") {
                console.log("Starting fog");
                document.getElementById("weather").innerText = "🌫️ Foggy";
                clearRaindrops();
                startFog();
            } else {
                console.log("Clearing weather effects");
                document.getElementById("weather").innerText = "☀️ Clear";
                clearRaindrops();
                clearFog();
            }
        }
              
        let rainInterval = null;
        let fogInterval = null

        let ws = new WebSocket("ws://" + location.host + "/ws");
        ws.onmessage = (msg)=>{
            let data = JSON.parse(msg.data);
            if (data.characters) render(data.characters);
            if (data.background) {
                rerenderBackground(data);
            }
            if (data.weather) {
                updateWeather(data.weather);
            }
        };
        </script>
        """)

