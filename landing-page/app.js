/* ============================================================
   DADOS — protótipo embute um exemplo. Para usar dados reais,
   troque a const DATA por:  const DATA = await (await fetch('data.json')).json();
   A estrutura é idêntica a data.sample.json (modelo de dados oficial).
   ============================================================ */
const METHOD = "Pontos atuais comparados ao máximo ainda alcançável (jogos por disputar + classificação final + categorias). Quem não consegue mais alcançar o líder é marcado como eliminado. Sem simulação de probabilidade — só a matemática dos pontos.";

// Categorias extras (labels/pontos = espelho do motor; usado como fallback sem data.json)
const EXTRAS_DEF = [
  {key:"artilheiro_nome",      label:"⚽ Artilheiro — nome",            points:8},
  {key:"artilheiro_equipe",    label:"👕 Artilheiro — equipe",          points:4},
  {key:"artilheiro_gols",      label:"🔢 Artilheiro — nº de gols",      points:3},
  {key:"mais_goleadora",       label:"🎯 Equipe mais goleadora",        points:5},
  {key:"menos_vazada",         label:"🧤 Equipe menos vazada",          points:5},
  {key:"mais_gols_jogo",       label:"🔥 Maior nº de gols em um jogo",  points:5},
  {key:"empates_1f",           label:"🤝 Nº de empates na 1ª fase",     points:5},
  {key:"jogos_penaltis",       label:"🥅 Jogos decididos nos pênaltis", points:5},
  {key:"equipe_1o_expulso",    label:"🟥 Equipe do 1º expulso",         points:5},
  {key:"equipe_1o_gol_contra", label:"😅 Equipe do 1º gol contra",      points:5},
  {key:"azarao",               label:"🦓 Azarão da Copa",               points:5}
];

// ---------- ESTADO 1: PRÉ-COPA (fallback embutido; sobrescrito por data.json se existir) ----------
let PRECOPA = {
  meta:{ pool_name:"Bolão Miha 2026", timezone:"America/Sao_Paulo", is_placeholder:true, bet_value:60,
    last_data_update:"2026-06-10T21:40:00-03:00", last_source_check:"2026-06-10T21:40:00-03:00",
    rule_version:"v2.1", freshness:"ok" },
  latest_result:null,
  participants:[
    {alias:"Crepaldi", score:0, rank:1, previous_rank:1, rank_change:0, last_match_points:0, p_win:0.18, p_top3:0.41, max_possible:612, points_available:612, eliminated:false, paid:true},
    {alias:"PaulinhIA",score:0, rank:2, previous_rank:3, rank_change:1, last_match_points:0, p_win:0.16, p_top3:0.39, max_possible:612, points_available:612, eliminated:false, paid:true},
    {alias:"Mihalik",  score:0, rank:3, previous_rank:2, rank_change:-1,last_match_points:0, p_win:0.15, p_top3:0.37, max_possible:612, points_available:612, eliminated:false, paid:true},
    {alias:"Jogador D",score:0, rank:4, previous_rank:4, rank_change:0, last_match_points:0, p_win:0.12, p_top3:0.30, max_possible:612, points_available:612, eliminated:false, paid:true},
    {alias:"Jogador E",score:0, rank:5, previous_rank:5, rank_change:0, last_match_points:0, p_win:0.10, p_top3:0.26, max_possible:612, points_available:612, eliminated:false, paid:false},
    {alias:"Jogador F",score:0, rank:6, previous_rank:6, rank_change:0, last_match_points:0, p_win:0.08, p_top3:0.21, max_possible:612, points_available:612, eliminated:false, paid:true}
  ],
  matches:[
    {group:"A", home_team:"México", away_team:"África do Sul", venue:"Estádio Azteca", kickoff_sao_paulo:"2026-06-11T16:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:true},
    {group:"B", home_team:"Canadá", away_team:"Bósnia", venue:"BC Place", kickoff_sao_paulo:"2026-06-12T16:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:false, is_special:true},
    {group:"D", home_team:"EUA", away_team:"Paraguai", venue:"SoFi Stadium", kickoff_sao_paulo:"2026-06-12T22:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:false},
    {group:"C", home_team:"Brasil", away_team:"Marrocos", venue:"MetLife Stadium", kickoff_sao_paulo:"2026-06-13T19:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:true}
  ],
  movement:{ biggest_jump:null, biggest_drop:null, longest_first:"— (após o 1º jogo)",
    pain_of_round:"Ninguém sofreu ainda. A bola nem rolou. Aproveitem a paz — ela é curta." },
  stats:{ best_exact:null, optimistic:null, cursed:null, elimination:"ninguém eliminado", longest_first:null, fav_score:"2 × 1" },
  probability:{ method:METHOD, simulations:30000 }
};

// ---------- ESTADO 2: SIMULAÇÃO AO VIVO (1ª rodada rolando) ----------
const DEMO = {
  meta:{ pool_name:"Bolão Miha 2026", timezone:"America/Sao_Paulo", is_placeholder:true, bet_value:60,
    last_data_update:"2026-06-13T21:55:00-03:00", last_source_check:"2026-06-13T21:50:00-03:00",
    rule_version:"v2.1", freshness:"ok" },
  latest_result:{ home_team:"Brasil", away_team:"Marrocos", home_score:3, away_score:0,
    note:"Brasil amassou. Quem cravou 3×0 fez a festa (e ganhou bônus de 3 gols)." },
  participants:[
    {alias:"Crepaldi", score:17, rank:1, previous_rank:3, rank_change:2,  last_match_points:6, p_win:0.29, p_top3:0.58, max_possible:601, points_available:584, eliminated:false, paid:true},
    {alias:"PaulinhIA",score:14, rank:2, previous_rank:1, rank_change:-1, last_match_points:3, p_win:0.23, p_top3:0.51, max_possible:598, points_available:584, eliminated:false, paid:true},
    {alias:"Mihalik",  score:12, rank:3, previous_rank:4, rank_change:1,  last_match_points:5, p_win:0.19, p_top3:0.46, max_possible:596, points_available:584, eliminated:false, paid:true},
    {alias:"Jogador D",score:11, rank:4, previous_rank:6, rank_change:2,  last_match_points:8, p_win:0.14, p_top3:0.39, max_possible:595, points_available:584, eliminated:false, paid:true},
    {alias:"Jogador E",score:7,  rank:5, previous_rank:2, rank_change:-3, last_match_points:0, p_win:0.09, p_top3:0.28, max_possible:591, points_available:584, eliminated:false, paid:false},
    {alias:"Jogador F",score:4,  rank:6, previous_rank:5, rank_change:-1, last_match_points:0, p_win:0.06, p_top3:0.20, max_possible:588, points_available:584, eliminated:false, paid:true}
  ],
  matches:[
    {group:"A", home_team:"México", away_team:"África do Sul", venue:"Estádio Azteca", kickoff_sao_paulo:"2026-06-11T16:00:00-03:00", status:"finished", home_score:2, away_score:1, verified:true},
    {group:"B", home_team:"Canadá", away_team:"Bósnia", venue:"BC Place", kickoff_sao_paulo:"2026-06-12T16:00:00-03:00", status:"finished", home_score:1, away_score:1, verified:true, is_special:true},
    {group:"D", home_team:"EUA", away_team:"Paraguai", venue:"SoFi Stadium", kickoff_sao_paulo:"2026-06-12T22:00:00-03:00", status:"finished", home_score:0, away_score:1, verified:true},
    {group:"C", home_team:"Brasil", away_team:"Marrocos", venue:"MetLife Stadium", kickoff_sao_paulo:"2026-06-13T19:00:00-03:00", status:"finished", home_score:3, away_score:0, verified:true},
    {group:"H", home_team:"Espanha", away_team:"Arábia Saudita", venue:"Mercedes-Benz Stadium", kickoff_sao_paulo:"2026-06-15T13:00:00-03:00", status:"live", home_score:1, away_score:0, verified:true},
    {group:"I", home_team:"França", away_team:"Senegal", venue:"Lumen Field", kickoff_sao_paulo:"2026-06-16T16:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:true},
    {group:"J", home_team:"Argentina", away_team:"Argélia", venue:"Hard Rock Stadium", kickoff_sao_paulo:"2026-06-16T22:00:00-03:00", status:"scheduled", home_score:null, away_score:null, verified:false}
  ],
  movement:{ biggest_jump:{alias:"Crepaldi",delta:2}, biggest_drop:{alias:"Jogador E",delta:-3},
    longest_first:"PaulinhIA — liderou do sorteio até o 1º jogo",
    pain_of_round:"A zebra do dia: EUA 0×1 Paraguai bagunçou o grupo todo. Quem apostou no favorito sentiu — faz parte." },
  stats:{
    best_exact:{alias:"Crepaldi", val:"50% (2 de 4)"},
    optimistic:{alias:"Mihalik", val:"média 3,2 gols/palpite"},
    cursed:{alias:"Jogador F", val:"0 de 4 placares"},
    elimination:"ninguém eliminado (só 4 jogos)",
    longest_first:{alias:"PaulinhIA", val:"do sorteio ao 1º jogo"},
    fav_score:"2 × 1"
  },
  probability:{ method:METHOD, simulations:30000 }
};

// Gera 70 apostas para a SIMULAÇÃO (demonstra a escala real do bolão).
// Determinístico (sem Math.random) p/ ficar igual a cada carregamento.
function genDemoParticipants(){
  const seeded = [
    {alias:"Crepaldi", score:17, paid:true},
    {alias:"PaulinhIA",score:14, paid:true},
    {alias:"Mihalik",  score:12, paid:true},
    {alias:"Jogador D",score:11, paid:true},
    {alias:"Jogador E",score:7,  paid:false},
    {alias:"Jogador F",score:4,  paid:true}
  ];
  const pool = ["Tauszig","Charles","Marcondes","Terzian","Kerr","Marina","Duarte","Luengo","Kat",
    "Mitev","Flávia","Fernandão","Tia Léa","Zé do Bar","Nostradamus","Chutômetro","Palpiteiro",
    "Sortudo","Vidente","Capitão","Maestro","Profeta","Encosto","Zebra FC","Pênalti","Lanterninha"];
  let s = 7919;                                   // semente fixa
  const rnd = () => { s = (s*1103515245 + 12345) & 0x7fffffff; return s/0x7fffffff; };
  const list = seeded.map(o => ({...o}));
  for(let i = list.length; i < 70; i++){
    const nm = pool[i % pool.length] + " " + (Math.floor(i/pool.length) + 1);
    const score = Math.max(0, Math.round(11 - (i-6)*0.12 + (rnd()*5 - 2.5)));
    list.push({ alias:nm, score, paid: rnd() > 0.45 });   // ~55% pagaram
  }
  list.sort((a,b) => b.score - a.score || a.alias.localeCompare(b.alias));
  const n = list.length;
  const exps = list.map(p => Math.exp(p.score/6));
  const sum  = exps.reduce((a,b) => a+b, 0);
  list.forEach((p,i) => {
    p.rank = i + 1;
    const drift = Math.round(rnd()*6 - 3);
    p.previous_rank = Math.min(n, Math.max(1, p.rank + drift));
    p.rank_change = p.previous_rank - p.rank;
    p.last_match_points = Math.max(0, Math.round(rnd()*8));
    p.max_possible = 580 + Math.round(rnd()*30);
    p.points_available = 555 + Math.round(rnd()*45);
    p.eliminated = false;
    p.phase1_points = p.score;          // na simulação, todos os pontos são da 1ª fase
  });
  return list;
}

// Reconstrói a SIMULAÇÃO em escala 70 e recalcula movimentação/estatísticas (auto-consistente).
(function buildDemoScale(){
  const g = genDemoParticipants();
  DEMO.participants = g;
  const jump = g.reduce((a,b) => b.rank_change > a.rank_change ? b : a);
  const drop = g.reduce((a,b) => b.rank_change < a.rank_change ? b : a);
  const last = g[g.length-1];
  DEMO.movement.biggest_jump = {alias:jump.alias, delta:jump.rank_change};
  DEMO.movement.biggest_drop = {alias:drop.alias, delta:drop.rank_change};
  DEMO.movement.longest_first = `${g[0].alias} — na ponta desde o 1º jogo`;
  DEMO.movement.pain_of_round = `${drop.alias} despencou ${Math.abs(drop.rank_change)} posições numa rodada só. Em ${g.length} apostas, dá pra cair MUITO.`;
  DEMO.stats.best_exact   = {alias:g[0].alias, val:"50% (2 de 4)"};
  DEMO.stats.optimistic   = {alias:g[3].alias, val:"média 3,2 gols/palpite"};
  DEMO.stats.cursed       = {alias:last.alias, val:"0 de 4 placares"};
  DEMO.stats.longest_first = {alias:g[0].alias, val:"do 1º jogo até agora"};
  // exemplo de categoria já definida (mostra o card verde + acertadores)
  DEMO.extras_summary = EXTRAS_DEF.map(d => ({...d, real:null, winners:[]}));
  DEMO.extras_summary[8] = {...EXTRAS_DEF[8], real:"Catar", winners:[g[0].alias, g[5].alias, g[11].alias]};
})();

let DATA = PRECOPA;

// ---------- HALL DA FAMA: pódios das edições anteriores (dados reais) ----------
const HISTORY = [
  {year:2022, host:"Catar",         flag:"🇶🇦", podium:["Alexandre Tauszig","Charles Miller","Guilherme Marcondes"]},
  {year:2018, host:"Rússia",        flag:"🇷🇺", podium:["Fabio Terzian","Pedro Marcondes","Ricardo Kerr"]},
  {year:2014, host:"Brasil",        flag:"🇧🇷", podium:["Paulo Crepaldi","Ricardo Mihalik","Fernando Mihalik"]},
  {year:2010, host:"África do Sul", flag:"🇿🇦", podium:["Marina Mihalik","Rodrigo Duarte","Luis Luengo"]},
  {year:2006, host:"Alemanha",      flag:"🇩🇪", podium:["Kat Lencina","Pedro Mitev","Flávia Mihalik"]}
];

const TAGLINES = [
  "Matematicamente vivo, emocionalmente questionável.",
  "Líder por enquanto. Não mande imprimir a faixa.",
  "Em último, mas primeiro no clima.",
  "Sendo carregado por um único placar exato.",
  "A planilha diz que há esperança. O futebol diz que não.",
  "Apostou no zebrão e agora reza pelo zebrão.",
  "Confiante como quem colocou 3×0 e tomou de 0×1.",
  "O grupo da morte aqui é o do bolão.",
  "Café-com-leite com sonho de Lanterna de Ouro.",
  "Cada empate dói um pouquinho na alma."
];

// Bandeiras (emoji) das 48 seleções da Copa 2026
const FLAGS = {
  "México":"🇲🇽","África do Sul":"🇿🇦","Canadá":"🇨🇦","Bósnia":"🇧🇦","Brasil":"🇧🇷","Marrocos":"🇲🇦",
  "Haiti":"🇭🇹","Escócia":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","EUA":"🇺🇸","Paraguai":"🇵🇾","Austrália":"🇦🇺","Turquia":"🇹🇷",
  "Alemanha":"🇩🇪","Curaçao":"🇨🇼","Costa do Marfim":"🇨🇮","Equador":"🇪🇨","Holanda":"🇳🇱","Japão":"🇯🇵",
  "Suécia":"🇸🇪","Tunísia":"🇹🇳","Bélgica":"🇧🇪","Egito":"🇪🇬","Irã":"🇮🇷","Nova Zelândia":"🇳🇿",
  "Espanha":"🇪🇸","Cabo Verde":"🇨🇻","Arábia Saudita":"🇸🇦","Uruguai":"🇺🇾","França":"🇫🇷","Senegal":"🇸🇳",
  "Iraque":"🇮🇶","Noruega":"🇳🇴","Argentina":"🇦🇷","Argélia":"🇩🇿","Áustria":"🇦🇹","Jordânia":"🇯🇴",
  "Portugal":"🇵🇹","RD Congo":"🇨🇩","Uzbequistão":"🇺🇿","Colômbia":"🇨🇴","Inglaterra":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Gana":"🇬🇭",
  "Croácia":"🇭🇷","Panamá":"🇵🇦","Catar":"🇶🇦","Suíça":"🇨🇭","Coreia do Sul":"🇰🇷","Rep Tcheca":"🇨🇿"
};
// Bandeiras de sub-nações (Escócia/Inglaterra/Gales) quebram em Windows → usa selo de 3 letras
const SUBDIV = { "Escócia":"SCO", "Inglaterra":"ENG", "País de Gales":"WAL", "Irlanda do Norte":"NIR" };
const fEmoji = t => SUBDIV[t] ? `<span class="fmono">${SUBDIV[t]}</span>` : (FLAGS[t] || '');
const flag  = t => { const f = fEmoji(t); return f ? f+' ' : ''; };   // prefixo (antes do nome)
const flagA = t => { const f = fEmoji(t); return f ? ' '+f : ''; };   // sufixo (depois do nome)

const fmtDateTime = iso => {
  const d = new Date(iso);
  return d.toLocaleString('pt-BR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'America/Sao_Paulo'}).replace(',','');
};
const arrow = c => c>0?`<span class="pill up">▲ ${c}</span>` : c<0?`<span class="pill down">▼ ${Math.abs(c)}</span>` : `<span class="pill flat">— 0</span>`;

// EN→PT p/ casar os nomes da ESPN (ao vivo no navegador) com os jogos do data.json
const EN_TO_PT = {
  "mexico":"México","south africa":"África do Sul","south korea":"Coreia do Sul","korea republic":"Coreia do Sul",
  "czechia":"Rep Tcheca","czech republic":"Rep Tcheca","canada":"Canadá","bosnia and herzegovina":"Bósnia",
  "bosnia-herzegovina":"Bósnia","bosnia":"Bósnia","qatar":"Catar","switzerland":"Suíça","brazil":"Brasil",
  "morocco":"Marrocos","haiti":"Haiti","scotland":"Escócia","united states":"EUA","usa":"EUA","paraguay":"Paraguai",
  "australia":"Austrália","türkiye":"Turquia","turkey":"Turquia","germany":"Alemanha","curaçao":"Curaçao","curacao":"Curaçao",
  "ivory coast":"Costa do Marfim","côte d'ivoire":"Costa do Marfim","cote d'ivoire":"Costa do Marfim","ecuador":"Equador",
  "netherlands":"Holanda","japan":"Japão","sweden":"Suécia","tunisia":"Tunísia","belgium":"Bélgica","egypt":"Egito",
  "iran":"Irã","ir iran":"Irã","new zealand":"Nova Zelândia","spain":"Espanha","cape verde":"Cabo Verde","cabo verde":"Cabo Verde",
  "saudi arabia":"Arábia Saudita","uruguay":"Uruguai","france":"França","senegal":"Senegal","iraq":"Iraque","norway":"Noruega",
  "argentina":"Argentina","algeria":"Argélia","austria":"Áustria","jordan":"Jordânia","portugal":"Portugal","dr congo":"RD Congo",
  "congo dr":"RD Congo","uzbekistan":"Uzbequistão","colombia":"Colômbia","england":"Inglaterra","ghana":"Gana",
  "croatia":"Croácia","panama":"Panamá"
};

// ===== AO VIVO DE VERDADE: o navegador busca a ESPN direto (oficial, tempo real) =====
// É o PRIMÁRIO p/ exibir placar ao vivo. Se a ESPN falhar, fica o dado do robô (BACKUP),
// sem erro. NUNCA mexe em pontos/classificação — só atualiza a EXIBIÇÃO de jogos não
// encerrados. O robô (pinger) segue como fonte oficial da pontuação.
let liveTimer=null;
async function liveOverlay(){
  let evs;
  try{
    const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard',{cache:'no-store'});
    if(!r.ok) return;
    evs=(await r.json()).events||[];
  }catch(e){ return; }   // ESPN indisponível → mantém o dado do robô, sem quebrar nada
  if(!Array.isArray(DATA.matches)) return;
  const key=(x,y)=>[x,y].sort().join('|');
  const idx={}; DATA.matches.forEach(m=>{ idx[key(m.home_team,m.away_team)]=m; });
  const pt=c=>EN_TO_PT[(((c.team||{}).displayName)||'').trim().toLowerCase()];
  let touched=false;
  evs.forEach(e=>{
    const comp=(e.competitions||[])[0]; if(!comp) return;
    const cs=comp.competitors||[]; if(cs.length!==2) return;
    const t=(e.status||{}).type||{};
    if(t.state!=='in') return;                       // só jogos em andamento
    const a=pt(cs[0]), b=pt(cs[1]); if(!a||!b) return;
    const m=idx[key(a,b)]; if(!m || m.status==='finished') return;  // encerrado = robô manda (tem pontos)
    const by={}; cs.forEach(c=>{ by[pt(c)]=parseInt(c.score); });
    const hs=by[m.home_team], as=by[m.away_team];
    if(Number.isFinite(hs) && Number.isFinite(as)){
      if(m.status!=='live'||m.home_score!==hs||m.away_score!==as||m.minute!==(e.status||{}).displayClock){
        m.status='live'; m.home_score=hs; m.away_score=as;
        m.minute=(e.status||{}).displayClock||t.shortDetail||''; touched=true;
      }
    }
  });
  if(touched){
    renderLiveStrip(); renderCurrentGameStats();
    const tab=document.querySelector('#matchTabs .tab.active')?.dataset.f||'scheduled';
    renderMatches(tab);
  }
}
function startLivePolling(){ if(liveTimer) clearInterval(liveTimer); liveOverlay(); liveTimer=setInterval(liveOverlay, 45000); }

// ===== Palpites do jogo de agora (estatísticas do jogo atual/ao vivo) =====
// Olha TODAS as apostas para o jogo que está rolando (ou o próximo) e mostra placar
// mais escolhido, mais ousado e a aposta solitária — só QUANTIDADES, sem nomes.
function currentGameMatch(){
  const ms=DATA.matches||[];
  const live=ms.filter(m=>m.status==='live')
    .sort((a,b)=>new Date(a.kickoff_sao_paulo||0)-new Date(b.kickoff_sao_paulo||0));
  if(live.length) return {m:live[0], live:true, more:live.length-1};
  const nowMs=Date.now();
  const next=ms.filter(m=>m.status==='scheduled'&&m.kickoff_sao_paulo&&new Date(m.kickoff_sao_paulo).getTime()>nowMs-2.5*3600e3)
    .sort((a,b)=>new Date(a.kickoff_sao_paulo)-new Date(b.kickoff_sao_paulo))[0];
  return next?{m:next, live:false, more:0}:null;
}
function renderCurrentGameStats(){
  const box=document.getElementById('cgStats'); if(!box) return;
  const cur=currentGameMatch();
  if(!cur){ box.hidden=true; box.innerHTML=''; return; }
  const m=cur.m;
  const sum=k=>{ const [h,a]=k.split('×').map(Number); return h+a; };
  const preds=[];
  (DATA.participants||[]).forEach(p=>{
    const g=p.picks&&p.picks.groups&&p.picks.groups[m.match_id];
    if(g&&g[0]!=null&&g[1]!=null) preds.push(g[0]+'×'+g[1]);
  });
  box.hidden=false;
  const moreTag = cur.more>0?` <span class="cg-more">+${cur.more} ao vivo</span>`:'';
  const status = cur.live
    ? `<span class="chip chip-live live"><span class="dot"></span> ao vivo</span> <span class="cg-min">${m.minute||'em andamento'}</span>`
    : `<span class="chip chip-sched">📅 próximo</span> <span class="cg-min">${fmtDateTime(m.kickoff_sao_paulo)}</span>`;
  const score = cur.live ? `<b>${m.home_score??0}×${m.away_score??0}</b>` : '×';
  const head=`<div class="cg-head">
    <div class="cg-match">${flag(m.home_team)}${m.home_team} ${score} ${m.away_team}${flagA(m.away_team)}${moreTag}</div>
    <div class="cg-status">${status}</div></div>`;
  if(!preds.length){
    box.innerHTML=head+`<div class="cg-empty">Sem palpites de placar para este jogo (o bolão crava placar só na 1ª fase).</div>`;
    return;
  }
  const counts=new Map();
  preds.forEach(k=>counts.set(k,(counts.get(k)||0)+1));
  const ents=[...counts.entries()];
  const most   =ents.reduce((x,y)=> y[1]>x[1]?y:x);
  const boldest=ents.reduce((x,y)=> (sum(y[0])>sum(x[0])||(sum(y[0])===sum(x[0])&&y[1]>x[1]))?y:x);
  const lonely =ents.reduce((x,y)=> (y[1]<x[1]||(y[1]===x[1]&&sum(y[0])>sum(x[0])))?y:x);
  const card=(ic,lab,k,n,sub)=>`<div class="cg-card"><div class="cg-ic">${ic}</div>
    <div class="cg-cl">${lab}</div><div class="cg-sc">${k}</div>
    <div class="cg-n">${n} aposta${n!==1?'s':''}</div><div class="cg-sub">${sub}</div></div>`;
  box.innerHTML=head+`<div class="cg-grid">
    ${card('🎯','Placar mais escolhido',most[0],most[1],'o palpite da maioria')}
    ${card('🚀','Palpite mais ousado',boldest[0],boldest[1],'mais gols apostados')}
    ${card('🎲','Aposta solitária',lonely[0],lonely[1],lonely[1]===1?'só uma cravou esse':'o menos escolhido')}
  </div><div class="cg-foot">${preds.length} palpites para este jogo · só números, sem nomes — o suspense continua 🤫</div>`;
}

function render(){
  const P = [...DATA.participants].sort((a,b)=>a.rank-b.rank);
  // hero
  const leader = P[0];
  document.getElementById('leaderName').textContent = leader.alias;
  document.getElementById('leaderScore').textContent = leader.score;
  document.getElementById('leaderNote').textContent = (leader.paid === false)
    ? 'Lidera no geral — mas é café-com-leite: joga pela glória (e pela zoeira).'
    : 'Líder por enquanto. Não mande imprimir a faixa.';
  // último resultado
  const lr = DATA.latest_result;
  if(lr){
    document.getElementById('lastResult').innerHTML = `<span>${flag(lr.home_team)}${lr.home_team}</span><span class="sc">${lr.home_score} × ${lr.away_score}</span><span>${lr.away_team}${flagA(lr.away_team)}</span>`;
    document.getElementById('lastResultNote').textContent = lr.note || '';
  } else {
    document.getElementById('lastResult').innerHTML = `<span>—</span><span class="sc">vs</span><span>—</span>`;
    document.getElementById('lastResultNote').textContent = 'A bola ainda não rolou. Calma.';
  }
  // next match — só jogos FUTUROS (tolerância de 2h30 p/ jogo em andamento)
  const nowMs = Date.now();
  const next = DATA.matches
    .filter(m=>m.status==='scheduled' && m.kickoff_sao_paulo && (new Date(m.kickoff_sao_paulo).getTime() > nowMs - 2.5*3600e3))
    .sort((a,b)=>new Date(a.kickoff_sao_paulo)-new Date(b.kickoff_sao_paulo))[0];
  if(next){
    document.getElementById('nextMatch').innerHTML = `<span>${flag(next.home_team)}${next.home_team}</span><span class="sc">×</span><span>${next.away_team}${flagA(next.away_team)}</span>`;
    document.getElementById('nextWhen').textContent = `${fmtDateTime(next.kickoff_sao_paulo)}${next.venue?' · '+next.venue:''}`;
    startCountdown(next);
  } else {
    if(cdTimer) clearInterval(cdTimer);
    document.getElementById('countdown').hidden = true;
    document.getElementById('nextMatch').innerHTML = `<span>—</span><span class="sc">×</span><span>—</span>`;
    document.getElementById('nextWhen').textContent = 'Aguardando a definição dos próximos jogos.';
  }
  // radar de JOGO ESPECIAL (verde = vale 5 pts): alerta no hero + countdown destacado
  const nextSpecial = DATA.matches
    .filter(m=>m.is_special && m.status==='scheduled' && m.kickoff_sao_paulo && (new Date(m.kickoff_sao_paulo).getTime() > nowMs - 2.5*3600e3))
    .sort((a,b)=>new Date(a.kickoff_sao_paulo)-new Date(b.kickoff_sao_paulo))[0];
  const sa = document.getElementById('specialAlert');
  if(nextSpecial){
    const isNext = next && next===nextSpecial;
    document.getElementById('saTxt').innerHTML =
      `<b>JOGO ESPECIAL${isNext?' — É O PRÓXIMO!':''}</b> · ${flag(nextSpecial.home_team)}${nextSpecial.home_team} × ${nextSpecial.away_team}${flagA(nextSpecial.away_team)} · ${fmtDateTime(nextSpecial.kickoff_sao_paulo)} — acertar o vencedor vale <b>5 pts</b> (em vez de 3). Capricha no palpite!`;
    sa.hidden = false;
  } else sa.hidden = true;
  document.getElementById('countdown').classList.toggle('is-special', !!(next && next.is_special));
  // prêmio acumulado
  renderPrize();
  // leaderboard (escalável até 70+ apostas)
  renderLeaderboard();
  renderBomPalpite();
  renderExtras();
  renderMinhaAposta();
  // movement
  const mv = DATA.movement;
  document.getElementById('bigJump').textContent = mv.biggest_jump ? `${mv.biggest_jump.alias} ▲${mv.biggest_jump.delta}` : '—';
  document.getElementById('bigDrop').textContent = mv.biggest_drop ? `${mv.biggest_drop.alias} ▼${Math.abs(mv.biggest_drop.delta)}` : '—';
  // stats
  const st = DATA.stats || {};
  const stat = o => o ? `${o.alias} · ${o.val}` : '—';
  document.getElementById('s-exact').textContent = stat(st.best_exact);
  document.getElementById('s-cursed').textContent = stat(st.cursed);
  renderCurrentGameStats();
  // corrida pelo título — modelo simples: pontos atuais × máximo ainda possível
  const ranked = [...P].sort((a,b)=> b.score - a.score || (b.max_possible??0)-(a.max_possible??0));
  const TOPP = 10;
  const top = ranked.slice(0, TOPP);
  const scaleMax = Math.max(...top.map(p=>p.max_possible ?? p.score), 1);
  const others = ranked.length - top.length;
  document.getElementById('probList').innerHTML = top.map(p=>{
    const cur = p.score, mx = (p.max_possible ?? p.score);
    const curW = (cur/scaleMax*100).toFixed(1), avW = (Math.max(0,mx-cur)/scaleMax*100).toFixed(1);
    const tag = p.eliminated ? '<span class="elim-tag">eliminado</span>' : '';
    return `<div class="prob-item">
      <div class="nm">${p.alias}${tag}</div>
      <div class="bar race"><i style="width:${curW}%"></i><u style="width:${avW}%"></u></div>
      <div class="pct">${cur}<span class="pct-mx">/${mx}</span></div>
    </div>`;
  }).join('') + (others>0 ? `<div class="prob-note">+ ${others} apostas — barra cheia = pontos já feitos · parte clara = ainda em jogo.</div>` : '');
  document.getElementById('methodText').textContent = (DATA.probability && DATA.probability.method)
    || 'Pontos atuais comparados ao máximo ainda alcançável. Sem simulação de probabilidade.';
  // audit
  document.getElementById('a-update').textContent = fmtDateTime(DATA.meta.last_data_update);
  document.getElementById('a-check').textContent = fmtDateTime(DATA.meta.last_source_check);
  document.getElementById('a-rule').textContent = DATA.meta.rule_version;
  document.getElementById('f-updated').textContent = fmtDateTime(DATA.meta.last_data_update);
  renderCrossCheck();
  // jogos ao vivo entram numa faixa destacada no topo (só quando existem)
  renderLiveStrip();
  // aba padrão: 'Próximos' enquanto houver jogos por vir; senão 'Encerrados'
  const hasScheduled = DATA.matches.some(m=>m.status==='scheduled');
  const defTab = hasScheduled ? 'scheduled' : 'finished';
  document.querySelectorAll('#matchTabs .tab').forEach(t=>t.classList.toggle('active', t.dataset.f===defTab));
  renderMatches(defTab);
}

// ---- Conferência independente (2 fontes: football-data × ESPN) ----
function renderCrossCheck(){
  const el = document.getElementById('a-crosscheck');
  if(!el) return;
  const a = DATA.audit;
  if(!a){
    el.innerHTML = 'Discrepâncias em aberto: <b class="ok">nenhuma</b> · conferência de 2 fontes ativa a cada rodada.';
    return;
  }
  const when = a.checked_at ? ' · conferido ' + fmtDateTime(a.checked_at) : '';
  const pair = `${a.source_a||'ESPN'} × ${a.source_b||'football-data.org'}`;
  if(a.status === 'divergencia' && (a.discrepancies||[]).length){
    const list = a.discrepancies.map(d =>
      `<li>${d.teams}: <b>${d.primaria||d.oficial}</b> ≠ <b>${d.secundaria||d.espn}</b>${d.lock?' (correção manual ativa)':''}</li>`).join('');
    el.innerHTML = `<b style="color:#ff6b6b">⚠ Divergência entre fontes detectada</b> — em verificação pelo organizador:
      <ul style="margin:6px 0 0 16px">${list}</ul>
      <div style="margin-top:6px;color:var(--ink-faint)">${pair}${when}. O organizador foi avisado automaticamente.</div>`;
  } else if(a.status === 'fonte_indisponivel'){
    el.innerHTML = `Conferência da 2ª fonte temporariamente indisponível — placares seguem pela fonte primária (ESPN).${when}`;
  } else {
    el.innerHTML = `<b class="ok">✓ ${a.agree}/${a.compared} jogos encerrados conferidos em 2 fontes independentes</b>
      (${pair}) — nenhuma divergência.${when}`;
  }
}

// ---- Prêmio acumulado (apenas apostas pagas × valor da aposta) ----
const brl = v => v.toLocaleString('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0});
function renderPrize(){
  const all = DATA.participants || [];
  const paidN = all.filter(p=>p.paid).length;
  const bet = (DATA.meta && DATA.meta.bet_value) || 60;
  const pot = paidN * bet;
  const refund = paidN > 0 ? bet : 0;          // Lanterna de Ouro recebe a aposta de volta (sai por cima)
  const base = Math.max(0, pot - refund);      // percentuais incidem sobre o RESTANTE
  document.getElementById('prizeAmount').textContent = brl(pot);
  document.getElementById('prizeSub').textContent =
    `${paidN} aposta${paidN!==1?'s':''} paga${paidN!==1?'s':''} × ${brl(bet)} — só os “para valer” concorrem ao dinheiro.`;
  const splits = [
    {ic:'🏆', lab:'Campeão do Bolão',  pct:0.40},
    {ic:'🥈', lab:'Vice-campeão',      pct:0.25},
    {ic:'🥉', lab:'3º lugar',          pct:0.10},
    {ic:'🏅', lab:'4º lugar',          pct:0.05},
    {ic:'⚡', lab:'Bom de Palpite (fim da 1ª fase)', pct:0.20}
  ];
  document.getElementById('prizeSplit').innerHTML =
    `<div class="psplit">
      <span class="pic">🔦</span>
      <span class="plab">Lanterna de Ouro (devolução da aposta)</span>
      <span class="ppct">—</span>
      <span class="pamt">${refund ? brl(refund) : '—'}</span>
    </div>` +
    splits.map(s=>`
    <div class="psplit">
      <span class="pic">${s.ic}</span>
      <span class="plab">${s.lab}</span>
      <span class="ppct">${Math.round(s.pct*100)}%</span>
      <span class="pamt">${base ? brl(Math.round(base*s.pct)) : '—'}</span>
    </div>`).join('');
  document.getElementById('prizeFoot').innerHTML =
    `Como divide: a <b>Lanterna de Ouro</b> (último ao fim da 1ª fase) recebe a aposta de volta (${brl(refund||bet)}); os percentuais incidem sobre o <b>restante</b> (${brl(base)}). Os pontos da 1ª fase não zeram — o vencedor da fase segue elegível aos prêmios finais. Bolão de palpites entre amigos: sem odds, sem casa de apostas.`;
}

// ---- Classificação escalável (busca + filtro pagas/café + colapso) ----
let lbFilter='all', lbSearch='', lbExpanded=false;
const LB_LIMIT=7;   // mostra o Top 7 (zona de prêmio + perseguidores); o resto expande
function renderLeaderboard(){
  const all=[...DATA.participants].sort((a,b)=>a.rank-b.rank);
  const total=all.length, paidN=all.filter(p=>p.paid).length, freeN=total-paidN;
  document.getElementById('lbCount').textContent =
    `${total} aposta${total!==1?'s':''} · ${paidN} para valer 💰 · ${freeN} café-com-leite ☕`;
  // prêmio em dinheiro: só pagantes — top 4 pela ordem geral
  const prizeSet=new Set(all.filter(p=>p.paid).slice(0,4).map(p=>p.alias));
  const maxRank=total;
  let list=all;
  if(lbFilter==='paid') list=list.filter(p=>p.paid);
  else if(lbFilter==='free') list=list.filter(p=>!p.paid);
  const q=lbSearch.trim().toLowerCase();
  if(q) list=list.filter(p=>p.alias.toLowerCase().includes(q));
  const collapsed = !lbExpanded && !q && list.length>LB_LIMIT;
  const view = collapsed ? list.slice(0,LB_LIMIT) : list;
  const el=document.getElementById('lbList');
  if(!view.length){
    el.innerHTML=`<div class="lb-empty">Nenhuma aposta encontrada${lbSearch?` para “${lbSearch}”`:''}. Tente outro apelido.</div>`;
  } else {
    el.innerHTML = view.map(p=>{
      const isFirst=p.rank===1, isLast=p.rank===maxRank;
      const cls = isFirst?'first':(p.rank===2?'second':(p.rank===3?'third':(isLast?'last':'')));
      const medal = isFirst?'👑 ':(p.rank===2?'🥈 ':(p.rank===3?'🥉 ':''));
      const prize = prizeSet.has(p.alias)?'<span class="chip chip-prize">💰 prêmio</span>':'';
      const free  = p.paid?'':'<span class="chip chip-ft">☕ café-com-leite</span>';
      const hit   = q?'<span class="you-tag">é você?</span>':'';
      return `<div class="lb-row ${cls}">
        <div class="rk">${p.rank}</div>
        <div class="who">
          <div class="nm">${medal}${isLast?'🔦 ':''}${p.alias} ${arrow(p.rank_change)} ${prize}${free} ${hit}</div>
          <div class="meta">última rodada: +${p.last_match_points} pts · placares exatos: ${p.exact_scores ?? 0}</div>
        </div>
        <div class="lb-right">
          <div class="pwin"><div class="v">${p.eliminated ? '<span style="color:var(--coral)">fora</span>' : (p.max_possible ?? '—')}</div><div class="l">máx possível</div></div>
          <div class="lb-score">${p.score}</div>
        </div>
      </div>`;
    }).join('');
  }
  // estado de espera: protótipo com poucas apostas → explica a ausência das 84
  if(DATA.meta && DATA.meta.is_placeholder && total < 8 && !q && lbFilter==='all'){
    el.innerHTML += `<div class="lb-empty" style="margin-top:4px">
      📦 <b>As 84 apostas oficiais entram aqui</b> assim que a organização liberar as planilhas —
      os nomes acima são exemplos de teste. O Top 7 (com 👑🥈🥉) e o botão “Ver todas” aparecem automaticamente.
    </div>`;
  }
  const more=document.getElementById('lbMore');
  if(collapsed){ more.hidden=false; more.textContent=`Ver todas as ${list.length} apostas ▾`; }
  else if(lbExpanded && !q && list.length>LB_LIMIT){ more.hidden=false; more.textContent='Recolher ▴'; }
  else more.hidden=true;
}
// Bom de Palpite — ranking só da 1ª fase (top 5)
function renderBomPalpite(){
  const P = [...DATA.participants]
    .map(p => ({...p, ph1: p.phase1_points ?? p.score}))
    .sort((a,b) => b.ph1 - a.ph1 || b.score - a.score)
    .slice(0, 5);
  document.getElementById('bpList').innerHTML = P.map((p,i) => `
    <div class="bp-row">
      <span class="bp-rk">${i+1}</span>
      <span class="bp-nm">${i===0?'🏁 ':''}${p.alias}${p.paid?'':' <span class="chip chip-ft">☕</span>'}</span>
      <span class="bp-pts">${p.ph1} pts</span>
    </div>`).join('') || '<div class="lb-empty">Sem pontos na 1ª fase ainda.</div>';
}

// Categorias Extras — o que já aconteceu na real + quem pontuou
function renderExtras(){
  const list = DATA.extras_summary || EXTRAS_DEF.map(d => ({...d, real:null, winners:[]}));
  document.getElementById('exGrid').innerHTML = list.map(x=>{
    const done = x.real !== null && x.real !== undefined && x.real !== '';
    const status = done
      ? `<div class="ex-real">${flag(String(x.real))}${x.real}</div>
         <div class="ex-winners">${x.winners && x.winners.length
            ? `🎉 Pontuaram (+${x.points}): <b>${x.winners.join('</b>, <b>')}</b>`
            : 'Ninguém acertou esta. O futebol venceu.'}</div>`
      : (x.partial
          ? `<div class="ex-status">📡 <b style="color:var(--blue)">Parcial ao vivo:</b> ${x.partial}</div>`
          : `<div class="ex-status">⏳ Em aberto — definido ao longo da Copa</div>`);
    return `<div class="ex-card ${done?'done':''}">
      <div class="ex-top"><span class="ex-lab">${x.label}</span><span class="ex-pts">+${x.points} pts</span></div>
      ${status}
    </div>`;
  }).join('');
}

document.getElementById('lbSearch').addEventListener('input',e=>{ lbSearch=e.target.value; renderLeaderboard(); });
document.getElementById('lbFilter').addEventListener('click',e=>{
  const b=e.target.closest('.seg-btn'); if(!b)return;
  document.querySelectorAll('#lbFilter .seg-btn').forEach(t=>t.classList.remove('active'));
  b.classList.add('active'); lbFilter=b.dataset.f; lbExpanded=false; renderLeaderboard();
});
document.getElementById('lbMore').addEventListener('click',()=>{ lbExpanded=!lbExpanded; renderLeaderboard(); });

function matchCardHTML(m){
  const chip = m.status==='live'?'<span class="chip chip-live live"><span class="dot"></span> Ao vivo</span>'
    : m.status==='finished'?'<span class="chip chip-ft">Encerrado</span>'
    : '<span class="chip chip-sched">Agendado</span>';
  const sc = (m.home_score==null)?'<span class="sc">–</span>':`<span class="sc">${m.home_score}</span>`;
  const sc2= (m.away_score==null)?'<span class="sc">–</span>':`<span class="sc">${m.away_score}</span>`;
  const special = m.is_special ? '<span class="chip chip-special">⭐ Especial · 5 pts</span>' : '';
  // rodapé: ao vivo mostra o minuto (se houver); encerrado mostra conferência; agendado, horário
  let foot;
  if(m.status==='live') foot = `<span class="mlive-min">${m.minute?('🔴 '+m.minute):'🔴 em andamento'}</span><span class="verif">placar parcial</span>`;
  else if(m.status==='finished') foot = `<span>📅 ${fmtDateTime(m.kickoff_sao_paulo)}</span><span class="verif">${m.verified?'<span class="ok">✓ conferido</span>':'<span class="warn">• conferindo</span>'}</span>`;
  else foot = `<span>📅 ${fmtDateTime(m.kickoff_sao_paulo)}</span><span class="verif">a bola não rolou</span>`;
  return `<div class="mcard">
    <div class="top"><span class="grp">Grupo ${m.group}</span><span style="display:flex;gap:6px;align-items:center">${special}${chip}</span></div>
    <div class="team"><span>${flag(m.home_team)}${m.home_team}</span>${sc}</div>
    <div class="team"><span>${flag(m.away_team)}${m.away_team}</span>${sc2}</div>
    <div class="foot">${foot}</div>
  </div>`;
}

// faixa "acontecendo agora" — só aparece quando há jogo ao vivo
function renderLiveStrip(){
  const el = document.getElementById('liveStrip');
  if(!el) return;
  const live = (DATA.matches||[]).filter(m=>m.status==='live')
    .sort((a,b)=>new Date(a.kickoff_sao_paulo||0)-new Date(b.kickoff_sao_paulo||0));
  if(!live.length){ el.hidden=true; el.innerHTML=''; return; }
  el.hidden=false;
  el.innerHTML = `<div class="live-strip-head"><span class="dot" style="color:#FF6B72"></span> 🔴 Acontecendo agora</div>
    <div class="matches">${live.map(matchCardHTML).join('')}</div>`;
}

let matchExpanded=false;
const MATCH_LIMIT=9;   // mostra ~3 linhas; o resto fica atrás de "Ver todos" (anti-scroll)
function renderMatches(filter){
  const list = DATA.matches.filter(m=>m.status===filter)
    .sort((a,b)=>new Date(a.kickoff_sao_paulo||0)-new Date(b.kickoff_sao_paulo||0));
  const el = document.getElementById('matchList');
  const more = document.getElementById('matchMore');
  const empty = filter==='scheduled' ? 'Sem próximos jogos no momento.' : 'Nenhum jogo encerrado ainda.';
  if(!list.length){ el.innerHTML = `<div class="mcard" style="grid-column:1/-1;text-align:center;color:var(--ink-faint)">${empty}</div>`; if(more) more.hidden=true; return; }
  const collapsed = !matchExpanded && list.length>MATCH_LIMIT;
  const view = collapsed ? list.slice(0,MATCH_LIMIT) : list;
  el.innerHTML = view.map(matchCardHTML).join('');
  if(more){
    if(collapsed){ more.hidden=false; more.textContent=`Ver todos os ${list.length} jogos ▾`; }
    else if(matchExpanded && list.length>MATCH_LIMIT){ more.hidden=false; more.textContent='Recolher ▴'; }
    else more.hidden=true;
  }
}

// Hall da Fama (estático — independe do estado pré/demo)
function renderFame(){
  document.getElementById('fameGrid').innerHTML = HISTORY.map(e=>`
    <div class="fame-card">
      <div class="fame-top"><span class="fame-year">${e.year}</span><span class="fame-host">${e.flag} ${e.host}</span></div>
      <ul class="podium">
        <li class="p1"><span>🥇</span><b>${e.podium[0]}</b></li>
        <li><span>🥈</span><span>${e.podium[1]}</span></li>
        <li><span>🥉</span><span>${e.podium[2]}</span></li>
      </ul>
    </div>`).join('');
  // dinastia = sobrenome mais frequente nos pódios
  const fam={};
  HISTORY.forEach(e=>e.podium.forEach(n=>{const s=n.trim().split(' ').pop(); fam[s]=(fam[s]||0)+1;}));
  const top=Object.entries(fam).sort((a,b)=>b[1]-a[1])[0];
  const champs=HISTORY.map(e=>`${e.podium[0].split(' ')[0]} (${e.year})`).join(' · ');
  document.getElementById('fameHighlight').innerHTML =
    `👑 <b>Dinastia ${top[0]}</b> — ${top[1]} presenças no pódio em ${HISTORY.length} edições. A casa do “Miha” claramente sabe das coisas.<br>🏆 <b>Campeões:</b> ${champs}`;
}

// countdown ao vivo até o próximo jogo
let cdTimer=null;
function startCountdown(match){
  if(cdTimer) clearInterval(cdTimer);
  const box=document.getElementById('countdown');
  box.querySelector('.cd-lab').textContent='⏳ A bola rola em';
  const target=new Date(match.kickoff_sao_paulo).getTime();
  document.getElementById('cd-match').innerHTML = `${flag(match.home_team)}${match.home_team} × ${match.away_team}${flagA(match.away_team)}`;
  box.hidden=false;
  const tick=()=>{
    let diff=target-Date.now();
    if(diff<=0){ box.querySelector('.cd-lab').textContent='🔴 É AGORA'; clearInterval(cdTimer);
      document.getElementById('cd-d').textContent='0';document.getElementById('cd-h').textContent='0';
      document.getElementById('cd-m').textContent='0';document.getElementById('cd-s').textContent='0';return; }
    const s=Math.floor(diff/1000);
    document.getElementById('cd-d').textContent=Math.floor(s/86400);
    document.getElementById('cd-h').textContent=Math.floor(s%86400/3600);
    document.getElementById('cd-m').textContent=Math.floor(s%3600/60);
    document.getElementById('cd-s').textContent=s%60;
  };
  tick(); cdTimer=setInterval(tick,1000);
}

// ===================== MINHA APOSTA =====================
let maSelected = null, maTab = 'played';
const maNorm = s => (s||'').toString().normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().trim();

function maPickRow(e){
  const m=e.m, played=m.status==='finished';
  const exact = played && e.ph===m.home_score && e.pa===m.away_score;
  let cls='wait', txt='⏳';
  if(played){
    if(e.pts===0){cls='zero'; txt='0';}
    else if(exact){cls='exato'; txt='⭐ +'+e.pts;}
    else {cls='win'; txt='✓ +'+e.pts;}
  }
  const sp = m.is_special?' · <small style="color:#5FE08A">⭐ especial</small>':'';
  return `<div class="ma-pick">
    <div>
      <div class="teams"><small>Grupo ${m.group}${sp}</small><br>${flag(m.home_team)}${m.home_team} <b>${e.ph}×${e.pa}</b> ${m.away_team}${flagA(m.away_team)}</div>
      <div class="guess">${played?('saiu <b>'+m.home_score+'×'+m.away_score+'</b>'):'aguardando o jogo'}</div>
    </div>
    <span class="ma-pts ${cls}">${txt}</span>
  </div>`;
}

function renderMinhaAposta(){
  const card=document.getElementById('maCard');
  const all=DATA.participants||[];
  if(!maSelected || !all.find(x=>x.alias===maSelected)){ card.hidden=true; return; }
  const p=all.find(x=>x.alias===maSelected);
  const total=all.length;
  card.hidden=false;
  const initials=(p.alias.match(/[A-Za-zÀ-ÿ0-9]+/g)||['?']).slice(0,2).map(w=>w[0]).join('').toUpperCase();
  const mv = p.rank_change>0?`<span class="pill up">▲ ${p.rank_change}</span>`:(p.rank_change<0?`<span class="pill down">▼ ${Math.abs(p.rank_change)}</span>`:'');
  const paidBadge = p.paid?'':'<span class="chip chip-ft">☕ café-com-leite</span>';
  const paidTop4=[...all].filter(x=>x.paid).sort((a,b)=>a.rank-b.rank).slice(0,4).map(x=>x.alias);
  const prize=(p.paid && paidTop4.includes(p.alias))?'<span class="chip chip-prize">💰 zona de prêmio</span>':'';
  const mx=p.max_possible??p.score, cur=p.score;
  const curW=(cur/Math.max(mx,1)*100).toFixed(1), avW=(Math.max(0,mx-cur)/Math.max(mx,1)*100).toFixed(1);
  const ph1=p.phase1_points??p.score;

  let h=`<div class="ma-hero">
    <div class="ma-av">${initials}</div>
    <div class="ma-who"><div class="ma-name">${p.alias} ${mv}</div>
      <div class="ma-sub">${p.rank}º de ${total}${p.eliminated?' · <span style="color:var(--coral)">eliminado</span>':''} ${prize}${paidBadge}</div></div>
    <div class="ma-score"><b>${p.score}</b><span>pontos</span></div></div>
  <div class="ma-break">
    <div class="ma-kpi"><b>${ph1}</b><span>pts 1ª fase</span></div>
    <div class="ma-kpi"><b>${p.exact_scores??0}</b><span>placares exatos</span></div>
    <div class="ma-kpi"><b>+${p.last_match_points??0}</b><span>última rodada</span></div>
    <div class="ma-kpi"><b>${mx}</b><span>máx. possível</span></div>
  </div>
  <div class="ma-barwrap"><div class="ma-barlab"><span>corrida pelo título</span><span>${cur} / ${mx}</span></div>
    <div class="ma-bar"><i style="width:${curW}%"></i><u style="width:${avW}%"></u></div></div>`;

  const picks=p.picks;
  if(!picks){
    h+=`<div class="ma-nodata">📋 O detalhe dos palpites aparece com os dados reais — esta é a simulação de exemplo.</div>`;
  } else {
    const mm={}; (DATA.matches||[]).forEach(x=>mm[x.match_id]=x);
    const entries=Object.entries(picks.groups||{}).map(([mid,a])=>({mid,m:mm[mid],ph:a[0],pa:a[1],pts:a[2]}))
      .filter(e=>e.m).sort((a,b)=> new Date(a.m.kickoff_sao_paulo||0)-new Date(b.m.kickoff_sao_paulo||0));
    const played=entries.filter(e=>e.m.status==='finished');
    const upcoming=entries.filter(e=>e.m.status!=='finished');
    if(maTab==='played' && !played.length && upcoming.length) maTab='upcoming';
    const list=maTab==='played'?played:upcoming;
    h+=`<div class="ma-sec"><h4>⚽ Meus palpites — fase de grupos</h4>
      <div class="ma-tabs" id="maTabs">
        <button class="ma-tab ${maTab==='played'?'active':''}" data-t="played">Já jogados (${played.length})</button>
        <button class="ma-tab ${maTab==='upcoming'?'active':''}" data-t="upcoming">A jogar (${upcoming.length})</button>
      </div>${list.length?list.map(maPickRow).join(''):'<div class="ma-pend">Nada nesta aba ainda.</div>'}</div>`;

    const rf=DATA.final_result||{}, fr=picks.final||{};
    h+=`<div class="ma-sec"><h4>🏆 Minha classificação final</h4>`+
      [['champion','Campeã',15],['vice','Vice',10],['third','3º lugar',5]].map(([k,lab,pt])=>{
        const g=fr[k]||'—'; const real=rf[k];
        const mark = (real!==null&&real!==undefined&&real!=='')
          ? (maNorm(real)===maNorm(g)?`<span class="ma-ok">✓ +${pt}</span>`:'<span class="ma-pend">não veio</span>')
          : '<span class="ma-pend">a definir</span>';
        return `<div class="ma-final-row"><span><span class="pos">${lab}:</span> ${g!=='—'?flag(g):''}${g}</span>${mark}</div>`;
      }).join('')+`</div>`;

    const exVals=picks.extras||{};
    const exRows=EXTRAS_DEF.map(d=>{
      const g=exVals[d.key];
      if(g===null||g===undefined||g==='') return '';
      const fact=(DATA.extras_summary||[]).find(x=>x.key===d.key);
      const real=fact?fact.real:null;
      let mark='<span class="ma-pend">a definir</span>';
      if(real!==null&&real!==undefined&&real!=='') mark=(maNorm(String(real))===maNorm(String(g)))?`<span class="ma-ok">✓ +${d.points}</span>`:'<span class="ma-pend">não veio</span>';
      else if(fact&&fact.partial) mark='<span class="ma-pend">📡 parcial</span>';
      return `<div class="ma-final-row"><span><span class="pos">${d.label}</span><br>${g}</span>${mark}</div>`;
    }).filter(Boolean).join('');
    h+=`<div class="ma-sec"><h4>🎯 Minhas categorias extras</h4>${exRows||'<div class="ma-pend">Sem categorias preenchidas.</div>'}</div>`;
  }
  card.innerHTML=h;
}

function maSelect(alias){
  maSelected=alias; maTab='played';
  try{ localStorage.setItem('minhaAposta', alias); }catch(e){}
  const inp=document.getElementById('maInput'); inp.value=alias;
  document.getElementById('maSuggest').hidden=true;
  renderMinhaAposta();
  document.getElementById('maCard').scrollIntoView({behavior:'smooth', block:'nearest'});
}

function maRenderSuggest(q){
  const box=document.getElementById('maSuggest');
  const all=[...(DATA.participants||[])].sort((a,b)=>a.rank-b.rank);
  const nq=maNorm(q);
  const hits=(nq? all.filter(p=>maNorm(p.alias).includes(nq)) : all).slice(0,8);
  if(!q){ box.hidden=true; return; }
  box.hidden=false;
  box.innerHTML = hits.length
    ? hits.map(p=>`<div class="ma-sugg" data-a="${p.alias.replace(/"/g,'&quot;')}"><span>${p.alias}</span><span class="r">${p.rank}º</span></div>`).join('')
    : `<div class="ma-empty-s">Nenhum apelido com “${q}”. Confere a grafia (igual à planilha).</div>`;
}

// limpa a seleção: nome apagado / clique no "x" → não deixa nada parado na tela
function maClear(){
  maSelected=null;
  try{ localStorage.removeItem('minhaAposta'); }catch(e){}
  document.getElementById('maCard').hidden=true;
  document.getElementById('maSuggest').hidden=true;
}
document.getElementById('maInput').addEventListener('input',e=>{
  const v=e.target.value;
  if(!v.trim()){ maClear(); return; }                 // campo vazio → reseta tudo
  if(v!==maSelected) document.getElementById('maCard').hidden=true;  // editando → some o card antigo
  maRenderSuggest(v);
});
document.getElementById('maInput').addEventListener('search',e=>{ if(!e.target.value.trim()) maClear(); });
document.getElementById('maInput').addEventListener('focus',e=>{ if(e.target.value) maRenderSuggest(e.target.value); });
document.getElementById('maSuggest').addEventListener('click',e=>{
  const it=e.target.closest('.ma-sugg'); if(it) maSelect(it.dataset.a);
});
document.getElementById('maCard').addEventListener('click',e=>{
  const t=e.target.closest('.ma-tab'); if(!t)return;
  maTab=t.dataset.t; renderMinhaAposta();
});
document.addEventListener('click',e=>{ if(!e.target.closest('.ma-search')) document.getElementById('maSuggest').hidden=true; });

// tabs
document.getElementById('matchTabs').addEventListener('click',e=>{
  const b=e.target.closest('.tab'); if(!b)return;
  document.querySelectorAll('#matchTabs .tab').forEach(t=>t.classList.remove('active'));
  b.classList.add('active'); matchExpanded=false; renderMatches(b.dataset.f);
});
document.getElementById('matchMore').addEventListener('click',()=>{
  matchExpanded=!matchExpanded;
  renderMatches(document.querySelector('#matchTabs .tab.active')?.dataset.f||'scheduled');
});

// alternar estado de visualização (pré-copa / simulação)
document.getElementById('stateToggle').addEventListener('click',e=>{
  const b=e.target.closest('.seg-btn'); if(!b)return;
  document.querySelectorAll('#stateToggle .seg-btn').forEach(t=>t.classList.remove('active'));
  b.classList.add('active');
  DATA = b.dataset.s==='demo' ? DEMO : PRECOPA;
  // reset dos filtros da classificação ao trocar de estado
  lbFilter='all'; lbSearch=''; lbExpanded=false;
  document.getElementById('lbSearch').value='';
  document.querySelectorAll('#lbFilter .seg-btn').forEach(t=>t.classList.toggle('active', t.dataset.f==='all'));
  render();
});

// rotating tagline
let ti=0; const tEl=document.getElementById('tagline');
function rotate(){ tEl.textContent = TAGLINES[ti % TAGLINES.length]; ti++; }
rotate(); setInterval(rotate, 4200);

// boot: carrega o placar direto do GitHub (não consome deploys da Netlify);
// fallback: data.json local (deploy antigo / file:// / offline).
// Duas fontes: a cópia local (mesma origem — fresca no GitHub Pages, que o robô
// republica a cada rodada) e o raw do GitHub (fresco no Netlify congelado).
// Buscamos as duas e usamos a MAIS RECENTE (por meta.last_data_update).
const DATA_SOURCES = [
  './data.json',
  'https://raw.githubusercontent.com/paulocrepaldi81/bolao-miha-2026/main/landing-page/data.json'
];
async function boot(){
  try{
    const got = await Promise.all(DATA_SOURCES.map(async src=>{
      try{ const r=await fetch(src + '?ts=' + Date.now(), {cache:'no-store'}); if(r.ok) return await r.json(); }
      catch(e){}
      return null;
    }));
    const live = got.filter(Boolean)
      .sort((a,b)=> new Date(b.meta?.last_data_update||0) - new Date(a.meta?.last_data_update||0))[0] || null;
    if(live){
      PRECOPA = live;                                   // "Pré-Copa" passa a refletir os dados reais
      if(Array.isArray(live.history)) HISTORY.splice(0, HISTORY.length, ...live.history);
      if(live.meta && live.meta.is_placeholder === false){
        document.querySelector('.statebar')?.remove();  // some o toggle de protótipo
        document.querySelector('.demo-banner')?.remove();// some o aviso de placeholder
      }
    }
  }catch(e){ console.info('data.json indisponível — usando dados embutidos (modo protótipo).'); }
  DATA = PRECOPA;
  // restaura "Minha Aposta" salva (se o apelido ainda existir nos dados)
  try{
    const saved=localStorage.getItem('minhaAposta');
    if(saved && (DATA.participants||[]).some(p=>p.alias===saved)){
      maSelected=saved; document.getElementById('maInput').value=saved;
    }
  }catch(e){}
  renderFame();
  render();
  startLivePolling();   // ao vivo de verdade (ESPN direto) por cima do dado do robô
}
boot();
