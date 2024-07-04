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
    def __init__(self, mass: float, radius: float, poz): # poz este vector 2D
        self.mass = mass
        self.R = radius
        self.x = poz
        self.v = np.zeros(2) # obiectele sunt initial in repaus
        self.F = np.zeros(2) # forta externa

ball   = Body(4.0,  0.015, np.array([WIDTH / 2, HEIGHT / 2]))
player = Body(10.0, 0.02, np.array([0.8 * WIDTH, HEIGHT / 2]))

KICK_DISTANCE = 6e-3
KICK_MOMENTUM = 10

keystates = {
    'right': False,
    'left': False,
    'up': False,
    'down': False,
    'x': False
}

def emit_gamestate():
    global ball
    global player
    global keystates

    sio.emit('gamestate', {
        'ballx': ball.x[0],
        'bally': ball.x[1],
        'playerx': player.x[0],
        'playery': player.x[1],
        'kicking': keystates['x']
    })

@sio.event
def connect(sid, environ, auth):
    print('connect ', sid)
    emit_gamestate()

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

@sio.on('key_upd')
def key_upd(sid, data):
    global keystates
    global player

    keystates[data['key']] = bool(data['new_state'])

    emit_gamestate()

@sio.on('client_wants_update')
def client_wants_update(sid, data):
    do_physics() # i do not have a smarter way of making a game loop here
    emit_gamestate()

EPS = 1e-4

last_time = None
MIN_REFRESH = 1 / 50
def do_physics():
    global player
    global ball
    global keystates
    global last_time

    now = time.time()
    if last_time == None:
        last_time = now - MIN_REFRESH

    dt = now - last_time
    last_time = now

    if dt > 0.3:
        print('yikes')
        return

    player.mass = 15 if keystates['x'] else 10

    player.F = np.array([
        keystates['right'] - keystates['left'],
        keystates['down'] - keystates['up']
    ]) * 4.0 - 0.4 * player.mass * player.v

    ball.F = - 0.4 * ball.mass * ball.v

    # ELASTIC COLLISION WITH THE BORDER --- NOT THE CASE IN REAL BONKIO??
    for C in [player, ball]:
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
    delta = ball.x - player.x # de la player la ball
    delta_abs = np.sqrt(delta.dot(delta))
    norm = delta / delta_abs
    if delta_abs <= ball.R + player.R + EPS:
        #perp = np.array([-norm[1], norm[0]])

        a = norm.dot(player.v)
        b = norm.dot(ball.v)

        A = 2 * (a * player.mass + b * ball.mass) / (player.mass + ball.mass) - a
        B = 2 * (a * player.mass + b * ball.mass) / (player.mass + ball.mass) - b

        player.v += norm * (A - a)
        ball.v   += norm * (B - b)

        # do we need to handle forces here? -- maybe, subject of later discussion

    # KICKING
    if keystates['x'] and delta_abs - player.R - ball.R + EPS <= KICK_DISTANCE:
        ball.v += KICK_MOMENTUM / ball.mass * norm


    player.v += (player.F / player.mass) * dt
    player.x += player.v * dt # maybe +1/2dt^2 * F/m

    ball.v += (ball.F / ball.mass) * dt
    ball.x += ball.v * dt # maybe +1/2dt^2 * F/m
