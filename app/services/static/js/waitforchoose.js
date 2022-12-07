$(document).ready(function() {

  function draw(clickX,clickY,clickDrag) {
    context = document.getElementById('canvas').getContext("2d");

    context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas

    context.strokeStyle = "#df4b26";
    context.lineJoin = "round";
    context.lineWidth = 5;

    for(var i=0; i < clickX.length; i++) {
      context.beginPath();
      if(clickDrag[i] && i) {
        context.moveTo(clickX[i-1], clickY[i-1]);
       } else {
         context.moveTo(clickX[i]-1, clickY[i]);
       }
       context.lineTo(clickX[i], clickY[i]);
       context.closePath();
       context.stroke();
    }
    // wait for guesses to be done
  }

  function change_gamestate(room_code) {
    url = `http://${window.location.host}/gamecontroller/` + room_code + "/change"
    console.log("change game")
    fetch(url).then(function(response) {
        sessionStorage.setItem("page","score")
        location.reload(true)
    }).catch(function(err) {
      console.log("Update Game ERROR: " + err)
    });
  }

  function check_choices() {
    room = sessionStorage.getItem("id")
    url = `http://${window.location.host}/room/` + room + "/check_choices"
    fetch(url).then(function(response) {
      response.json().then(function(data) {
        if (data == "0") {
          change_gamestate()
        }
      })
    })
  }


  function add_guess_button(guess_text) {
    console.log("adding " + guess_text)
    new_guess = document.createElement("div")
    new_guess.setAttribute("class","guess")
    new_guess.innerHTML = guess_text
    $("#guess_container").append(new_guess)
    $(new_guess).click(function() {
        c = this.innerHTML;
        n = sessionStorage.getItem("name")
        data = {choice:c,name:n}
        submit_guess(data)
    })
  }

  function get_guesses() {
    room = sessionStorage.getItem("id")
    url = `http://${window.location.host}/player/` + room + "/all_guesses"
    fetch(url).then(function(response) {
      response.json().then(function(data) {
        console.log(data)
        image = JSON.parse(data["image"])
        clickX = image.map(x => x[0])
        clickY = image.map(x => x[1])
        clickDrag = image.map(x => x[2])

        draw(clickX,clickY,clickDrag)
        console.log("image drawn")
        guesses = (data["guesses"])
        truth = data["truth"]

        random_num = Math.floor(Math.random()*guesses.length)

        for (var i = 0; i < random_num; i++) {
          add_guess_button(guesses[i].guess)
        }
        add_guess_button(truth)
        for (var i = random_num; i < guesses.length; i++ ) {
          add_guess_button(guesses[i].guess)
        }
        var intervalID = setInterval(check_choices, 1000)
      })
    })
  }
  get_guesses()
})
