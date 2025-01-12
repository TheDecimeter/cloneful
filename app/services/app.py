from __future__ import print_function
from init import db, app
from flask import request,jsonify,render_template,abort,flash,Response
from werkzeug.utils import secure_filename
import random
from models import Room, Player, Prompt
import random
import json
import time
import sys
import os

# TODO: Unify bodies of PUT requests room_id should be same for every request
# TODO: Unify URLs for room_id, have passed in url not body

# TODO: Create funciton for getting prompt for the current round
# TODO: Beautify the UI!

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response
app.after_request(add_cors_headers)
db.create_all()

""" Creates a 4 upper case room code """
def generate_room_code():
    code = ""
    for i in range(4):
        r = random.randint(0,25)
        c = chr(65+r)
        code += c
    return code

# TODO: Move to init file
""" adds prompts from /static/prompts/prompts.csv to table"""
def add_prompts_from_file():
    filename = os.path.join("static","prompts","prompts.csv")
    file = open(filename,"r")
    for line in file:
        new_prompt = Prompt(text=str(line))
        db.session.add(new_prompt)
    db.session.commit()
add_prompts_from_file()


""" Start of Routes """

""" Display base template """
@app.route("/")
def display_webpage():
    return render_template("index.html")

""" Return <room_id> from table """
@app.route("/room/<string:room_id>",methods=["GET"])
def get_specific_room(room_id):
    room = Room.query.filter_by(id=room_id).first()
    return jsonify(room.serialize())

""" Return all rooms """
@app.route("/room",methods=["GET"])
def get_all_rooms():
    return jsonify(list(map(lambda x:x.serialize(),Room.query.all())))

# TODO: Clear old file creation stuff
""" Creates a room
    Takes body: name """
@app.route("/room",methods=["PUT"])
def create_room():
    print("danx create room")
    rc = generate_room_code()
    host = str(request.json["name"])
    gameState = 0
    data = [rc,host]
    new_room = Room(id=rc,host=host)
    new_player = Player(id=rc,name=host)

    db.session.add(new_player)
    db.session.add(new_room)
    db.session.commit()
    return jsonify(new_room.serialize())


""" Return list of all players """
@app.route("/player",methods=["GET"])
def get_player():
    print("danx get player")
    return jsonify(list(map(lambda x:x.serialize(),Player.query.all())))

""" Returns all players in <room_id> """
@app.route("/player/<string:room_id>",methods=["GET"])
def get_all_player_in_room(room_id):
    print("danx get all player in room")
    players = Player.query.filter_by(id=room_id).all()
    r = list(map((lambda x: x.serialize()),players))
    return jsonify(r)

""" Adds a new player
    Takes body: name, room """
@app.route("/player",methods=["PUT"])
def add_player():
    print("danx add player")
    room = str(request.json["room"])
    name = str(request.json["name"])
    target_room = Room.query.get_or_404(room)
    if target_room is None:
        abort(400)
    if target_room.gameState != 0:
        abort(400)
    num_players_in_room = Player.query.filter_by(id=room).count()
    if num_players_in_room >= 8:
        abort(400)
    check_not_in_room = Player.query.filter_by(id=room,name=name)
    if not check_not_in_room:
        abort(400)
    new_player = Player(id=room,name=name)
    db.session.add(new_player)
    db.session.commit()
    return jsonify(new_player.serialize())


""" Adds a players image to the table
    body: id,name,image """
@app.route("/player/submitimage", methods=["PUT"])
def add_image():
    print("danx add image")
    player = request.json["name"]
    room = request.json["id"]
    Player.query.filter_by(id=room,name=player).update(dict(drawing=json.dumps(request.json["image"])))
    db.session.commit()
    return jsonify(request.json["image"])

# TODO: clean up (may be from old set up)
@app.route("/room/<string:room_id>/players", methods=["GET"])
def num_players_in_room(room_id):
    print("danx num players in room")
    room = Room.query.filter_by(id=room_id).first()
    if room == None:
        abort(404)
    return str(room.players)

# TODO: clean up (may be from old set up)
@app.route("/room/<string:room_id>/players", methods=["PUT"])
def add_player_to_room(room_id):
    print("danx add player to room")
    room = Room.query.filter_by(id=room_id).first()
    add_one_player = str(int(room.players) + 1)
    Room.query.filter_by(id=room_id).update(dict(players=add_one_player))
    db.session.commit()
    return str(add_one_player)

@app.route("/player/<string:room_id>/<string:name>/prompt", methods=["GET"])
def get_prompt(room_id,name):
    print("danx get prompt")
    prompt = Player.query.filter_by(id=room_id,name=name).first().prompt
    return jsonify(prompt)

""" Returns number of players who have submitted an image """
@app.route("/room/<string:room_id>/check_subs",methods=["GET"])
def check_everyone_submitted(room_id):
    print("danx check everyone submitted")
    submissions = list(filter(lambda x: x.drawing == u'', Player.query.filter_by(id=room_id).all()))
    if submissions == None:
        return jsonify(0)
    return jsonify(len(submissions))

@app.route("/room/<string:room_id>/check_choices", methods=["GET"])
def check_everyone_chosen(room_id):
    print("danx check everyone chosen")
    room = room_id
    choices = list(filter(lambda x: len(x.choice) == 0, Player.query.filter_by(id=room_id).all()))
    if len(choices) == 1:
        return jsonify(0)
    return jsonify(len(choices))

""" Returns "True" if 60 seconds has elapsed since the drawing session started
    Else returns time left before forced submission"""
@app.route("/gamecontroller/<string:room_id>/time")
def check_time(room_id):
    print("danx checktime")
    start_time = Room.query.filter_by(id=room_id).first().start_time
    current_time = int(time.time())
    if (start_time + 60 < current_time):
        return jsonify("True")
    else:
        return jsonify(str(current_time - start_time))

""" Starts the timer for <room_id> """
@app.route("/gamecontroller/<string:room_id>/start_timer")
def start_time(room_id):
    print("danx start time")
    cur_time = int(time.time())
    Room.query.filter_by(id=room_id).update(dict(start_time=cur_time))
    db.session.commit()
    return jsonify(cur_time)


def add_prompts(room_id):
    print("danx add prompts")
    players = Player.query.filter_by(id=room_id).all()
    num_players = len(players)
    all_prompts = list(map(lambda x:  x.text, Prompt.query.all()))
    random.shuffle(all_prompts)
    sliced_prompts = all_prompts[:num_players]
    for i,p in enumerate(players):
        Player.query.filter_by(id=room_id,name=p.name).update(dict(prompt=sliced_prompts[i]))
    db.session.commit()

""" Changes the game state to signal clients to change mode """
@app.route("/gamecontroller/<string:room_id>/change",methods=["GET"])
def change_gamestate(room_id):
    print("danx change gamestate "+room_id)
    room = str(room_id)
    target_room = Room.query.get_or_404(room)
    current_gamestate = target_room.gameState

    current_gamestate += 1
    if current_gamestate == 1:
        add_prompts(room)
    print (current_gamestate, file=sys.stderr)
    Room.query.filter_by(id=room).update(dict(gameState=current_gamestate))
    db.session.commit()
    return str(current_gamestate)

""" Sets the drawing for player
    Takes body: room, name, guess """
@app.route("/player/<string:room_id>/submitdrawing", methods=["PUT"])
def submit_drawing(room_id):
    print("danx submit drawing")
    room = str(room_id)
    name = request.json["name"]
    drawing = request.json["drawing"]
    Player.query.filter_by(id=room,name=name).update(dict(drawing=drawing))
    db.session.commit()
    return request.json["drawing"]


""" Return the name of the owner of the current picture """
@app.route("/room/<string:room_id>/imageowner", methods=["GET"])
def get_image_owner(room_id):
    print("danx get image owner")
    viewing = Room.query.filter_by(id=room_id).first().viewing
    players =list(map(lambda x: x.name, Player.query.filter_by(id=room_id).all()))
    return jsonify(players[viewing])

""" Return a picture and increment viewing or end flag """
@app.route("/room/<string:room_id>/image",methods=["GET"])
def get_next_image(room_id):
    print("danx get next image")
    images = list(map(lambda x: x.drawing, Player.query.filter_by(id=room_id).all()))
    toReturn = Room.query.filter_by(id=room_id).first().viewing
    if toReturn >= len(images):
        return jsonify("End")
    else:
        return jsonify(images[toReturn])

""" Set the guess for player
    Takes body: name, guess """
@app.route("/player/<string:room_id>/guess",methods=["PUT"])
def submit_guess(room_id):
    print("danx submit guess")
    name = request.json["name"]
    guess = request.json["guess"]
    Player.query.filter_by(id=room_id,name=name).update(dict(guess=guess))
    db.session.commit()
    return jsonify(guess)


""" Get number of players who have not guessed """
@app.route("/player/<string:room_id>/check_guesses",methods=["GET"])
def get_num_guesses(room_id):
    print("danx get num guesses")
    guesses = list(filter(lambda x: x.guess == u'', Player.query.filter_by(id=room_id).all()))
    if len(guesses) == 1:
        # everyone has guessed
        return jsonify(0)
    return jsonify(len(guesses))

def add_score_to_players(owner,guesser,room_id):
    print (owner,guesser,room_id,file=sys.stderr)
    owner_score = int(Player.query.filter_by(id=room_id,name=owner).first().score)
    guesser_score = int(Player.query.filter_by(id=room_id,name=guesser).first().score)
    Player.query.filter_by(id=room_id,name=owner).update(dict(score=(owner_score+100)))
    Player.query.filter_by(id=room_id,name=guesser).update(dict(score=guesser_score+100))

""" Eval round and update scores """
# TODO: Fix function so extreme case are accounted for ie. player picking their own
@app.route("/room/<string:room_id>/finishRound")
def finish_round(room_id):
    print("danx finish round")
    room = str(room_id)
    viewing = Room.query.filter_by(id=room).first().viewing
    prompt =  Player.query.filter_by(id=room).all()[viewing].prompt
    owner = Player.query.filter_by(id=room,guess=u'').first()

    for player in Player.query.filter(Player.id == room,Player.guess != u'').all():
        if player.choice == prompt:
            add_score_to_players(owner.name,player.name,room)
        else:
            # guessed someone elses
            lier = Player.query.filter_by(id=room_id,guess=player.choice).first()
            lier_score = int(lier.score)
            Player.query.filter_by(id=room,name=lier.name).update(dict(score=lier_score + 100))
    Room.query.filter_by(id=room_id).update(dict(scoresUpdated=1))

    num_images = len(Player.query.filter_by(id=room).all())
    end_flag = 0
    if (viewing >= num_images-1):
        Room.query.filter_by(id=room_id).update(dict(gameState=6))
        db.session.commit()
        end_flag = 1
    db.session.commit()
    return jsonify(end_flag)

""" Check if round has been evalulated """
@app.route("/room/<string:room_id>/check_scored")
def check_scored(room_id):
    print("danx check scored")
    room = str(room_id)
    return jsonify(Room.query.filter_by(id=room).first().scoresUpdated)
""" Gets all guesses """
@app.route("/player/<string:room_id>/all_guesses", methods=["GET"])
def get_all_guesses(room_id):
    print("danx get all guesses")
    room = str(room_id)
    viewing = Room.query.filter_by(id=room).first().viewing
    prompt = Player.query.filter_by(id=room).all()[viewing].prompt
    images = list(map(lambda x:x.drawing, Player.query.filter_by(id=room).all()))
    all_guesses = list(map(lambda x: {'name':x.name, 'guess':x.guess}, Player.query.filter_by(id=room).all()))
    remove_empty = list(filter(lambda x: x["guess"] != u'', all_guesses))
    prompt_and_guesses = {'image':images[viewing], 'truth':prompt, 'guesses':remove_empty}
    return jsonify(prompt_and_guesses)

@app.route("/player/<string:room_id>/set_choice",methods=["PUT"])
def set_player_choice(room_id):
    print("danx set player choice")
    room = str(room_id)
    choice = request.json["choice"]
    player = request.json["name"]
    Player.query.filter_by(id=room_id,name=player).update(dict(choice=choice))

    viewing = Room.query.filter_by(id=room).first().viewing
    p= Player.query.filter_by(id=room).all()[viewing]
    prompt =  p.prompt
    if (choice == prompt):
        owner = Player.query.filter_by(id=room,guess=u'').first().name
        add_score_to_players(owner,player,room)
    else:
        lier = Player.query.filter_by(id=room_id,guess=p.choice).first()
        lier_score = int(lier.score)
        Player.query.filter_by(id=room,name=lier.name).update(dict(score=lier_score + 100))
    db.session.commit()
    return ""



""" Retunrs ordered the scoreboard """
@app.route("/room/<string:room_id>/scores", methods=["GET"])
def get_scores(room_id):
    print("danx get scores")
    room = str(room_id)
    scores = Player.query.filter_by(id=room).order_by(Player.score).all()
    return jsonify(list(map(lambda x: x.serialize(), scores)))

""" Construction Zone """
""" Resets gamestate to guessing if another round can happen else end """
@app.route("/gamecontroller/<string:room_id>/next")
def get_next_stage(room_id):
    print("danx get next stage")
    images = list(map(lambda x: x.drawing, Player.query.filter_by(id=room_id).all()))
    images_viewed = Room.query.filter_by(id=room_id).first().viewing
    Room.query.filter_by(id=room_id).update(dict(gameState=2,scoresUpdated=0,viewing=images_viewed+1))
    Player.query.filter_by(id=room_id).update(dict(choice=u'',guess=u''))
    db.session.commit()
    return jsonify(2)

""" Get gamestate """
@app.route("/gamecontroller/<string:room_id>/state")
def get_state(room_id):
    print("danx get state")
    state = Room.query.filter_by(id=room_id).first().gameState
    return jsonify(state)
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True,threaded=True)
