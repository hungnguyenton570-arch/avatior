let player = null;
let waiting = false;
let ready = false;
let timer = null;
let roundStarted = 0;
const $ = (id) => document.getElementById(id);
async function api(url, options={}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(data.error || 'Có lỗi xảy ra.');
  return data;
}
function updatePlayer() {
  $('playerInfo').textContent = player ? `Xin chào ${player.nickname}!` : 'Nhập biệt danh để bắt đầu.';
  $('score').textContent = player ? player.score : 0;
}
$('join').addEventListener('click', async () => {
  try {
    const nickname = $('nickname').value.trim();
    player = await api('/api/players', {method:'POST', body:JSON.stringify({nickname})});
    updatePlayer(); $('notice').textContent = 'Đã vào chơi! Chúc bạn vui vẻ.';
    refreshLeaderboard();
  } catch(e) {$('notice').textContent=e.message;}
});
$('start').addEventListener('click', () => {
  if (!player) {$('notice').textContent='Hãy nhập biệt danh và bấm Vào chơi trước nhé.';return;}
  clearTimeout(timer); waiting=true; ready=false; $('fly').disabled=true;
  $('status').textContent='Chờ tín hiệu... đừng nhấn vội!';
  $('plane').textContent='🛫';
  const delay=1200+Math.floor(Math.random()*2800);
  timer=setTimeout(()=>{ready=true;roundStarted=performance.now();$('plane').textContent='✈️';$('status').textContent='BAY NGAY!';$('fly').disabled=false;},delay);
});
$('fly').addEventListener('click', async () => {
  if (!player || !waiting || !ready) { $('notice').textContent='Chưa có tín hiệu! Hãy bắt đầu lượt mới.'; return; }
  const reaction=performance.now()-roundStarted; waiting=false;ready=false;$('fly').disabled=true;
  $('status').textContent=`Phản xạ: ${Math.round(reaction)} ms`;
  const points = reaction < 350 ? 10 : reaction < 650 ? 7 : reaction < 1000 ? 5 : 2;
  try { player=await api(`/api/players/${player.id}/score`,{method:'POST',body:JSON.stringify({points})}); updatePlayer(); $('notice').textContent=`+${points} điểm thành tích!`; await refreshLeaderboard(); }
  catch(e){$('notice').textContent=e.message;}
  $('plane').textContent='🛬';
});
async function refreshLeaderboard(){
  try { const rows=await api('/api/leaderboard'); $('leaderboard').innerHTML=''; if(!rows.length){$('leaderboard').textContent='Chưa có người chơi.';return;}
    rows.forEach((row,i)=>{const div=document.createElement('div');div.className='leader';const name=document.createElement('span');name.textContent=`${i+1}. ${row.nickname}`;const score=document.createElement('strong');score.textContent=`${row.score} điểm`;div.append(name,score);$('leaderboard').append(div);});
  } catch(e){$('leaderboard').textContent='Không tải được bảng thành tích.';}
}
$('refresh').addEventListener('click',refreshLeaderboard);
updatePlayer();refreshLeaderboard();
