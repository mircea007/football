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

class Body:
    def __init__(self, mass: float, radius: float, poz, color = '#ffffff', stationary = False, kicking = False): # poz este vector 2D
        self.rest_mass = mass
        self.mass = mass
        self.R = radius
        self.x = poz
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

players = []
sid2player = {}

stalpi = [
    Body(4.0,  0.015, np.array([WIDTH, HEIGHT * 0.7]), '#ff0000', True),
    Body(4.0,  0.015, np.array([WIDTH, HEIGHT * 0.3]), '#ff0000', True),
    Body(4.0,  0.015, np.array([0, HEIGHT * 0.7]), '#0000ff', True),
    Body(4.0,  0.015, np.array([0, HEIGHT * 0.3]), '#0000ff', True),
]

corpuri = [ball] + stalpi

KICK_DISTANCE = 10e-3
KICK_MOMENTUM = 1.0

keystates = {}

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
        sio.emit('gamestate', [
            {
                'x': corp.x[0],
                'y': corp.x[1],
                'R': corp.R,
                'color': corp.color,
                'kicking': corp.kicking
            } for corp in corpuri
        ])

@sio.event
def connect(sid, environ, auth):
    global keystates
    global players
    global player_locations
    global player_colors
    global sid2player
    global corpuri

    print('connect ', sid)

    player_idx = len(players)
    new_player = Body(10.0, 0.02, player_locations[player_idx], player_colors[player_idx])
    players.append(new_player)
    corpuri.append(new_player)
    sid2player[sid] = new_player
    keystates[sid] = {
        'left': False,
        'right': False,
        'up': False,
        'down': False,
        'x': False,
    }
    new_player.keystates = keystates[sid]

    emit_gamestate()

@sio.event
def disconnect(sid):
    global keystates
    global players
    #global player_locations
    #global player_colors
    global sid2player
    global corpuri

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
        ]) * 8.0 - 0.8 * player.mass * player.v

    ball.F = - 0.3 * ball.mass * ball.v

    # ELASTIC COLLISION WITH THE BORDER --- NOT THE CASE IN REAL BONKIO??
    for C in corpuri:
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

    # KICKING
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

def game_loop():
    while True:
        do_physics()
        emit_gamestate()
        time.sleep(min(BROADCAST_REFRESH, PHYSICS_REFRESH))

import eventlet
eventlet.spawn(game_loop)
