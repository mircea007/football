canvas_el = document.getElementById('canvas');
// fit screen to body size

const RATIO = 16/9;
HEIGHT = 180;
WIDTH = 320;
need_new_canvas = true;

ctx = canvas_el.getContext('2d');

BACKGROUND_COL = '#90cc90';
DARK_BACKGROUND_COL = '#85c085'

KICK_WIDTH = 3;
KICK_COLOR = '#ffffff';

PITCH_LINE_COLOR = '#eeeeee';

PADDING = 0.1 * HEIGHT;
PITCH_X_BEGIN = PADDING;
PITCH_X_END = WIDTH - PADDING;

PITCH_Y_BEGIN = PADDING;
PITCH_Y_END = HEIGHT - PADDING;

POLE_BIG_Y = HEIGHT * 0.65;
POLE_SMALL_Y = HEIGHT * 0.35;

LEN_CAREU = HEIGHT * 0.2;
PADDING_CAREU = HEIGHT * 0.1;

CENTER_RADIUS = HEIGHT * 0.075;

const BANDS = 12;

const NEXT_ROUND_DELAY = 3000;
const TRANSITION = 200;

client_server_time_delta = 0; // initialy assume client and server have same clocks

window.addEventListener("resize", _ => {
  need_new_canvas = true;
});

function handle_wh_changes() {
  if( !need_new_canvas )
    return;

  const height = window.innerHeight;
  const width = window.innerWidth;

  canvas_el.height = HEIGHT = Math.min(width / RATIO, height);
  canvas_el.width = WIDTH = HEIGHT * RATIO;

  canvas_el.style.width = WIDTH;
  canvas_el.style.height = HEIGHT;

  ctx = canvas_el.getContext('2d'); // new context
  need_new_canvas = false;
}

handle_wh_changes();

FPS = 30;

function draw_players( player_list ) {
  //ctx.fillText('Press P for players', 20, HEIGHT - 20);
  const NAME_PREFIX = 12;
  const NAME_MARGIN = 10;
  const TEAM_RAD = 10;
  const BIG_MARGIN = 7;

  const Y_COMP = PITCH_Y_END + BIG_MARGIN;
  x_blue = PADDING;
  x_red = WIDTH - PADDING;
  player_list.forEach( ({'name': name, 'team': team, 'on_pitch': on_pitch}) => {
    short_name = name;
    if( name.length > NAME_PREFIX )
      short_name = name.slice(0, NAME_PREFIX - 2) + '...';

    text_width = ctx.measureText(short_name).width;
    comp_width = text_width + 3 * NAME_MARGIN + 2 * TEAM_RAD;

    x_render = (team == 0) ? x_blue : x_red - comp_width;
    if( team == 0 )
      x_blue += (comp_width + BIG_MARGIN);
    else
      x_red -= (comp_width + BIG_MARGIN);

    // background
    ctx.fillStyle = (on_pitch) ? '#75a075' : 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(x_render, Y_COMP, comp_width, 2 * NAME_MARGIN + 2 * TEAM_RAD);

    // team circle
    ctx.fillStyle = (team == 0) ? 'blue' : 'red';
    ctx.beginPath();
    ctx.arc(x_render + NAME_MARGIN + TEAM_RAD, Y_COMP + NAME_MARGIN + TEAM_RAD, TEAM_RAD, 0, 2 * Math.PI);
    ctx.fill();

    // player name
    ctx.font = "15px Courier New, monospace";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(short_name, x_render + 2 * NAME_MARGIN + 2 * TEAM_RAD, Y_COMP + 2.5 * NAME_MARGIN);
  } );
}

function draw_bodies( entity_list ) {
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

    const nick = corp['name'];
    if( nick ){
      ctx.font = "15px Courier New, monospace";
      ctx.fillStyle = "#ffffff";
      text_info = ctx.measureText(nick);
      ctx.fillText(nick, x - text_info.width / 2, y - R - 10);
    }
  });
}

function draw_pitch() {
  ctx.fillStyle = BACKGROUND_COL;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  // dark bands on the pitch, even bands are dark, odd ones are light
  ctx.fillStyle = DARK_BACKGROUND_COL;
  for( i = 0; i < BANDS; i += 2 )
    ctx.fillRect(PITCH_X_BEGIN + (PITCH_X_END - PITCH_X_BEGIN) * i / BANDS, PITCH_Y_BEGIN, (PITCH_X_END - PITCH_X_BEGIN) / BANDS, PITCH_Y_END - PITCH_Y_BEGIN);

  ctx.strokeStyle = PITCH_LINE_COLOR;
  ctx.lineWidth = 3;

  // frame
  ctx.beginPath();
  ctx.rect(PITCH_X_BEGIN, PITCH_Y_BEGIN, PITCH_X_END - PITCH_X_BEGIN, PITCH_Y_END - PITCH_Y_BEGIN);
  ctx.stroke();

  // careu stang
  ctx.beginPath();
  ctx.rect(PITCH_X_BEGIN, POLE_SMALL_Y - PADDING_CAREU, LEN_CAREU, POLE_BIG_Y - POLE_SMALL_Y + 2 * PADDING_CAREU);
  ctx.stroke();

  // careu drept
  ctx.beginPath();
  ctx.rect(PITCH_X_END - LEN_CAREU, POLE_SMALL_Y - PADDING_CAREU, LEN_CAREU, POLE_BIG_Y - POLE_SMALL_Y + 2 * PADDING_CAREU);
  ctx.stroke();

  // cetru
  ctx.beginPath();
  ctx.moveTo(WIDTH / 2, PITCH_Y_BEGIN);
  ctx.lineTo(WIDTH / 2, PITCH_Y_END);
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(WIDTH / 2, HEIGHT / 2, CENTER_RADIUS, 0, 2 * Math.PI);
  ctx.stroke();
}

function draw_scene( {'round_info': round_info, 'bodies': entity_list, 'players': player_list} ){
  handle_wh_changes();

  PADDING = 0.1 * HEIGHT;
  PITCH_X_BEGIN = PADDING;
  PITCH_X_END = WIDTH - PADDING;

  PITCH_Y_BEGIN = PADDING;
  PITCH_Y_END = HEIGHT - PADDING;

  POLE_BIG_Y = HEIGHT * 0.65;
  POLE_SMALL_Y = HEIGHT * 0.35;

  LEN_CAREU = HEIGHT * 0.2;
  PADDING_CAREU = HEIGHT * 0.1;

  CENTER_RADIUS = HEIGHT * 0.075;

  draw_pitch();

  document.body.style.backgroundColor = '';

  if( !round_info.in_play ){ // animation between rounds
    if( round_info.start_play ){
      ctx.font = "15px Courier New, monospace";
      ctx.fillStyle = "#ffffff";
      ctx.fillText(
        Math.max(0, (round_info.start_play - +(new Date()) / 1000)).toFixed(1),
        WIDTH - 60, 50
      );
    }

    //ctx.fillStyle = 'rgba(0, 0, 0, ' + 0.2 * trainsition_param + ')';
    //ctx.fillRect(0, 0, WIDTH, HEIGHT);

    //const FONT_HEIGHT = 60;
    //ctx.font = "60px 'Brush Scipt MT', cursive";
    const FONT_HEIGHT = 80;
    ctx.font = "80px Courier New, monospace";

    ctx.fillStyle = "#ffffff";
    if( round_info.msg ){
      lines = round_info.msg.split(/\n/);
      nlines = lines.length;

      if( nlines >= 1 )
        ctx.fillText(lines[0], WIDTH / 2 - ctx.measureText(lines[0]).width / 2, PADDING / 2 + FONT_HEIGHT / 2);
      if( nlines >= 2 )
        ctx.fillText(lines[1], WIDTH / 2 - ctx.measureText(lines[1]).width / 2, HEIGHT - PADDING / 2 + FONT_HEIGHT / 2);
    }

    if( round_info.last_scorer == 0 )
      document.body.style.backgroundColor = 'blue';

    if( round_info.last_scorer == 1 )
      document.body.style.backgroundColor = 'red';
  }

  //if( Math.floor(+(new Date()) / 100) % 100 == 0 )
  //  console.log(round_info);

  ctx.font = "15px Courier New, monospace";
  ctx.fillStyle = "#ffffff";
  ctx.fillText(
    "Score: " + round_info.score[0] + ' vs ' + round_info.score[1],
    20, 20
  );

  ctx.fillText('' + round_info.in_play, WIDTH - 60, 20);
  ctx.fillText('FPS = ' + FPS.toFixed(1), 20, 40);

  draw_players( player_list );
  draw_bodies( entity_list );
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


socket = io();

game_state = {
  'round_info': {
      'score': [0, 0],
      'in_play': false,
      'start_play': +(new Date()) + 10 * 1000
  },
  'bodies': [],
  'players': []
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

form = document.getElementById('join');
name_input = document.getElementById('name');
team_input = document.getElementById('team');
spectate_input = document.getElementById('spectate');
lobby_button = document.getElementById('lobby');

spectate_input.addEventListener('click', (evt) => {
  form.classList.add("form_acc");
});

lobby_button.addEventListener('click', (evt) => {
  socket.emit('move_to_lobby');
  form.classList.remove('form_acc');
  form.classList.remove('form_deny');
});

form.addEventListener('submit', (evt) => {
  socket.emit('request_join', {
    'name': name_input.value,
    'team': team_input.value
  });

  evt.preventDefault();
});

socket.on('request_accept', (evt) => {
  form.classList.add("form_acc");
});

socket.on('request_deny', (evt) => {
  form.classList.add("form_deny");
});

MIN_REFRESH = 1000 / 50; // ms

done = false;
prev_timestamp = undefined;
function step( timestamp ) {
  if( !prev_timestamp )
    prev_timestamp = timestamp - (MIN_REFRESH+1);

  delta = timestamp - prev_timestamp;

  if( delta >= MIN_REFRESH ){
    FPS = 1000 / delta;
    // barbaric method, must fix sometime:
    //socket.emit('client_wants_update', {});
    draw_scene(game_state);
    prev_timestamp = timestamp;
  }

  if( !done )
    window.requestAnimationFrame(step);
}

window.requestAnimationFrame(step);
