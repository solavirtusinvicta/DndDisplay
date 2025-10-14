import tornado


class ControlHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <h1>Control Panel</h1>
        <div id="background"></div>
        <form id="addForm" enctype="multipart/form-data">
          <input name="name" placeholder="Character Name" pattern="[A-Za-z]+" required>
          <input name="hp" type="number" placeholder="HP" style="width: 50px" required><span> / </span>
          <input name="maxHp" type="number" placeholder="MaxHP" style="width: 50px" required>
          <input type="file" name="file">
          <button type="submit">Add Character</button>
        </form>
        <hr>
        <div id="charList"></div>

        <script>
        function refreshGlobal(backgrounds, weathers, currentBg, currentWeather) {
            let div = document.getElementById("background");
            let html = `
              <label for="backgroundSelect">Background:</label>
              <select name="background" id="backgroundSelect" onchange="setBg(this.value)">
            `;
            for (let bg of backgrounds) {
                html += `<option value="${bg}" ${bg === currentBg ? " selected" : ""}>${bg}</option>`;
            }
            html += "</select>";

            html += `
              <label for="backgroundSelect">Weather:</label>
              <select name="weather" id="weatherSelect" onchange="setWeather(this.value)">
            `;
            for (let w of weathers) {
                html += `<option value="${w}" ${w === currentWeather ? " selected" : ""}>${w}</option>`;
            }
            html += "</select>";
            div.innerHTML = html;
        }
        
        function refreshList(chars) {
            let div = document.getElementById("charList");
            div.innerHTML = "";
            for (let c in chars) {
                let char = chars[c];
                div.innerHTML += `<p>${c} (HP: ${chars[c].hp} / ${chars[c].maxHp})
                  <button onclick="updateChar('${c}', 1)">+1</button>
                  <button onclick="updateChar('${c}', -1)">-1</button>
                  <button onclick="removeChar('${c}')">Remove</button></p>
                  <span>Initiative: ${chars[c].initiative} </span><input id="initiative${c}" name="initiative" type="number" placeholder="Initiative" style="width: 45px" onchange="updateInitiative('${c}', this.value)" value="${chars[c].initiative}">
                  <input id="abilityInput${c}" name="ability" placeholder="Ability Name" pattern="[A-Za-z]+" required>
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
                if (e.target.matches("button[id^='updateInitiative']")) {
                    const c = e.target.id.replace("updateInitiative", "");
                    const initiative = document.getElementById("initiative" + c).value;
                }
            });
        }
        
        function setBg(bg) {
            fetch("/setBg", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({background:bg})
            });
        }
        function setWeather(weather) {
            fetch("/setWeather", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({weather:weather})
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

        function updateInitiative(name, initiative) {
            fetch("/updateInitiative", {
                method:"POST", 
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({name:name, initiative:initiative})
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
            console.log(data);
            if (data.characters) refreshList(data.characters);
            if (data.backgroundOptions && data.weatherOptions) {
                refreshGlobal(data.backgroundOptions, data.weatherOptions, data.background, data.weather);            
            }
        };
        </script>
        """)

