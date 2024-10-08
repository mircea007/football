let canvas_el = document.getElementById('canvas');
// fit screen to body size

const RATIO = 16/9;
let HEIGHT = 180;
let WIDTH = 320;
let need_new_canvas = true;

let ctx = canvas_el.getContext('2d');

let BACKGROUND_COL = '#90cc90';

let KICK_WIDTH = 3;
let KICK_COLOR = '#ffffff';

let PITCH_LINE_COLOR = '#eeeeee';

const NEXT_ROUND_DELAY = 3000;
const TRANSITION = 200;

let client_server_time_delta = 0; // initialy assume client and server have same clocks

window.addEventListener("resize", _ => {
  need_new_canvas = true;
});

function handle_wh_changes() {
  if( !need_new_canvas )
    return;

  canvas_el.height = HEIGHT = Math.min(document.body.clientWidth / RATIO, document.body.clientHeight);
  canvas_el.width = WIDTH = HEIGHT * RATIO;

  canvas_el.style.width = WIDTH;
  canvas_el.style.height = HEIGHT;

  ctx = canvas_el.getContext('2d'); // new context
  need_new_canvas = false;
}

handle_wh_changes();

function draw_scene( {'round_info': round_info, 'bodies': entity_list} ){
  handle_wh_changes();

  const PADDING = 0.1 * HEIGHT;
  const PITCH_X_BEGIN = PADDING;
  const PITCH_X_END = WIDTH - PADDING;

  const PITCH_Y_BEGIN = PADDING;
  const PITCH_Y_END = HEIGHT - PADDING;

  const POLE_BIG_Y = HEIGHT * 0.7;
  const POLE_SMALL_Y = HEIGHT * 0.3;

  ctx.fillStyle = BACKGROUND_COL;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.strokeStyle = PITCH_LINE_COLOR;
  ctx.lineWidth = 5;

  ctx.beginPath();
  ctx.moveTo(PITCH_X_BEGIN, POLE_SMALL_Y);
  ctx.lineTo(PITCH_X_BEGIN, PITCH_Y_BEGIN);
  ctx.lineTo(PITCH_X_END, PITCH_Y_BEGIN);
  ctx.lineTo(PITCH_X_END, POLE_SMALL_Y);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(PITCH_X_BEGIN, POLE_BIG_Y);
  ctx.lineTo(PITCH_X_BEGIN, PITCH_Y_END);
  ctx.lineTo(PITCH_X_END, PITCH_Y_END);
  ctx.lineTo(PITCH_X_END, POLE_BIG_Y);
  ctx.stroke();

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

  ctx.font = "15px Courier New, monospace";
  ctx.fillStyle = "#000000";
  ctx.fillText(
    "Score: " + round_info.score[0] + ' vs ' + round_info.score[1],
    20, 20
  );

  //if( Math.floor(+(new Date()) / 100) % 100 == 0 )
  //  console.log(round_info);

  ctx.fillText('' + round_info.in_play, WIDTH - 60, 20);

  document.body.style.backgroundColor = '';

  if( !round_info.in_play ){ // animation between rounds
    const trainsition_param = Math.min(
      1,
      (new Date() - round_info.start_play + NEXT_ROUND_DELAY) / TRANSITION,
      (round_info.start_play - new Date()) / TRANSITION,
    );

    ctx.fillText(
      Math.max(0, (round_info.start_play - (new Date())) / 1000).toFixed(1),
      WIDTH - 60, 50
    );

    ctx.fillStyle = 'rgba(0, 0, 0, ' + 0.2 * trainsition_param + ')';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    ctx.font = "60px 'Brush Scipt MT', cursive";
    ctx.fillStyle = "#ffffff";
    ctx.fillText("GOAL", WIDTH / 2, HEIGHT / 2 * trainsition_param);
    ctx.fillText(round_info.score[0] + ' vs ' + round_info.score[1], WIDTH / 2, 60 + HEIGHT / 2 * trainsition_param);

    if( round_info.last_scorer == 0 )
      document.body.style.backgroundColor = 'blue';

    if( round_info.last_scorer == 1 )
      document.body.style.backgroundColor = 'red';
  }
}

document.addEventListener('keydown', (evt) => {
  if( evt.key === 'ArrowLeft' )  socket.emit('key_upd', {'key': 'left', 'new_state': true});
  if( evt.key === 'ArrowRight' ) socket.emit('key_upd', {'key': 'right', 'new_state': true});
  if( evt.key === 'ArrowUp' )    socket.emit('key_upd', {'key': 'up', 'new_state': true});
  if( evt.key === 'ArrowDown' )  socket.emit('key_upd', {'key': 'down', 'new_state': true});
  if( evt.key === 'x' ) socket.emit('key_upd', {'key': 'x', 'new_state': true});

  if( evt.key === 'a' )  socket.emit('key_upd', {'key': 'left', 'new_state': true});
  if( evt.key === 'd' ) socket.emit('key_upd', {'key': 'right', 'new_state': true});
  if( evt.key === 'w' )    socket.emit('key_upd', {'key': 'up', 'new_state': true});
  if( evt.key === 's' )  socket.emit('key_upd', {'key': 'down', 'new_state': true});
  if( evt.code === 'Space' ) socket.emit('key_upd', {'key': 'x', 'new_state': true});
});

document.addEventListener('keyup', (evt) => {
  if( evt.key === 'ArrowLeft' )  socket.emit('key_upd', {'key': 'left', 'new_state': false});
  if( evt.key === 'ArrowRight' ) socket.emit('key_upd', {'key': 'right', 'new_state': false});
  if( evt.key === 'ArrowUp' )    socket.emit('key_upd', {'key': 'up', 'new_state': false});
  if( evt.key === 'ArrowDown' )  socket.emit('key_upd', {'key': 'down', 'new_state': false});
  if( evt.key === 'x' ) socket.emit('key_upd', {'key': 'x', 'new_state': false});

  if( evt.key === 'a' )  socket.emit('key_upd', {'key': 'left', 'new_state': false});
  if( evt.key === 'd' ) socket.emit('key_upd', {'key': 'right', 'new_state': false});
  if( evt.key === 'w' )    socket.emit('key_upd', {'key': 'up', 'new_state': false});
  if( evt.key === 's' )  socket.emit('key_upd', {'key': 'down', 'new_state': false});
  if( evt.code === 'Space' ) socket.emit('key_upd', {'key': 'x', 'new_state': false});
});


let socket = io();

let game_state = {
  'round_info': {
      'score': [0, 0],
      'in_play': false,
      'start_play': +(new Date()) + 10 * 1000
  },
  'bodies': []
};

socket.on('connect', () => {console.log('connected');});
socket.on('disconnect', () => {console.log('connected');});
socket.on('time_sync', ({'server_time': server_time}) => {
  client_server_time_delta = (new Date()) - server_time;
})

socket.on('gamestate', (new_state) => {
  new_state.round_info.start_play += client_server_time_delta;
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
