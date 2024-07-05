let canvas_el = document.getElementById('canvas');
// fit screen to body size

const RATIO = 16/9;
let WIDTH = document.body.clientWidth;
let HEIGHT = WIDTH / RATIO;
canvas_el.setAttribute('width', WIDTH);
canvas_el.setAttribute('height', HEIGHT);

let ctx = canvas_el.getContext('2d');

let BACKGROUND_COL = '#90cc90';

let BALL_RAD = 0.015 * HEIGHT;
//let BALL_COL = '#ffffff';

let PLAYER_RAD = 0.02 * HEIGHT;
//let PLAYER_COL = '#ff0000';
let KICK_WIDTH = 3;
let KICK_COLOR = '#ffffff';

function draw_scene( entity_list ){
  ctx.fillStyle = BACKGROUND_COL;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  entity_list.forEach( (corp) => {
    x = corp['x'] * HEIGHT;
    y = corp['y'] * HEIGHT;
    R = corp['R'] * HEIGHT;

    ctx.fillStyle = corp['color'];
    ctx.beginPath();
    ctx.arc(x, y, R, 0, 2 * Math.PI);
    ctx.fill();

    if( corp['kicking'] ){
      ctx.lineWidth = KICK_WIDTH;
      ctx.strokeStyle = KICK_COLOR;
      ctx.stroke();
    }
  });
}

document.addEventListener('keydown', (evt) => {
  if( evt.key === 'ArrowLeft' )  socket.emit('key_upd', {'key': 'left', 'new_state': true});
  if( evt.key === 'ArrowRight' ) socket.emit('key_upd', {'key': 'right', 'new_state': true});
  if( evt.key === 'ArrowUp' )    socket.emit('key_upd', {'key': 'up', 'new_state': true});
  if( evt.key === 'ArrowDown' )  socket.emit('key_upd', {'key': 'down', 'new_state': true});
  if( evt.key === 'x' ) socket.emit('key_upd', {'key': 'x', 'new_state': true});
});

document.addEventListener('keyup', (evt) => {
  if( evt.key === 'ArrowLeft' )  socket.emit('key_upd', {'key': 'left', 'new_state': false});
  if( evt.key === 'ArrowRight' ) socket.emit('key_upd', {'key': 'right', 'new_state': false});
  if( evt.key === 'ArrowUp' )    socket.emit('key_upd', {'key': 'up', 'new_state': false});
  if( evt.key === 'ArrowDown' )  socket.emit('key_upd', {'key': 'down', 'new_state': false});
  if( evt.key === 'x' ) socket.emit('key_upd', {'key': 'x', 'new_state': false});
});


let socket = io('http://localhost:8000/');

let game_state = [];

socket.on('connect', () => {console.log('connected');});
socket.on('disconnect', () => {console.log('connected');});

socket.on('gamestate', (new_state) => {
  game_state = new_state;
});

let MIN_REFRESH = 1000 / 50; // ms

let done = false;
let prev_timestamp = undefined;
function step( timestamp ) {
  if( !prev_timestamp )
    prev_timestamp = timestamp - (MIN_REFRESH+1);

  let delta = timestamp - prev_timestamp;

  if( delta >= MIN_REFRESH ){
    // barbaric method, must fix sometime:
    //socket.emit('client_wants_update', {});
    draw_scene(game_state);
    prev_timestamp = timestamp;
  }

  if( !done )
    window.requestAnimationFrame(step);
}

window.requestAnimationFrame(step);
