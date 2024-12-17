import socketio
import numpy as np
import time

# create a Socket.IO server
sio = socketio.Server()

# wrap with a WSGI application
app = socketio.WSGIApp(sio, static_files = {
    '/': '../client/',
})

# --- event example ---
#@sio.event
#def my_event(sid, data):
#    pass
#
#sio.emit('my event', {'data': 'foobar'}, to=user_sid) # just one
#sio.emit('my event', {'data': 'foobar'}) # all

RATIO = 16/9

HEIGHT = 1.0
WIDTH = HEIGHT * RATIO

PADDING = 0.1 * HEIGHT
PITCH_X_BEGIN = PADDING
PITCH_X_END = WIDTH - PADDING

PITCH_Y_BEGIN = PADDING
PITCH_Y_END = HEIGHT - PADDING

class Body:
    def __init__(self, mass: float, radius: float, poz, color = '#ffffff', stationary = False, kicking = False, used_kick = True, name = None): # poz este vector 2D
        self.rest_mass = mass
        self.mass = mass
        self.R = radius
        self.x = np.copy(poz)
        self.v = np.zeros(2) # obiectele sunt initial in repaus
        self.F = np.zeros(2) # forta externa
        self.stationary = stationary
        self.color = color
        self.kicking = kicking
        self.used_kick = used_kick
        self.keystates = None
        self.name = name

class Player:
    def __init__(self, name, team: bool, sid):
        self.name = name
        self.team = team
        self.sid = sid
        self.body = None

players = []

ball   = Body(4.0,  0.015, np.array([WIDTH / 2, HEIGHT / 2]))
#player = Body(10.0, 0.02, np.array([0.8 * WIDTH, HEIGHT / 2]), '#ff0000')

player_locations = [
    [np.array([0.2 * WIDTH, 0.5 * HEIGHT]), np.array([0.2 * WIDTH, 0.4 * HEIGHT]), np.array([0.2 * WIDTH, 0.6 * HEIGHT])],
    [np.array([0.8 * WIDTH, 0.5 * HEIGHT]), np.array([0.8 * WIDTH, 0.4 * HEIGHT]), np.array([0.8 * WIDTH, 0.6 * HEIGHT])]
]

team_colors = [
    '#0000ff',
    '#ff0000'
]

team_count = [
    0,
    0
]

player_bodies = []
sid2player = {}

POLE_BIG_Y = HEIGHT * 0.65
POLE_SMALL_Y = HEIGHT * 0.35
stalpi = [
    Body(4.0,  0.015, np.array([PITCH_X_END, POLE_BIG_Y]), '#ff0000', True),
    Body(4.0,  0.015, np.array([PITCH_X_END, POLE_SMALL_Y]), '#ff0000', True),
    Body(4.0,  0.015, np.array([PITCH_X_BEGIN, POLE_BIG_Y]), '#0000ff', True),
    Body(4.0,  0.015, np.array([PITCH_X_BEGIN, POLE_SMALL_Y]), '#0000ff', True),
]

corpuri = [ball] + stalpi

KICK_DISTANCE = 15e-3
KICK_MOMENTUM = 3

RESTITUTION = 0.80

keystates = {} # access by sid

NEXT_ROUND_DELAY = 3
score = [0, 0]
in_play = True
start_play = time.time() # when in_play = False a countdown starts until the next round
last_scorer = 0

# prepares arena for the round
def reset_coords():
    global ball
    global player_bodies
    global sid2player
    global sid2idx_type
    global corpuri
    global players
    global keystates

    ball.x = np.array([WIDTH / 2, HEIGHT / 2])
    ball.v = np.zeros(2)
    corpuri = [ball] + stalpi
    loc_idx = [0, 0]
    for player in players:
        P = Body(
            10.0,
            0.02,
            player_locations[player.team][loc_idx[player.team]],
            team_colors[player.team],
            name = player.name
        )
        P.keystates = keystates[player.sid]

        player_bodies.append(P)
        corpuri.append(P)
        player.body = P

def check_game_state():
    global NEXT_ROUND_DELAY
    global PITCH_X_BEGIN
    global PITCH_X_END

    global score
    global in_play
    global start_play
    global ball
    global last_scorer

    if in_play == False:
        if time.time() > start_play:
            in_play = True
            reset_coords()
    else:
        change_state = False
        if ball.x[0] < PITCH_X_BEGIN:
            last_scorer = 1
            change_state = True
        elif ball.x[0] > PITCH_X_END:
            last_scorer = 0
            change_state = True

        if change_state:
            score[last_scorer] += 1
            in_play = False
            start_play = time.time() + NEXT_ROUND_DELAY

BROADCAST_REFRESH = 1 / 150
last_emit_gamestate = None
def emit_gamestate():
    global corpuri
    global last_emit_gamestate

    now = time.time()
    if last_emit_gamestate == None:
        last_emit_gamestate = now - BROADCAST_REFRESH - 1

    delta = now - last_emit_gamestate
    if delta >= BROADCAST_REFRESH:
        last_emit_gamestate = now
        sio.emit('gamestate', {
            'bodies': [
                {
                    'x': corp.x[0],
                    'y': corp.x[1],
                    'R': corp.R,
                    'color': corp.color,
                    'kicking': corp.kicking,
                    'name': corp.name
                } for corp in corpuri
            ],
            'round_info': {
                'score': score,
                'in_play': in_play,
                'start_play': int(start_play * 1000),
                'last_scorer': last_scorer,
            }
        })

# team is bool
def add_player(sid, name, team):
    global keystates
    global players
    global sid2player

    reset_after = (len(players) == 0)

    team_count[team] += 1

    new_player = Player(name, team, sid)
    players.append(new_player)
    sid2player[sid] = new_player
    keystates[sid] = {
        'left': False,
        'right': False,
        'up': False,
        'down': False,
        'x': False,
    }

    if reset_after:
        reset_coords()

@sio.event
def connect(sid, environ, auth):
    print('connect ', sid)
    sio.emit('time_sync', {'server_time': int(1000 * time.time())})
    emit_gamestate()

@sio.event
def disconnect(sid):
    global keystates
    global player_bodies
    global players
    global sid2player
    global corpuri

    if not sid in sid2player:
        return

    player = sid2player[sid]
    body = player.body

    del sid2player[sid]
    del keystates[sid]

    if body != None:
        player_bodies.remove(body)
        corpuri.remove(body)
    players.remove(player)

    print('disconnect ', sid)

@sio.on('request_join')
def request_join(sid, data):
    team = data['team']
    name = data['name']

    if not name:
        sio.emit('request_deny', None, to = sid)
        return

    if not (team == 'red' or team == 'blue'):
        sio.emit('request_deny', None, to = sid)
        return

    team = (team == 'red')

    if team_count[team] >= len(player_locations[team]):
        sio.emit('request_deny', None, to = sid)
        return

    if sid in sid2player:
        sio.emit('request_deny', None, to = sid)
        return

    add_player(sid, name, team)
    sio.emit('request_accept', to = sid)

@sio.on('key_upd')
def key_upd(sid, data):
    global keystates
    #global players
    #global player_bodies

    if not sid in keystates:
        return

    keystates[sid][data['key']] = bool(data['new_state'])

    #emit_gamestate()

@sio.on('client_wants_update')
def client_wants_update(sid, data):
    #do_physics() # i do not have a smarter way of making a game loop here
    emit_gamestate()

def modul(vector):
    return np.sqrt(vector.dot(vector))

EPS = 1e-4

PHYSICS_REFRESH = 1 / 300
last_time = None
def do_physics():
    global player_bodies
    global ball
    global keystates
    global last_time

    now = time.time()
    if last_time == None:
        last_time = now - PHYSICS_REFRESH

    dt = now - last_time
    last_time = now

    if dt > 0.3:
        #print('yikes')
        return

    for player in player_bodies:
        if player.kicking == False and player.keystates['x'] == True:
            player.used_kick = False
        player.kicking = player.keystates['x']
        player.mass = player.rest_mass * (1.5 if player.kicking else 1.0)

    for C in corpuri:
        if C.stationary:
            C.mass = 1e6
        else:
            C.mass = C.rest_mass

    for player in player_bodies:
        player.F = np.array([
            player.keystates['right'] - player.keystates['left'],
            player.keystates['down'] - player.keystates['up']
        ]) * 8.0 - 0.8 * player.mass * player.v * 3

    ball.F = - 0.3 * ball.mass * ball.v * 2

    # ELASTIC COLLISION WITH THE BORDER --- NOT THE CASE IN REAL BONKIO??
    for C in player_bodies:
        if C.x[0] + C.R >= WIDTH - EPS:
            if C.v[0] > 0:
                C.v[0] = -RESTITUTION * C.v[0]
            C.F[0] = 0

        if C.x[0] - C.R <= 0.0 + EPS:
            if C.v[0] < 0:
                C.v[0] = -RESTITUTION * C.v[0]
            C.F[0] = 0

        if C.x[1] + C.R >= HEIGHT - EPS:
            if C.v[1] > 0:
                C.v[1] = -RESTITUTION * C.v[1]
            C.F[1] = 0

        if C.x[1] - C.R <= 0.0 + EPS:
            if C.v[1] < 0:
                C.v[1] = -RESTITUTION * C.v[1]
            C.F[1] = 0

    # ELASTIC COLLISION WITH THE BORDER - BALL
    if in_play:
        inside_goal = (ball.x[1] < POLE_BIG_Y and ball.x[1] > POLE_SMALL_Y)
        if ball.x[0] + ball.R >= PITCH_X_END - EPS and not inside_goal:
            if ball.v[0] > 0:
                ball.v[0] = -RESTITUTION * ball.v[0]
            ball.F[0] = 0

        if ball.x[0] - ball.R <= PITCH_X_BEGIN + EPS and not inside_goal:
            if ball.v[0] < 0:
                ball.v[0] = -RESTITUTION * ball.v[0]
            ball.F[0] = 0

        if ball.x[1] + ball.R >= PITCH_Y_END - EPS:
            if ball.v[1] > 0:
                ball.v[1] = -RESTITUTION * ball.v[1]
            ball.F[1] = 0

        if ball.x[1] - ball.R <= PITCH_Y_BEGIN + EPS:
            if ball.v[1] < 0:
                ball.v[1] = -RESTITUTION * ball.v[1]
            ball.F[1] = 0

    # ELASTIC COLLISION BETWEEN THE PLAYER AND THE BALL -- HOW TO INCLUDE RESTITUTION?
    N = len(corpuri)
    for idxA in range(N):
        for idxB in range(idxA+1, N):
            gigel = corpuri[idxA]
            dorel = corpuri[idxB]

            delta = gigel.x - dorel.x # de la player la ball
            delta_abs = modul(delta)
            norm = delta / delta_abs
            if delta_abs <= gigel.R + dorel.R + EPS:
                #perp = np.array([-norm[1], norm[0]])

                # IMPORTANT TO AVOID BALL AND PLAYER GETTING STUCK: MAKE THEM NOT COLLIDE
                gigel.x = dorel.x + norm * (gigel.R + dorel.R)

                a = norm.dot(dorel.v)
                b = norm.dot(gigel.v)

                vrel = b - a
                new_vrel = -RESTITUTION * (b - a)
                total_momentum = dorel.mass * a + gigel.mass * b

                # ma * a + mb * b = ma * A + mb * B
                # B - A = -R * (b - a)

                # ma * A + mb * B + ma * B - ma * A = momentum + ma * new_vrel
                # (mb + ma) B = momentum + ma * new_vrel

                A = (total_momentum - gigel.mass * new_vrel) / (dorel.mass + gigel.mass)
                B = (total_momentum + dorel.mass * new_vrel) / (dorel.mass + gigel.mass)

                #A = 2 * (a * dorel.mass + b * gigel.mass) / (dorel.mass + gigel.mass) - a
                #B = 2 * (a * dorel.mass + b * gigel.mass) / (dorel.mass + gigel.mass) - b

                dorel.v += norm * (A - a)
                gigel.v += norm * (B - b)

                # do we need to handle forces here? -- maybe, subject of later discussion

    # KICKING 2
    for player in player_bodies:
        if (not player.used_kick) and player.kicking and modul(player.x - ball.x) - player.R - ball.R <= KICK_DISTANCE:
            norm = (ball.x - player.x) / modul(player.x - ball.x)
            ball.v += KICK_MOMENTUM / ball.mass * norm
            player.used_kick = True

    for C in corpuri:
        if not C.stationary:
            a = C.F / C.mass
            C.v += a * dt
            C.x += C.v * dt # maybe +1/2dt^2 * F/m
            #C.x += (C.v + dt/2 * a) * dt

    check_game_state()

def game_loop():
    while True:
        do_physics()
        emit_gamestate()
        time.sleep(min(BROADCAST_REFRESH, PHYSICS_REFRESH))

import eventlet
eventlet.spawn(game_loop)
