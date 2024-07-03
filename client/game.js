let canvas_el = document.getElementById('canvas');
let ctx = canvas_el.getContext('2d');

let WIDTH = canvas_el.getAttribute('width');
let HEIGHT = canvas_el.getAttribute('height');

let BACKGROUND_COL = '#0044aa';

let BALL_RAD = 15;
let BALL_COL = '#ffffff';

let PLAYER_RAD = 30;
let PLAYER_COL = '#ff0000';
let KICK_WIDTH = 3;
let KICK_COLOR = '#ffffff';

ctx.moveTo(0, 0);
ctx.lineTo(WIDTH, HEIGHT);
ctx.stroke();

function draw_scene( {ballx, bally, playerx, playery, kicking} ){
  ctx.fillStyle = BACKGROUND_COL;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = BALL_COL;
  ctx.beginPath();
  ctx.arc(ballx, bally, BALL_RAD, 0, 2 * Math.PI);
  ctx.fill();

  ctx.fillStyle = PLAYER_COL;
  ctx.beginPath();
  ctx.arc(playerx, playery, PLAYER_RAD, 0, 2 * Math.PI);
  ctx.fill();

  if( kicking ){
    ctx.lineWidth = KICK_WIDTH;
    ctx.strokeStyle = KICK_COLOR;
    ctx.stroke();
  }
}

//draw_scene( 100, 100, 200, 100 );

let left_active = false;
let right_active = false;
let up_active = false;
let down_active = false;
let x_active = false;

document.addEventListener('keydown', (evt) => {
  if( evt.key === 'ArrowLeft' ) left_active = true;
  if( evt.key === 'ArrowRight' ) right_active = true;
  if( evt.key === 'ArrowUp' ) up_active = true;
  if( evt.key === 'ArrowDown' ) down_active = true;
  if( evt.key === 'x' ) x_active = true;
});

document.addEventListener('keyup', (evt) => {
  if( evt.key === 'ArrowLeft' ) left_active = false;
  if( evt.key === 'ArrowRight' ) right_active = false;
  if( evt.key === 'ArrowUp' ) up_active = false;
  if( evt.key === 'ArrowDown' ) down_active = false;
  if( evt.key === 'x' ) x_active = false;
});

let ACC = 5e-4; // px/ms2
let COEF = 1.5e-3;
let MAX_SPEED = ACC / COEF; // px/ms

let playerx = WIDTH / 2;
let playery = HEIGHT / 2;
let speedx = 0;
let speedy = 0;

let MIN_REFRESH = 20; // ms

let done = false;
let prev_timestamp = undefined;
function step( timestamp ) {
  if( !prev_timestamp )
    prev_timestamp = timestamp - (MIN_REFRESH+1);

  let delta = timestamp - prev_timestamp;

  if( delta >= MIN_REFRESH ){
    let accx = ACC * (right_active - left_active) - COEF * speedx;
    let accy = ACC * (down_active - up_active) - COEF * speedy;

    speedx += delta * accx;
    speedy += delta * accy;

    playerx += delta * speedx;
    playery += delta * speedy;

    draw_scene({
      ballx: 100 + 20 * (1 + Math.sin(timestamp/500)),
      bally: 200,
      playerx: playerx,
      playery: playery,
      kicking: x_active
    });

    prev_timestamp = timestamp;
  }

  if( !done )
    window.requestAnimationFrame(step);
}

window.requestAnimationFrame(step);
