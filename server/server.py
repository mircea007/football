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
    def __init__(self, mass: float, radius: float, poz, color = '#ffffff', stationary = False, kicking = False): # poz este vector 2D
        self.rest_mass = mass
        self.mass = mass
        self.R = radius
        self.x = np.copy(poz)
        self.v = np.zeros(2) # obiectele sunt initial in repaus
        self.F = np.zeros(2) # forta externa
        self.stationary = stationary
        self.color = color
        self.kicking = kicking
        self.keystates = None

ball   = Body(4.0,  0.015, np.array([WIDTH / 2, HEIGHT / 2]))
#player = Body(10.0, 0.02, np.array([0.8 * WIDTH, HEIGHT / 2]), '#ff0000')

player_locations = [
    np.array([0.2 * WIDTH, 0.5 * HEIGHT]),
    np.array([0.8 * WIDTH, 0.5 * HEIGHT]),
]

player_colors = [
    '#0000ff',
    '#ff0000'
]

used_positions = [
    0,
    0
]

players = []
sid2player = {}
sid2idx_type = {}

POLE_BIG_Y = HEIGHT * 0.7
POLE_SMALL_Y = HEIGHT * 0.3
stalpi = [
    Body(4.0,  0.015, np.array([PITCH_X_END, POLE_BIG_Y]), '#ff0000', True),
    Body(4.0,  0.015, np.array([PITCH_X_END, POLE_SMALL_Y]), '#ff0000', True),
    Body(4.0,  0.015, np.array([PITCH_X_BEGIN, POLE_BIG_Y]), '#0000ff', True),
    Body(4.0,  0.015, np.array([PITCH_X_BEGIN, POLE_SMALL_Y]), '#0000ff', True),
]

corpuri = [ball] + stalpi

KICK_DISTANCE = 10e-3
KICK_MOMENTUM = 1.5

keystates = {}

NEXT_ROUND_DELAY = 3
score = [0, 0]
in_play = True
start_play = time.time() # when in_play = False a countdown starts until the next round

def reset_coords():
    global ball
    global players
    global sid2player
    global sid2idx_type

    ball.x = np.array([WIDTH / 2, HEIGHT / 2])
    ball.v = np.zeros(2)
    for sid in sid2player:
        sid2player[sid].x = np.copy(player_locations[sid2idx_type[sid]])
        sid2player[sid].v = np.zeros(2)

def check_game_state():
    global NEXT_ROUND_DELAY
    global PITCH_X_BEGIN
    global PITCH_X_END

    global score
    global in_play
    global start_play
    global ball

    if in_play == False:
        if time.time() > start_play:
            in_play = True
            reset_coords()
    else:
        if ball.x[0] < PITCH_X_BEGIN:
            score[1] += 1
            in_play = False
            start_play = time.time() + NEXT_ROUND_DELAY

        elif ball.x[0] > PITCH_X_END:
            score[0] += 1
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
                    'kicking': corp.kicking
                } for corp in corpuri
            ],
            'round_info': {
                'score': score,
                'in_play': in_play,
                'start_play': int(start_play * 1000)
            }
        })

@sio.event
def connect(sid, environ, auth):
    global keystates
    global players
    global player_locations
    global player_colors
    global sid2player
    global corpuri

    print('connect ', sid)

    # if the lobby is full let others spectate
    if sum(used_positions) == len(used_positions):
        emit_gamestate()
        return

    player_idx = 0
    while used_positions[player_idx] == 1:
        player_idx += 1

    used_positions[player_idx] = 1

    new_player = Body(10.0, 0.02, player_locations[player_idx], player_colors[player_idx])
    players.append(new_player)
    corpuri.append(new_player)
    sid2player[sid] = new_player
    sid2idx_type[sid] = player_idx # avem nevoie la disconnect
    keystates[sid] = {
        'left': False,
        'right': False,
        'up': False,
        'down': False,
        'x': False,
    }
    new_player.keystates = keystates[sid]

    sio.emit('time_sync', {'server_time': int(1000 * time.time())})
    emit_gamestate()

@sio.event
def disconnect(sid):
    global keystates
    global players
    #global player_locations
    #global player_colors
    global sid2player
    global corpuri

    if not sid in sid2player:
        return

    player_type = sid2idx_type[sid]
    used_positions[player_type] = 0

    player = sid2player[sid]
    del sid2player[sid]
    del keystates[sid]

    players.remove(player)
    corpuri.remove(player)

    print('disconnect ', sid)

@sio.on('key_upd')
def key_upd(sid, data):
    global keystates
    global players

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
    global players
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

    for player in players:
        player.kicking = player.keystates['x']
        player.mass = player.rest_mass * (1.5 if player.kicking else 1.0)

    for C in corpuri:
        if C.stationary:
            C.mass = 1e6
        else:
            C.mass = C.rest_mass

    for player in players:
        player.F = np.array([
            player.keystates['right'] - player.keystates['left'],
            player.keystates['down'] - player.keystates['up']
        ]) * 8.0 - 0.8 * player.mass * player.v * 3

    ball.F = - 0.3 * ball.mass * ball.v * 2

    # ELASTIC COLLISION WITH THE BORDER --- NOT THE CASE IN REAL BONKIO??
    for C in players:
        if C.x[0] + C.R >= WIDTH - EPS:
            if C.v[0] > 0:
                C.v[0] = -C.v[0]
            C.F[0] = 0

        if C.x[0] - C.R <= 0.0 + EPS:
            if C.v[0] < 0:
                C.v[0] = -C.v[0]
            C.F[0] = 0

        if C.x[1] + C.R >= HEIGHT - EPS:
            if C.v[1] > 0:
                C.v[1] = -C.v[1]
            C.F[1] = 0

        if C.x[1] - C.R <= 0.0 + EPS:
            if C.v[1] < 0:
                C.v[1] = -C.v[1]
            C.F[1] = 0

    # ELASTIC COLLISION WITH THE BORDER - BALL
    if in_play:
        inside_goal = (ball.x[1] < POLE_BIG_Y and ball.x[1] > POLE_SMALL_Y)
        if ball.x[0] + ball.R >= PITCH_X_END - EPS and not inside_goal:
            if ball.v[0] > 0:
                ball.v[0] = -ball.v[0]
            ball.F[0] = 0

        if ball.x[0] - ball.R <= PITCH_X_BEGIN + EPS and not inside_goal:
            if ball.v[0] < 0:
                ball.v[0] = -ball.v[0]
            ball.F[0] = 0

        if ball.x[1] + ball.R >= PITCH_Y_END - EPS:
            if ball.v[1] > 0:
                ball.v[1] = -ball.v[1]
            ball.F[1] = 0

        if ball.x[1] - ball.R <= PITCH_Y_BEGIN + EPS:
            if ball.v[1] < 0:
                ball.v[1] = -ball.v[1]
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

                A = 2 * (a * dorel.mass + b * gigel.mass) / (dorel.mass + gigel.mass) - a
                B = 2 * (a * dorel.mass + b * gigel.mass) / (dorel.mass + gigel.mass) - b

                dorel.v += norm * (A - a)
                gigel.v += norm * (B - b)

                # do we need to handle forces here? -- maybe, subject of later discussion

    # KICKING 2
    for player in players:
        if player.kicking and modul(player.x - ball.x) - player.R - ball.R <= KICK_DISTANCE:
            norm = (ball.x - player.x) / modul(player.x - ball.x)
            ball.v += KICK_MOMENTUM / ball.mass * norm

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
