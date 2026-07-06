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
  movement:{ round_points:null, biggest_jump:null, biggest_drop:null, longest_first:"— (após o 1º jogo)",
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
  movement:{ round_points:{value:6,holders:["Crepaldi"],count:1}, biggest_jump:{value:2,holders:["Crepaldi"],count:1}, biggest_drop:{value:-3,holders:["Jogador E"],count:1},
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
  DEMO.movement.biggest_jump = {value:jump.rank_change, holders:[jump.alias], count:1};
  DEMO.movement.biggest_drop = {value:drop.rank_change, holders:[drop.alias], count:1};
  DEMO.movement.round_points = {value: Math.max(1,...g.map(p=>p.last_match_points||0)), holders:[g[0].alias], count:1};
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
  {year:2006, host:"Alemanha",      flag:"🇩🇪", podium:["Kat Lencina","Pedro Mitev","Flávia Mihalik"]},
  {year:2002, host:"Coreia/Japão",  flag:"🇰🇷🇯🇵", podium:["Rafael Liberman","Wagner Jacot","Roberto Mihalik"]}
];

const TAGLINES = [
  "Hora de derrubar a Casa Mihalik.",
  "Mata-mata é igual o 6-7: ninguém entende, mas todo mundo grita.",
  "Seu palpite tá igual o Endrick: aquecendo no banco esperando entrar.",
  "Nem o Mounjaro do Ronaldo enxuga o peso da sua tabela.",
  "No bolão da família não tem tigrinho: tem tabela, vergonha e zoeira.",
  "Assistiu pela CazéTV, gritou com o Casimiro, mas na hora do palpite gelou.",
  "Sua confiança é igual narrador na abertura: jurou que era mascote, era Labubu.",
  "O cara entrou no ônibus agora, nem tá em pé e já quer sentar na janela.",
  // referências do mata-mata 2026 (Vozinha, meme Vini Jr/Haaland) — trocar à vontade
  "O Vozinha tem 40 anos e não vaza nada. Seu palpite tem 3 dias e já afundou.",
  "Aos 40 anos o Vozinha virou sensação da Copa. Aos 3 acertos, você virou piada do grupo.",
  "Vini Jr e Haaland recriaram meme antes do jogo. Seu palpite recriou foi vexame.",
  "Ninguém segura o Vozinha no gol. Ninguém segura a zebra que virou sua tabela.",
  "Sua confiança começou igual parede do Vozinha. Seu resultado terminou igual sua torcida: vazado.",
  "JÁ ERA! Seu palpite não foi eliminado — ele pediu pra se aposentar de vergonha."
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
// Bandeiras de sub-nações (Escócia/Inglaterra) quebram como EMOJI no Windows/Noto → SVG inline,
// que renderiza igual em qualquer sistema. As demais seleções usam o emoji de bandeira normal.
const SUBDIV_SVG = {
  "Inglaterra": '<svg viewBox="0 0 30 20" width="19" height="13" style="vertical-align:-2px;border-radius:2px;box-shadow:0 0 0 1px rgba(255,255,255,.18)"><rect width="30" height="20" fill="#fff"/><rect x="12" width="6" height="20" fill="#ce1124"/><rect y="7" width="30" height="6" fill="#ce1124"/></svg>',
  "Escócia":    '<svg viewBox="0 0 30 20" width="19" height="13" style="vertical-align:-2px;border-radius:2px"><rect width="30" height="20" fill="#0065bf"/><path d="M0 0L30 20M30 0L0 20" stroke="#fff" stroke-width="4.5"/></svg>'
};
const fEmoji = t => SUBDIV_SVG[t] || FLAGS[t] || '';
const flag  = t => { const f = fEmoji(t); return f ? f+' ' : ''; };   // prefixo (antes do nome)
const flagA = t => { const f = fEmoji(t); return f ? ' '+f : ''; };   // sufixo (depois do nome)
// Escapa dados de HUMANOS (apelido, da planilha) ou de 3ª parte (minuto, da ESPN) antes de
// entrar em innerHTML — defesa contra XSS / quebra de layout.
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// nomes com empate: até N inline + "+X" que EXPANDE de verdade (clicável). Reutilizado em
// Movimentação, Números do bolão e ganhadores das Extras (antes o "+X" era só decoração).
function holdersWrap(list, N=3){
  const arr = (list||[]).map(esc);
  if(arr.length <= N) return arr.join(', ');
  const head = arr.slice(0,N).join(', '), full = arr.join(', ');
  return `<span class="who-wrap"><span class="who-head">${head} <button type="button" class="more-btn" aria-label="ver todos os ${arr.length}">+${arr.length-N}</button></span>`
       + `<span class="who-full" hidden>${full} <button type="button" class="less-btn">ver menos</button></span></span>`;
}
document.addEventListener('click', e => {
  const m = e.target.closest('.more-btn'), l = e.target.closest('.less-btn');
  const w = (m||l) && (m||l).closest('.who-wrap'); if(!w) return;
  w.querySelector('.who-head').hidden = !!m;
  w.querySelector('.who-full').hidden = !m;
});

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
// CLIENTE EVENT-DRIVEN: quando um jogo que estava AO VIVO encerra, busca o data.json oficial na
// hora e faz um "burst" (a cada 12s por ~3 min) até o robô publicar os pontos — sem esperar o
// ciclo de 30s. NÃO recalcula nada no cliente; só acelera a busca do dado oficial (acurácia intocada).
let prevLive = new Set(), burstUntil = 0, burstTimer = null;
function startBurst(){
  burstUntil = Date.now() + 180000;                 // janela de 3 min
  refreshData();                                    // pega o oficial agora
  if(!burstTimer) burstTimer = setInterval(()=>{
    if(Date.now() > burstUntil){ clearInterval(burstTimer); burstTimer = null; return; }
    refreshData();
  }, 12000);
}
// SELO DE FRESCURA CONTEXTUAL: só avisa quando há AÇÃO (jogo ao vivo ou recém-encerrado) E o
// data.json está parado há muito tempo. Assim NÃO grita de madrugada/entre jogos (quando é normal
// o dado ficar parado) — só torna VISÍVEL uma falha do robô/pinger em vez de congelar em silêncio.
function checkFreshness(){
  const el = document.getElementById('freshWarn'); if(!el) return;
  const upd = DATA.meta && DATA.meta.last_data_update;
  const ageMin = upd ? (Date.now() - new Date(upd).getTime())/60000 : 1e9;
  const liveNow = (DATA.matches||[]).some(m=>m.status==='live');
  const recentlyEnded = burstUntil > 0 && Date.now() < burstUntil + 480000;   // até ~8 min após encerrar
  if((liveNow || recentlyEnded) && ageMin > 12){
    el.textContent = `⚠️ Tem jogo agora, mas os pontos não atualizam há ${Math.round(ageMin)} min — pode ser atraso na fonte. Reconferindo…`;
    el.hidden = false;
  } else el.hidden = true;
}
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
  let touched=false; const nowLive=new Set();
  evs.forEach(e=>{
    const comp=(e.competitions||[])[0]; if(!comp) return;
    const cs=comp.competitors||[]; if(cs.length!==2) return;
    const t=(e.status||{}).type||{};
    if(t.state!=='in') return;                       // só jogos em andamento
    const a=pt(cs[0]), b=pt(cs[1]); if(!a||!b) return;
    const m=idx[key(a,b)]; if(!m || m.status==='finished') return;  // encerrado = robô manda (tem pontos)
    nowLive.add(key(a,b));
    const by={}; cs.forEach(c=>{ by[pt(c)]=parseInt(c.score,10); });
    const hs=by[m.home_team], as=by[m.away_team];
    if(Number.isFinite(hs) && Number.isFinite(as)){
      if(m.status!=='live'||m.home_score!==hs||m.away_score!==as||m.minute!==(e.status||{}).displayClock){
        m.status='live'; m.home_score=hs; m.away_score=as;
        m.minute=(e.status||{}).displayClock||t.shortDetail||''; touched=true;
      }
    }
  });
  // jogo que ESTAVA ao vivo e sumiu da lista de 'in' → encerrou → busca o oficial na hora (burst)
  const ended = [...prevLive].some(k=>!nowLive.has(k));
  prevLive = nowLive;
  if(ended) startBurst();
  if(touched){
    renderLiveStrip(); renderCurrentGameStats(); renderHeroLive();
    const tab=document.querySelector('#matchTabs .tab.active')?.dataset.f||'scheduled';
    renderMatches(tab);
  }
  checkFreshness();
}
function startLivePolling(){ if(liveTimer) clearInterval(liveTimer); liveOverlay(); liveTimer=setInterval(liveOverlay, 45000); }

// Indicador simples no hero: aparece só quando há jogo AO VIVO (sem lotar a página).
function renderHeroLive(){
  const el=document.getElementById('heroLive'); if(!el) return;
  const live=(DATA.matches||[]).filter(m=>m.status==='live');
  if(!live.length){ el.hidden=true; el.innerHTML=''; return; }
  const txt=live.map(m=>`${flag(m.home_team)}${m.home_team} <b>${m.home_score}×${m.away_score}</b> ${m.away_team}${flagA(m.away_team)}${m.minute?` · ${esc(m.minute)}`:''}`).join('   ·   ');
  el.innerHTML=`<span class="hl-dot"></span><span class="hl-tag">Ao vivo</span><span class="hl-game">${txt}</span>`;
  el.hidden=false;
}

// ===== Palpites do jogo de agora (estatísticas do jogo atual/ao vivo) =====
// Olha TODAS as apostas para o jogo que está rolando (ou o próximo) e mostra placar
// mais escolhido, mais ousado e a aposta solitária — só QUANTIDADES, sem nomes.
// jogos a destacar agora: TODOS os que estão ao vivo (na Copa, a última rodada de cada grupo
// tem 2 simultâneos) — ou, se nenhum ao vivo, todos os do PRÓXIMO horário (±15min).
function gamesNow(){
  const ms=DATA.matches||[]; const byKick=(a,b)=>new Date(a.kickoff_sao_paulo||0)-new Date(b.kickoff_sao_paulo||0);
  const live=ms.filter(m=>m.status==='live').sort(byKick);
  if(live.length) return {games:live, live:true};
  const nowMs=Date.now();
  const up=ms.filter(m=>m.status==='scheduled'&&m.kickoff_sao_paulo&&new Date(m.kickoff_sao_paulo).getTime()>nowMs-2.5*3600e3).sort(byKick);
  if(!up.length) return null;
  const t0=new Date(up[0].kickoff_sao_paulo).getTime();
  return {games:up.filter(m=>Math.abs(new Date(m.kickoff_sao_paulo).getTime()-t0)<15*60e3), live:false};
}
// painel COMPLETO de um jogo (placar/status + na-mosca + 1X2 + 3 cards + rodapé). Reutilizado
// por jogo — assim 2 jogos simultâneos aparecem cada um com seus próprios stats.
function gameBlockHTML(m, live){
  const sum=k=>{ const [h,a]=k.split('×').map(Number); return h+a; };
  const preds=[];
  (DATA.participants||[]).forEach(p=>{
    const gk=p.picks&&p.picks.knockout&&p.picks.knockout[m.match_id];
    const g=(p.picks&&p.picks.groups&&p.picks.groups[m.match_id]) || (gk&&gk.used);
    if(g&&g[0]!=null&&g[1]!=null) preds.push(g[0]+'×'+g[1]);
  });
  const status = live
    ? `<span class="chip chip-live live"><span class="dot"></span> ao vivo</span> <span class="cg-min">${esc(m.minute||'em andamento')}</span>`
    : `<span class="chip chip-sched">📅 próximo</span> <span class="cg-min">${fmtDateTime(m.kickoff_sao_paulo)}</span>`;
  const score = live ? `<b>${m.home_score??0}×${m.away_score??0}</b>` : '×';
  const headLine=`<div class="cg-head">
    <div class="cg-match">${flag(m.home_team)}${m.home_team} ${score} ${m.away_team}${flagA(m.away_team)}</div>
    <div class="cg-status">${status}</div></div>`;
  if(!preds.length){
    return `<div class="cg-game">${headLine}<div class="cg-empty">Sem palpites de placar para este jogo ainda.</div></div>`;
  }
  const counts=new Map();
  preds.forEach(k=>counts.set(k,(counts.get(k)||0)+1));
  const ents=[...counts.entries()];
  // os 3 cards mostram placares SEMPRE DIFERENTES (cada métrica exclui os já mostrados).
  const most    = ents.reduce((x,y)=> y[1]>x[1]?y:x);
  const restB   = ents.filter(e=> e[0]!==most[0]);
  const boldest = restB.length ? restB.reduce((x,y)=> (sum(y[0])>sum(x[0])||(sum(y[0])===sum(x[0])&&y[1]>x[1]))?y:x) : null;
  const usados  = new Set([most[0], boldest && boldest[0]]);
  const restL   = ents.filter(e=> !usados.has(e[0]));
  const lonely  = restL.length ? restL.reduce((x,y)=> (y[1]<x[1]||(y[1]===x[1]&&sum(y[0])>sum(x[0])))?y:x) : null;
  const card=(ic,lab,k,n,sub)=>`<div class="cg-card"><div class="cg-ic">${ic}</div>
    <div class="cg-cl">${lab}</div><div class="cg-sc">${k}</div>
    <div class="cg-n">${n} aposta${n!==1?'s':''}</div><div class="cg-sub">${sub}</div></div>`;
  let cards = card('🎯','Placar mais escolhido',most[0],most[1],'o palpite da maioria');
  if(boldest) cards += card('🚀','Palpite mais ousado',boldest[0],boldest[1],'mais gols apostados');
  if(lonely)  cards += card('🎲', lonely[1]===1?'Aposta solitária':'Placar menos escolhido', lonely[0], lonely[1], lonely[1]===1?'só uma cravou esse':'o menos escolhido');

  // Palpite de RESULTADO (1X2): quantos no mandante / empate / visitante
  let hw=0,dr=0,aw=0;
  preds.forEach(k=>{ const [h,a]=k.split('×').map(Number); if(h>a)hw++; else if(h<a)aw++; else dr++; });
  const tot=preds.length;
  // arredondamento de maior-resto: os 3 %s somam exatamente 100.
  const _raw=[hw,dr,aw].map(n=> tot? n/tot*100 : 0);
  const _fl=_raw.map(Math.floor);
  const _pcs=[..._fl];
  if(tot){
    const _rem=Math.round(100-_fl.reduce((a,b)=>a+b,0));
    const _ord=_raw.map((v,i)=>[v-_fl[i],i]).sort((a,b)=>b[0]-a[0]);
    for(let k=0;k<_rem;k++) _pcs[_ord[k%3][1]]++;
  }
  const [pcH,pcD,pcA]=_pcs;
  const seg=(n,color)=> n>0?`<div style="width:${(n/tot*100).toFixed(1)}%;background:${color}"></div>`:'';
  const r1x2=`<div class="cg-1x2">
    <div class="cg-1x2-h">Quem o bolão acha que ganha</div>
    <div class="cg-1x2-bar">${seg(hw,'#57d98a')}${seg(dr,'#e8b94e')}${seg(aw,'#5b9bff')}</div>
    <div class="cg-1x2-leg">
      <span><i style="background:#57d98a"></i>${flag(m.home_team)}${m.home_team} <b>${hw}</b> · ${pcH}%</span>
      <span><i style="background:#e8b94e"></i>Empate <b>${dr}</b> · ${pcD}%</span>
      <span><i style="background:#5b9bff"></i>${m.away_team}${flagA(m.away_team)} <b>${aw}</b> · ${pcA}%</span>
    </div></div>`;
  // 🎯 NA MOSCA AO VIVO: quantas apostas batem o placar EXATO agora (recalcula a cada mudança).
  const liveKey = `${m.home_score??0}×${m.away_score??0}`;
  const naMosca = live ? preds.filter(k=>k===liveKey).length : 0;
  const moscaLine = live
    ? `<div class="cg-mosca"><span class="cg-mosca-dot"></span><span>Se acabasse agora (<b>${m.home_score??0} × ${m.away_score??0}</b>): <b>${naMosca}</b> aposta${naMosca!==1?'s':''} ${naMosca?'cravando o placar exato 🎯':'nesse placar ainda 👀'}</span></div>`
    : '';
  return `<div class="cg-game">${headLine}${moscaLine}${r1x2}<div class="cg-grid">${cards}</div>`
    +`<div class="cg-foot">${preds.length} palpites para este jogo · só números, sem nomes — o suspense continua 🤫</div></div>`;
}
function renderCurrentGameStats(){
  const box=document.getElementById('cgStats'); if(!box) return;
  const cur=gamesNow();
  if(!cur){ box.hidden=true; box.innerHTML=''; return; }
  box.hidden=false;
  const n=cur.games.length;
  const title = cur.live ? (n>1?'Os jogos de agora nas apostas':'O jogo de agora nas apostas')
                         : (n>1?'Os próximos jogos nas apostas':'O próximo jogo nas apostas');
  const liveBadge = (cur.live && n>1) ? ` <span class="cg-more">🔴 ${n} ao vivo ao mesmo tempo</span>` : '';
  box.innerHTML = `<h3 class="sub-h" style="margin-top:4px">🔥 ${title}${liveBadge}</h3>`
    + cur.games.map(m=>gameBlockHTML(m, cur.live)).join('');
}

let pelLens='pontos', pelDraw=null;
function renderPelotao(){
  const svg=document.getElementById('pelChart');
  if(!svg || !DATA.participants || !DATA.participants.length) return;
  const P=DATA.participants;
  const scores=P.map(p=>p.score).filter(v=>typeof v==='number');
  if(!scores.length) return;
  const outs=P.map(p=>p.correct_outcomes||0), exas=P.map(p=>p.exact_scores||0);
  const med=a=>{const s=[...a].sort((x,y)=>x-y);return s[Math.floor((s.length-1)/2)];};
  const short=s=>{s=String(s);return s.length>16?s.slice(0,15)+'…':s;};
  const binize=(v,maxBins)=>{const mn=Math.min(...v),mx=Math.max(...v),w=Math.max(1,Math.ceil((mx-mn+1)/maxBins)),b=[];
    for(let lo=mn;lo<=mx;lo+=w){const hi=lo+w-1;b.push({lo,hi,lab:w===1?`${lo}`:`${lo}–${hi}`,n:0});}
    v.forEach(x=>{b[Math.min(b.length-1,Math.floor((x-mn)/w))].n++;});return b;};
  const discrete=v=>{const mn=Math.min(...v),mx=Math.max(...v),b=[];
    for(let x=mn;x<=mx;x++)b.push({lo:x,hi:x,lab:`${x}`,n:v.filter(y=>y===x).length});return b;};
  const idxOf=(bins,val)=>bins.findIndex(b=>val>=b.lo&&val<=b.hi);
  const ranked=[...P].sort((a,b)=>b.score-a.score), leader=ranked[0], gap=ranked[1]?leader.score-ranked[1].score:0;
  const ss=[...scores].sort((a,b)=>a-b), q=p=>ss[Math.floor(p*(ss.length-1))];
  const dOut=discrete(outs), dExa=discrete(exas);
  const TK={
    pontos:`O pelotão se concentra entre ${q(.25)} e ${q(.75)} pts. O líder (${esc(short(leader.alias))}, ${leader.score}) abriu ${gap} ponto${gap!==1?'s':''} de frente${gap>=4?' e corre destacado na ponta':''}.`,
    acertos:`O miolo do bolão acerta cerca de ${med(outs)} resultados. Os extremos são poucos — é onde a disputa se decide.`,
    exatos:`Placar exato é raro: poucos cravam muitos e a maioria fica na base. Vale ouro no desempate.`
  };
  const XL={pontos:'pontos totais',acertos:'nº de resultados certos',exatos:'nº de placares exatos'};
  const GOLD='#F4C430',GREEN='#27B14B',FAINT='#8B919C',DIM='#BFC4CC';
  const lg=(c,t,dash)=>`<span style="display:flex;align-items:center;gap:5px"><span style="${dash?`width:14px;border-top:1.4px dashed ${c}`:`width:11px;height:11px;border-radius:2px;background:${c}`}"></span>${t}</span>`;
  pelDraw=function(){
    // px reais (viewBox = largura medida) → fontes legíveis em qualquer tela; nº de barras adapta no mobile
    const pr=(svg.parentNode&&svg.parentNode.clientWidth)||svg.clientWidth||640;
    const W=Math.max(300,Math.min(Math.round(pr),(window.innerWidth||9999))), H=320;
    svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
    let bins, medVal, leaderBin=-1;
    if(pelLens==='pontos'){bins=binize(scores, W<360?6:W<480?8:12); medVal=med(scores); leaderBin=idxOf(bins,leader.score);}
    else if(pelLens==='acertos'){bins=dOut; medVal=med(outs);}
    else {bins=dExa; medVal=med(exas);}
    const n=bins.length, maxN=Math.max(...bins.map(x=>x.n),1), scale=maxN*1.15;
    const x0=24,x1=W-24,top=54,base=276,pw=x1-x0,ph=base-top,slot=pw/n,bw=Math.min(slot*0.66,46);
    let s=`<line x1="${x0}" y1="${base}" x2="${x1}" y2="${base}" stroke="rgba(255,255,255,.16)"/>`;
    const mIdx=idxOf(bins,medVal);
    if(mIdx>=0){const mx=(x0+slot*mIdx+slot/2).toFixed(1);
      s+=`<line x1="${mx}" y1="${top-4}" x2="${mx}" y2="${base}" stroke="${FAINT}" stroke-dasharray="3 3"/>`;
      s+=`<text x="${mx}" y="${top-9}" fill="${FAINT}" font-size="11.5" text-anchor="middle">mediana ${medVal}</text>`;}
    bins.forEach((d,i)=>{const h=d.n/scale*ph, x=x0+slot*i+(slot-bw)/2, y=base-h, isL=i===leaderBin, cx=(x0+slot*i+slot/2).toFixed(1);
      if(d.n>0){s+=`<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="3" fill="${isL?GREEN:GOLD}"/>`;
        s+=`<text x="${cx}" y="${(y-5).toFixed(1)}" fill="${isL?GREEN:DIM}" font-size="12" font-weight="500" text-anchor="middle">${d.n}</text>`;}
      s+=`<text x="${cx}" y="${base+17}" fill="${FAINT}" font-size="11.5" text-anchor="middle">${d.lab}</text>`;});
    if(leaderBin>=0){const lx=x0+slot*leaderBin+slot/2, lab=W<480?`Líder ${leader.score} →`:`Líder · ${esc(short(leader.alias))} ${leader.score} →`;
      s+=`<text x="${Math.min(lx,x1-2).toFixed(0)}" y="${top}" fill="${GREEN}" font-size="12" font-weight="500" text-anchor="end">${lab}</text>`;}
    s+=`<text x="${x0}" y="${base+34}" fill="${FAINT}" font-size="11">${XL[pelLens]} →  (cada barra = nº de pessoas)</text>`;
    svg.innerHTML=s;
    document.getElementById('pelTake').textContent=TK[pelLens];
    const leg=[lg(GOLD,'pessoas'),lg(FAINT,'mediana',true)];
    if(leaderBin>=0)leg.push(lg(GREEN,'líder'));
    document.getElementById('pelLegend').innerHTML=leg.join('');
    document.querySelectorAll('#pelTabs .pel-tab').forEach(t=>t.classList.toggle('active',t.dataset.k===pelLens));
  };
  const tabs=document.getElementById('pelTabs');
  if(tabs && !tabs._wired){tabs._wired=1;tabs.addEventListener('click',e=>{const btn=e.target.closest('.pel-tab');if(!btn)return;pelLens=btn.dataset.k;pelDraw&&pelDraw();});}
  if(!window._pelResize){window._pelResize=1;let rt;window.addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(()=>pelDraw&&pelDraw(),150);});}
  pelDraw();
}

// Favoritos ao título: agrega o palpite de CAMPEÃO de cada aposta (picks.final.champion).
// 100% client-side (o dado já vem no data.json). %s por maior-resto somam exatamente 100.
function renderFavoritos(){
  const el=document.getElementById('favRows');
  if(!el) return;
  if(!DATA.participants || !DATA.participants.length){ el.innerHTML=''; return; }
  const cnt={}; let tot=0;
  DATA.participants.forEach(p=>{ const c=((p.picks||{}).final||{}).champion; if(c){ cnt[c]=(cnt[c]||0)+1; tot++; } });
  const rows=Object.entries(cnt).sort((a,b)=> b[1]-a[1] || a[0].localeCompare(b[0]));
  if(!tot){ el.innerHTML='<div class="cg-empty">Os palpites de campeão entram aqui.</div>'; return; }
  const fl=rows.map(([,n])=>Math.floor(n/tot*100));
  const rem=Math.round(100-fl.reduce((a,b)=>a+b,0));
  const ord=rows.map(([,n],i)=>[n/tot*100-fl[i],i]).sort((a,b)=>b[0]-a[0]);
  const pcs=[...fl]; for(let k=0;k<rem;k++) pcs[ord[k%ord.length][1]]++;
  const max=rows[0][1];
  el.innerHTML=rows.map(([team,n],i)=>{
    const w=Math.max(6,Math.round(n/max*100)), lead=i===0, col=lead?'var(--green)':'var(--gold)';
    return `<div class="fav-row">
      <div class="fav-team">${flag(team)} ${team}${lead?' <span class="fav-star">★</span>':''}</div>
      <div class="fav-bar"><i style="width:${w}%;background:${col}"></i></div>
      <div class="fav-val"><b style="color:${col}">${pcs[i]}%</b> · ${n}</div>
    </div>`;
  }).join('');
}

function render(){
  const P = [...(DATA.participants||[])].sort((a,b)=>a.rank-b.rank);
  if(!P.length) return;   // data.json vazio/malformado → degrada (não derruba a página inteira)
  renderClosing(P);       // tela de encerramento (aparece só quando a Copa termina)
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
  const next = (DATA.matches||[])
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
  const nextSpecial = (DATA.matches||[])
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
  renderPelotao();
  renderFavoritos();
  renderBomPalpite();
  renderExtras();
  renderMinhaAposta();
  // movement
  renderMovement();
  // stats
  renderNumberStats();
  renderWisdom();
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
      <div class="nm">${esc(p.alias)}${tag}</div>
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
  renderHeroLive();
  // aba padrão: 'Próximos' enquanto houver jogos por vir; senão 'Encerrados'
  const hasScheduled = (DATA.matches||[]).some(m=>m.status==='scheduled');
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
      `<li>${esc(String(d.teams))}: <b>${esc(String(d.primaria||d.oficial))}</b> ≠ <b>${esc(String(d.secundaria||d.espn))}</b>${d.lock?' (correção manual ativa)':''}</li>`).join('');
    el.innerHTML = `<b style="color:#ff6b6b">⚠ Divergência entre fontes detectada</b> — em verificação pelo organizador:
      <ul style="margin:6px 0 0 16px">${list}</ul>
      <div style="margin-top:6px;color:var(--ink-faint)">${pair}${when}. O organizador foi avisado automaticamente.</div>`;
  } else if(a.status === 'fonte_indisponivel'){
    el.innerHTML = `Conferência da 2ª fonte temporariamente indisponível — placares seguem pela fonte primária (ESPN).${when}`;
  } else if((a.resolvidas || []).length){
    // Há divergência(s) DECIDIDA(s) pelo organizador (vale a ESPN): banner verde + nota transparente.
    const list = a.resolvidas.map(d =>
      `${esc(String(d.teams))} — <b>${esc(String(d.primaria||d.oficial))}</b> (≠ ${esc(String(d.secundaria||d.espn))})`).join('; ');
    el.innerHTML = `<b class="ok">✓ ${a.agree}/${a.compared} jogos encerrados conferidos em 2 fontes independentes</b>
      (${pair}) — nenhuma divergência em aberto.${when}
      <div style="margin-top:6px;color:var(--ink-faint)">Decidido pelo organizador (vale o placar da ESPN): ${list}.</div>`;
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
    `Como divide: a <b>Lanterna de Ouro</b> (último ao fim da 1ª fase) recebe a aposta de volta (${brl(refund||bet)}); os percentuais incidem sobre o <b>restante</b> (${brl(base)}). <b>Empate:</b> quem empatar numa posição divide, em partes iguais, os prêmios das posições que o grupo ocupa (ex.: 3 em 1º dividem o 1º+2º+3º; 5 em 4º dividem o 4º). Os pontos da 1ª fase não zeram — o vencedor da fase segue elegível aos prêmios finais. Bolão de palpites entre amigos: sem odds, sem casa de apostas.`;
}

// ---- Tela de ENCERRAMENTO: aparece só quando a Copa acaba (final decidida + tudo encerrado).
// Mostra TODOS os premiados (1º–4º, Bom de Palpite, Lanterna), com empate dividindo os prêmios
// das posições ocupadas — mesma matemática do bloco "Prêmio acumulado" (motor entrega prize_pos/
// bom_palpite/phase1_points; o front só distribui o dinheiro). ----
function renderClosing(P){
  const sec = document.getElementById('closing');
  const matches = DATA.matches || [];
  const fin = matches.find(m=>m.slot==='FIN');
  const finished = !!(fin && fin.status==='finished') && matches.length>0 && matches.every(m=>m.status==='finished');
  if(!finished){ sec.hidden = true; return; }

  const bet = (DATA.meta && DATA.meta.bet_value) || 60;
  const paid = P.filter(p=>p.paid);
  const paidN = paid.length;
  const pot = paidN*bet, refund = paidN>0?bet:0, base = Math.max(0, pot-refund);
  const PCT = {1:.40, 2:.25, 3:.10, 4:.05};
  const LAB = {1:['🏆','Campeão do Bolão'], 2:['🥈','Vice-campeão'], 3:['🥉','3º lugar'], 4:['🏅','4º lugar']};
  // agrupa pagantes por posição de prêmio (empate = mesma posição → dividem as posições ocupadas)
  const byPos = {};
  paid.forEach(p=>{ if(p.prize_pos){ (byPos[p.prize_pos] = byPos[p.prize_pos]||[]).push(p.alias); } });
  const prizes = [];
  [1,2,3,4].forEach(pos=>{
    const win = byPos[pos]; if(!win || !win.length) return;
    let pct=0; for(let o=pos; o<pos+win.length; o++) pct += (PCT[o]||0);   // soma das posições ocupadas
    prizes.push({ic:LAB[pos][0], lab:LAB[pos][1], win, each: base?Math.round(base*pct/win.length):0, champ:pos===1});
  });
  const bp = paid.filter(p=>p.bom_palpite).map(p=>p.alias);
  if(bp.length) prizes.push({ic:'⚡', lab:'Bom de Palpite', win:bp, each: base?Math.round(base*.20/bp.length):0});
  if(paid.length){   // Lanterna de Ouro = último PAGANTE por pontos da 1ª fase (recebe a aposta de volta)
    const worst = Math.min(...paid.map(p=>p.phase1_points ?? p.score));
    const lant = paid.filter(p=>(p.phase1_points ?? p.score)===worst).map(p=>p.alias);
    prizes.push({ic:'🔦', lab:'Lanterna de Ouro', win:lant, each: lant.length?Math.round(refund/lant.length):0, note:'devolução'});
  }
  const champs = byPos[1] || [];
  const worldCh = (fin && fin.winner) ? `${flag(fin.winner)} ${fin.winner}` : null;
  const fmtWin = a => a.map(esc).join(' + ');
  document.getElementById('closingCard').innerHTML =
    `<div class="closing-kicker">🏁 Bolão Miha 2026 · Encerrado</div>
     <div class="closing-champ">👑 ${champs.length?fmtWin(champs):'—'}
       <small>${champs.length>1?'Campeões do Bolão — empate, dividem':'Campeão do Bolão'}${worldCh?` · 🌍 Campeão Mundial: ${worldCh}`:''}</small></div>
     <div class="closing-grid">${prizes.map(pz=>`
        <div class="closing-prize${pz.champ?' is-champ':''}">
          <div class="cp-top">${pz.ic} ${esc(pz.lab)}</div>
          <div class="cp-win">${fmtWin(pz.win)}${pz.win.length>1?' <span style="font-weight:600;color:var(--ink-faint)">(dividem)</span>':''}</div>
          <div class="cp-amt">${pz.each?brl(pz.each)+(pz.win.length>1?' cada':''):'—'}${pz.note?` <span style="font-weight:600;color:var(--ink-faint)">· ${pz.note}</span>`:''}</div>
        </div>`).join('')}</div>
     <div class="closing-foot">Prêmios sobre ${brl(pot)} (${paidN} aposta${paidN!==1?'s':''} paga${paidN!==1?'s':''}). A Lanterna recebe a aposta de volta; os percentuais incidem sobre o restante. Empate numa posição divide, em partes iguais, os prêmios das posições ocupadas. 🎉</div>`;
  sec.hidden = false;
}

// ---- Classificação escalável (busca + filtro pagas/café + colapso) ----
let lbFilter='all', lbSearch='', lbExpanded=false;
const LB_LIMIT=7;   // mostra o Top 7 (zona de prêmio + perseguidores); o resto expande
function renderLeaderboard(){
  const all=[...DATA.participants].sort((a,b)=>a.rank-b.rank);
  const total=all.length, paidN=all.filter(p=>p.paid).length, freeN=total-paidN;
  document.getElementById('lbCount').textContent =
    `${total} aposta${total!==1?'s':''} · ${paidN} para valer 💰 · ${freeN} café-com-leite ☕`;
  // prêmio em dinheiro: vem do MOTOR (in_the_money), que respeita empate na borda (empatados
  // dividem). fallback p/ data.json antigo (sem a flag): top-4 pagantes pela ordem.
  const hasMoney = all.some(p=>p.in_the_money!==undefined);
  const prizeSet=new Set((hasMoney ? all.filter(p=>p.in_the_money) : all.filter(p=>p.paid).slice(0,4)).map(p=>p.alias));
  const maxRank=all.length?Math.max(...all.map(p=>p.rank)):0;   // com empate, o último rank ≠ nº de apostas
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
      const free  = p.paid?'':'<span class="chip chip-ft" title="café-com-leite: joga pela glória, não concorre à grana">☕ café-com-leite</span>';
      const hit   = q?'<span class="you-tag">é você?</span>':'';
      return `<div class="lb-row ${cls}">
        <div class="rk">${p.rank}</div>
        <div class="who">
          <div class="nm">${medal}${isLast?'🔦 ':''}${esc(p.alias)} ${arrow(p.rank_change)} ${prize}${free} ${hit}</div>
          <div class="meta">na rodada: +${p.day_points ?? p.last_match_points ?? 0} pts · placares exatos: ${p.exact_scores ?? 0}</div>
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
// Bom de Palpite — ranking só da 1ª fase (top 5). Regra v2.1: os 20% do bolo vão ao LÍDER
// PAGANTE ao fim da 1ª fase; empate no topo pagante DIVIDE os 20%. Café-com-leite (☕) compete
// nos pontos, mas não leva prêmio. Exibição PARCIAL até o fim da fase de grupos.
function renderBomPalpite(){
  const P = [...DATA.participants]
    .map(p => ({...p, ph1: p.phase1_points ?? p.score}))
    // desempate visual canônico (igual à Classificação): exatos → acertos
    .sort((a,b) => b.ph1 - a.ph1 || (b.exact_scores??0)-(a.exact_scores??0) || (b.correct_outcomes??0)-(a.correct_outcomes??0));
  // O MOTOR decide rank/vencedor (campos phase1_rank/bom_palpite); o front só exibe.
  // fallback client-side só p/ data.json antigo — some assim que o robô republica.
  const fromEngine = P.some(p => p.bom_palpite !== undefined);
  let fbWin = new Set(), fbSplit = false;
  if(!fromEngine){
    const ps = P.filter(p=>p.paid).map(p=>p.ph1); const mx = ps.length ? Math.max(...ps) : null;
    fbWin = new Set(P.filter(p=>p.paid && p.ph1===mx).map(p=>p.alias)); fbSplit = fbWin.size>1;
  }
  const rows = P.slice(0, 5).map(p => {
    const rk = p.phase1_rank ?? (1 + P.filter(o => o.ph1 > p.ph1).length);
    const win = fromEngine ? p.bom_palpite===true : fbWin.has(p.alias);
    const split = fromEngine ? p.bom_palpite_split===true : fbSplit;
    const cafe = p.paid ? '' : ' <span class="chip chip-ft" title="café-com-leite: compete, mas não leva prêmio">☕</span>';
    const badge = win ? `<span class="bp-win-badge">🏁 ${split ? 'divide' : 'leva'} os 20%</span>` : '';
    return `<div class="bp-row${rk===1?' bp-lead':''}${win?' bp-win':''}">
      <span class="bp-rk">${rk}º</span>
      <span class="bp-nm"><span class="bp-name">${esc(p.alias)}</span>${cafe}</span>
      <span class="bp-pts">${p.ph1} pts</span>
      ${badge}
    </div>`;
  }).join('');
  const foot = `<div class="bp-foot">⏳ Parcial — os <b>20%</b> vão ao líder <b>pagante</b> ao fim da 1ª fase; empate no topo divide. ☕ café-com-leite joga, mas não leva a grana.</div>`;
  document.getElementById('bpList').innerHTML = rows
    ? rows + foot
    : '<div class="lb-empty">Sem pontos na 1ª fase ainda.</div>';
}

// 📊 Movimentação da rodada — DESTAQUE: mais pontos na rodada (day_points). + maior salto/tombo
// (base: rank_change "desde a última mudança" — rótulo deixa isso claro). Empates: todos juntos.
function renderMovement(){
  const mv = DATA.movement || {};
  const hero = document.getElementById('moveHero'), grid = document.getElementById('moveGrid');
  if(!hero || !grid) return;
  // tolera o shape ANTIGO ({alias,delta}) até o robô republicar — transição sem NaN.
  const norm = o => !o ? null : ('value' in o ? o : {value:o.delta, holders:[o.alias], count:1});
  mv.biggest_jump = norm(mv.biggest_jump); mv.biggest_drop = norm(mv.biggest_drop);
  const rp = mv.round_points;
  hero.innerHTML = rp
    ? `<div class="move-hero"><div class="lab">⚡ Mais pontos na rodada</div>
        <div class="hero-v"><b>+${rp.value}</b> <span class="u">pts${rp.count>1?' cada':''}</span></div>
        <div class="who">${holdersWrap(rp.holders)}</div>
        <div class="extra">${rp.count>1?'mandaram bem na rodada 🔥':'a melhor da rodada 🔥'}</div></div>`
    : `<div class="move-hero"><div class="lab">⚡ Mais pontos na rodada</div>
        <div class="who" style="margin-top:8px;color:var(--ink-dim);font-weight:600">A rodada ainda não pontuou — a bola decide ⚽</div></div>`;
  const card = (cls,lab,arrow,o,solo,tie,empty) => o
    ? `<div class="move-card"><div class="lab">${lab}<span class="lab-sub">desde a última mudança no placar</span></div>
        <div class="big ${cls}">${arrow}${Math.abs(o.value)}${o.count>1?' <span class="u">cada</span>':''}</div>
        <div class="who">${holdersWrap(o.holders)}</div>
        <div class="extra">${o.count>1?tie:solo}</div></div>`
    : `<div class="move-card"><div class="lab">${lab}</div><div class="who" style="margin-top:8px;color:var(--ink-dim);font-weight:600">${empty}</div></div>`;
  grid.innerHTML =
      card('up','📈 Maior salto','▲',mv.biggest_jump,'disparou na rodada 🚀','subiram junto 🚀','Ninguém saltou nessa rodada.')
    + card('down','📉 Maior tombo','▼',mv.biggest_drop,'escorregou na rodada — dá pra recuperar 🍀','azar coletivo — tão no mesmo barco 🍀','Rodada tranquila — ninguém despencou. 😌');
}

// 🎯 Números do bolão — superlativos com EMPATE EXPLÍCITO: mostra TODOS que alcançaram o
// valor (até 3 nomes + "+X"), nunca um sorteado por desempate escondido. holders vêm do motor.
function renderNumberStats(){
  const el = document.getElementById('statGrid'); if(!el) return;
  const st = DATA.stats || {};
  const N = 3;   // nomes inline antes do "+X"
  const names = o => holdersWrap((o.holders && o.holders.length) ? o.holders : (o.alias ? [o.alias] : []), N);
  const cada = o => ((o.count || 1) > 1 ? ' cada' : '');
  const cards = [];
  const be = st.best_exact;
  if(be && (be.value ?? 0) > 0){
    const many = (be.count || 1) > 1;
    cards.push(`<div class="stat stat-good">
      <div class="ico">🎯</div><div class="lab">Mais placares exatos</div>
      <div class="val"><b>${be.value}</b><span class="u">${esc(be.unit || 'placares exatos')}${cada(be)}</span></div>
      <div class="who">${names(be)}</div>
      <div class="extra">${many ? 'cravaram na mosca 🎯' : 'cravou na mosca 🎯'}</div>
    </div>`);
  }
  const cu = st.cursed;   // motor manda null no caso degenerado (quase todo mundo no piso)
  if(cu){
    const many = (cu.count || 1) > 1;
    cards.push(`<div class="stat stat-cold">
      <div class="ico">🧤</div><div class="lab">Pé-frio do bolão</div>
      <div class="val"><b>${cu.value}</b><span class="u">${esc(cu.unit || 'placares exatos')}${cada(cu)}</span></div>
      <div class="who">${names(cu)}</div>
      <div class="extra">${many ? 'menos placares exatos do bolão — dá pra virar 🍀' : 'o menos cravado do bolão — dá pra virar 🍀'}</div>
    </div>`);
  }
  el.innerHTML = cards.join('') || '<div class="lb-empty">Sem números ainda — os jogos decidem.</div>';
}

// "Sabedoria das multidões": o placar-consenso (mediana do palpite de todo o bolão) erra menos
// que o apostador médio? Vem pronto do motor (fun_stats.compute_wisdom) — só exibe.
function renderWisdom(){
  const el=document.getElementById('wisdomCard'); if(!el) return;
  const w=DATA.wisdom;
  if(!w){ el.innerHTML='<div class="lb-empty">Ainda sem jogos suficientes pra medir isso.</div>'; return; }
  const better=w.pct_better>=0;
  const bc=w.best_call, wc=w.worst_call;
  const call=(c,ico,lab)=>`<div class="extra">${ico} ${lab}: ${flag(c.home)}${esc(c.home)} <b>${c.real[0]}×${c.real[1]}</b> ${esc(c.away)}${flagA(c.away)} — o bolão previu ${c.consensus[0]}×${c.consensus[1]} (mediana).</div>`;
  el.innerHTML=`<div class="stat ${better?'stat-good':'stat-cold'}" style="grid-column:1/-1">
    <div class="ico">🧠</div><div class="lab">A sabedoria do bolão</div>
    <div class="val"><b>${better?'−':'+'}${Math.abs(w.pct_better)}%</b><span class="u">de erro vs. o apostador médio</span></div>
    <div class="who">${better?'O "placar-consenso" (mediana dos 88 palpites) erra MENOS que qualquer um sozinho':'Dessa vez o apostador médio venceu o consenso'} · ${w.games_evaluated} jogos avaliados</div>
    ${call(bc,'✅','Onde o consenso mais acertou')}
    ${call(wc,'😅','Onde o consenso mais errou')}
  </div>`;
}

// Categorias Extras — três estados claros (Definido/Parcial/Em aberto) + quem pontuou
function renderExtras(){
  const list = DATA.extras_summary || EXTRAS_DEF.map(d => ({...d, real:null, winners:[]}));
  document.getElementById('exGrid').innerHTML = list.map(x=>{
    const done = x.real !== null && x.real !== undefined && x.real !== '';
    const live = !done && !!x.partial;
    const badge = done ? '<span class="ex-state done">Definido ✅</span>'
                : live ? '<span class="ex-state live">Parcial 📡</span>'
                       : '<span class="ex-state open">Em aberto ⏳</span>';
    let body;
    if(done){
      const W = x.winners || [], n = W.length;
      const names = holdersWrap(W, 6);
      body = `<div class="ex-real">${flag(String(x.real))}${esc(String(x.real))}</div>
        <div class="ex-winners">${n
          ? `🎉 <b>+${x.points} para ${n} aposta${n!==1?'s':''}</b><br>${names}`
          : 'ninguém cravou — o futebol venceu 😅'}</div>`;
    } else if(live){
      body = `<div class="ex-status">${esc(String(x.partial))}<div class="ex-hint">prévia ao vivo · pode mudar até o fim</div></div>`;
    } else {
      body = '<div class="ex-status">ainda não rolou — definido ao longo da Copa</div>';
    }
    return `<div class="ex-card ${done?'done':''}">
      <div class="ex-top"><span class="ex-lab">${x.label}</span><span class="ex-pts">+${x.points} pts</span></div>
      <div class="ex-badge-row">${badge}</div>
      ${body}
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
  if(m.status==='live') foot = `<span class="mlive-min">${m.minute?('🔴 '+esc(m.minute)):'🔴 em andamento'}</span><span class="verif">placar parcial</span>`;
  else if(m.status==='finished') foot = `<span>📅 ${fmtDateTime(m.kickoff_sao_paulo)}</span><span class="verif">${m.verified?'<span class="ok">✓ conferido</span>':'<span class="warn">• conferindo</span>'}</span>`;
  else foot = `<span>📅 ${fmtDateTime(m.kickoff_sao_paulo)}</span><span class="verif">a bola não rolou</span>`;
  return `<div class="mcard">
    <div class="top"><span class="grp">${m.phase ? m.group : 'Grupo '+m.group}</span><span style="display:flex;gap:6px;align-items:center">${special}${chip}</span></div>
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

// ---- Prévia "a definir" da próxima fase do mata-mata (transição entre fases) ----
// Topologia FIXA do chaveamento (igual ao resolve_bracket): cada slot da fase seguinte é
// alimentado por dois slots da fase atual. Enquanto o confronto não está resolvido (sem os dois
// times reais), mostramos "Vencedor de A×B × Vencedor de C×D" — assim a Central nunca fica
// "vazia/confusa" na virada de fase, e dá pra ver o que vem.
const KO_NEXT = {R32:'R16', R16:'QF', QF:'SF', SF:'FIN'};
const KO_NSLOTS = {R16:8, QF:4, SF:2, FIN:1};
const KO_PHASE_LABEL = {R32:'16 avos', R16:'Oitavas', QF:'Quartas', SF:'Semifinal', FIN:'Final', TER:'3º lugar'};
const _p2 = n => String(n).padStart(2,'0');
function nextPhasePreview(){
  const ko = (DATA.matches||[]).filter(m=>m.phase && m.slot);
  if(!ko.length) return [];
  const bySlot = {}; ko.forEach(m=>{ bySlot[m.slot]=m; });
  const out = [];
  for(const cur of ['R32','R16','QF','SF']){
    const nxt = KO_NEXT[cur];
    for(let k=1; k<=KO_NSLOTS[nxt]; k++){
      const slot = nxt==='FIN' ? 'FIN' : `${nxt}-${_p2(k)}`;
      if(bySlot[slot]) continue;                          // já resolvido → aparece como jogo normal
      const f1 = bySlot[`${cur}-${_p2(2*k-1)}`], f2 = bySlot[`${cur}-${_p2(2*k)}`];
      if(f1 && f2) out.push({slot, phase:nxt, f1, f2});    // só prevê quando os 2 alimentadores existem
    }
  }
  if(!bySlot['TER']){   // 3º lugar = perdedores das semis (previsível quando as SFs existem)
    const s1=bySlot['SF-01'], s2=bySlot['SF-02'];
    if(s1 && s2) out.push({slot:'TER', phase:'TER', f1:s1, f2:s2, losers:true});
  }
  return out;
}
// rótulo de UM lado do confronto futuro: se o jogo alimentador já tem vencedor, mostra o time
// REAL (com bandeira) — resolução PARCIAL; senão "Vencedor/Perdedor de A × B". 3º lugar = perdedor.
function koSide(feed, losers){
  if(!feed) return {label:'—', team:null};
  if(feed.winner){
    const team = losers ? (feed.winner===feed.home_team ? feed.away_team : feed.home_team) : feed.winner;
    return {label:team, team};
  }
  return {label:`${losers?'Perdedor':'Vencedor'} de ${feed.home_team} × ${feed.away_team}`, team:null};
}
function previewCardHTML(pv){
  const a = koSide(pv.f1, pv.losers), b = koSide(pv.f2, pv.losers);
  const side = s => `<div class="team ${s.team?'':'team-tbd'}"><span>${s.team?flag(s.team):''}${esc(s.label)}</span></div>`;
  const n = (a.team?1:0) + (b.team?1:0);
  const foot = n===2 ? '🔧 confronto definido' : n===1 ? '🔧 já tem um lado — aguarda o outro classificado'
                                                        : '🔧 se define quando esses dois jogos terminam';
  return `<div class="mcard mcard-tbd">
    <div class="top"><span class="grp">${KO_PHASE_LABEL[pv.phase]||pv.phase}</span><span class="chip chip-sched">A definir</span></div>
    ${side(a)}${side(b)}
    <div class="foot"><span>${foot}</span></div>
  </div>`;
}

let matchExpanded=false;
const MATCH_LIMIT=9;   // mostra ~3 linhas; o resto fica atrás de "Ver todos" (anti-scroll)
function renderMatches(filter){
  const sortK = (a,b)=>new Date(a.kickoff_sao_paulo||0)-new Date(b.kickoff_sao_paulo||0);
  let list = (DATA.matches||[]).filter(m=>m.status===filter).sort(sortK);
  const previews = filter==='scheduled' ? nextPhasePreview() : [];
  // A próxima fase vira UM grupo só: os confrontos JÁ definidos dela (ex.: Canadá × Marrocos)
  // saem da lista cronológica (onde ficavam soterrados, por serem mais à frente) e aparecem
  // JUNTO dos "em montagem" — assim a foto das oitavas fica completa num lugar só.
  const montPhases = new Set(previews.map(p=>p.phase));
  const resolvedNext = list.filter(m=>m.phase && montPhases.has(m.phase)).sort(sortK);
  if(resolvedNext.length) list = list.filter(m=>!(m.phase && montPhases.has(m.phase)));
  const el = document.getElementById('matchList');
  const more = document.getElementById('matchMore');
  const empty = filter==='scheduled' ? 'Sem próximos jogos no momento.' : 'Nenhum jogo encerrado ainda.';
  if(!list.length && !previews.length && !resolvedNext.length){ el.innerHTML = `<div class="mcard" style="grid-column:1/-1;text-align:center;color:var(--ink-faint)">${empty}</div>`; if(more) more.hidden=true; return; }
  const collapsed = !matchExpanded && list.length>MATCH_LIMIT;
  const view = collapsed ? list.slice(0,MATCH_LIMIT) : list;
  let html = view.map(matchCardHTML).join('');
  if(resolvedNext.length || previews.length){
    const phs = [...new Set([...montPhases, ...resolvedNext.map(m=>m.phase)])].map(p=>KO_PHASE_LABEL[p]||p);
    const nome = phs.length===1 ? phs[0] : 'Próxima fase';
    html += `<div class="match-note">🔧 <b>${nome}</b> — os confrontos já definidos aparecem aqui; os outros se montam conforme os jogos terminam.</div>`;
    html += resolvedNext.map(matchCardHTML).join('');   // já definidos (ex.: Canadá × Marrocos)
    html += previews.map(previewCardHTML).join('');      // ainda em montagem
  }
  el.innerHTML = html;
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
let maSelected = null, maTab = 'upcoming';   // abre em "A jogar": quem consulta quer ver o próximo/atual
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
  // rótulo: grupo ("Grupo A") ou fase do mata-mata ("16 avos") — KO tem m.phase
  const fase = m.phase ? m.group : 'Grupo '+m.group;
  // mata-mata: selo de mudança (e.changed só existe nas linhas de KO) + original riscado
  const chg = e.changed===undefined ? ''
    : (e.changed ? ' · <small style="color:#5FE08A">✏️ você atualizou</small>'
                 : ' · <small style="color:var(--ink-faint)">🔒 original</small>');
  const orig = (e.changed && e.orig) ? ` <small style="color:var(--ink-faint)">(antes: ${e.orig[0]}×${e.orig[1]})</small>` : '';
  let res;
  if(played){
    let nota='';
    if(m.decided_by==='pen' && m.pen_home!=null) nota=` <small style="color:var(--ink-faint)">(pênaltis ${m.pen_home}×${m.pen_away}) · vale o placar até a prorrogação</small>`;
    res = `saiu <b>${m.home_score}×${m.away_score}</b>${nota}`;
  } else res = (m.status==='live' ? '🔴 em andamento' : 'aguardando o jogo');
  return `<div class="ma-pick">
    <div>
      <div class="teams"><small>${fase}${chg}${sp}</small><br>${flag(m.home_team)}${m.home_team} <b>${e.ph}×${e.pa}</b> ${m.away_team}${flagA(m.away_team)}${orig}</div>
      <div class="guess">${res}</div>
    </div>
    <span class="ma-pts ${cls}">${txt}</span>
  </div>`;
}

// mini-gráfico de linha da POSIÇÃO ao longo do tempo (rank 1 = melhor, fica no TOPO do desenho).
// series = [[rank,total]|null, ...] alinhado a DATA.history_dates; pontos ausentes (dia sem
// snapshot pra essa pessoa, ex.: entrou depois) são simplesmente pulados na linha.
function journeySVG(series){
  const pts=series.map((v,i)=>v?{i,rank:v[0]}:null).filter(Boolean);
  if(pts.length<2) return '';
  const ranks=pts.map(x=>x.rank), minR=Math.min(...ranks), maxR=Math.max(...ranks);
  const W=320,H=64,pad=6,n=series.length;
  const x=i=>pad+(W-2*pad)*(n>1?i/(n-1):0);
  const y=r=>pad+(H-2*pad)*(maxR===minR?0.5:(r-minR)/(maxR-minR));   // rank baixo (melhor) -> y pequeno (topo)
  const line=pts.map(pt=>`${x(pt.i).toFixed(1)},${y(pt.rank).toFixed(1)}`).join(' ');
  const last=pts[pts.length-1], first=pts[0];
  const melhorou=first.rank-last.rank;
  const color=melhorou>0?'#27B14B':(melhorou<0?'#E6533D':'#F4C430');
  const dots=pts.map(pt=>`<circle cx="${x(pt.i).toFixed(1)}" cy="${y(pt.rank).toFixed(1)}" r="2.2" fill="${color}" opacity="${pt===last?1:0.4}"/>`).join('');
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:64px;display:block" preserveAspectRatio="none">
    <polyline points="${line}" fill="none" stroke="${color}" stroke-width="2"/>${dots}
  </svg>`;
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
  const paidBadge = p.paid?'':'<span class="chip chip-ft" title="café-com-leite: joga pela glória, não concorre à grana">☕ café-com-leite</span>';
  // zona de prêmio = MESMA fonte do leaderboard (in_the_money do motor; respeita empate na
  // borda). Antes recalculava top-4 e divergia: empatado no 4º via 💰 na lista e não aqui.
  const hasMoney=all.some(x=>x.in_the_money!==undefined);
  const prizeSet=new Set((hasMoney?all.filter(x=>x.in_the_money):all.filter(x=>x.paid).slice(0,4)).map(x=>x.alias));
  const prize=prizeSet.has(p.alias)?'<span class="chip chip-prize">💰 zona de prêmio</span>':'';
  const mx=p.max_possible??p.score, cur=p.score;
  const curW=(cur/Math.max(mx,1)*100).toFixed(1), avW=(Math.max(0,mx-cur)/Math.max(mx,1)*100).toFixed(1);
  const ph1=p.phase1_points??p.score;

  let h=`<div class="ma-hero">
    <div class="ma-av">${initials}</div>
    <div class="ma-who"><div class="ma-name">${esc(p.alias)} ${mv}</div>
      <div class="ma-sub">${p.rank}º de ${total}${p.eliminated?' · <span style="color:var(--coral)">eliminado</span>':''} ${prize}${paidBadge}</div></div>
    <div class="ma-score"><b>${p.score}</b><span>pontos</span></div></div>
  <div class="ma-break">
    <div class="ma-kpi"><b>${ph1}</b><span>pts 1ª fase</span></div>
    <div class="ma-kpi"><b>${p.exact_scores??0}</b><span>placares exatos</span></div>
    <div class="ma-kpi"><b>+${p.day_points ?? p.last_match_points ?? 0}</b><span>na rodada</span></div>
    <div class="ma-kpi"><b>${mx}</b><span>máx. possível</span></div>
  </div>
  <div class="ma-barwrap"><div class="ma-barlab"><span>corrida pelo título</span><span>${cur} / ${mx}</span></div>
    <div class="ma-bar"><i style="width:${curW}%"></i><u style="width:${avW}%"></u></div></div>`;

  // ---- estatísticas "divertidas" (fun_stats.py já manda tudo pronto; só exibe) ----
  const fun=p.fun||{};
  if(fun.twin || fun.rival){
    const names=a=>a.map(esc).join(' + ');
    const twinTxt = fun.twin
      ? (fun.twin.distance===0
          ? `${names(fun.twin.aliases)} — apostas IDÊNTICAS. Só pode ser telepatia (ou a mesma pessoa) 👀`
          : `${names(fun.twin.aliases)} (diferença de ${fun.twin.distance} gol${fun.twin.distance!==1?'s':''} no total dos 72 jogos)`)
      : '—';
    const rivalTxt = fun.rival ? `${names(fun.rival.aliases)} (diferença de ${fun.rival.distance} gols)` : '—';
    h+=`<div class="ma-sec"><h4>🧬 Seu gêmeo de aposta</h4>
      <div class="ma-final-row"><span><span class="pos">Mais parecido com você:</span> ${twinTxt}</span></div>
      <div class="ma-final-row"><span><span class="pos">Seu arqui-rival:</span> ${rivalTxt}</span></div>
    </div>`;
  }
  const gp=fun.goal_profile;
  if(gp){
    const ICO={quente:'🔥 Time-Quente',frio:'❄️ Cabeça-Fria',equilibrado:'⚖️ Equilibrado'};
    const diffPct=gp.bolao_avg?Math.round((gp.avg_goals/gp.bolao_avg-1)*100):0;
    const diffTxt=diffPct===0?'bem na média do bolão':(diffPct>0?`${diffPct}% ACIMA da média do bolão`:`${Math.abs(diffPct)}% ABAIXO da média do bolão`);
    h+=`<div class="ma-sec"><h4>🌡️ Seu perfil de apostador</h4>
      <div class="ma-final-row"><span>${ICO[gp.label]} — média de <b>${gp.avg_goals}</b> gols/jogo apostado, ${diffTxt} (bolão: ${gp.bolao_avg}).</span></div>
    </div>`;
  }
  const rs=fun.rank_series||[], hdates=DATA.history_dates||[];
  const known=rs.filter(Boolean);
  if(known.length>=2 && hdates.length===rs.length){
    const firstIdx=rs.findIndex(Boolean), lastIdx=rs.length-1-[...rs].reverse().findIndex(Boolean);
    const firstRank=rs[firstIdx][0], lastRank=rs[lastIdx][0];
    const delta=firstRank-lastRank;
    const deltaTxt = delta>0?`subiu ${delta} posiç${delta!==1?'ões':'ão'}`:(delta<0?`caiu ${Math.abs(delta)} posiç${Math.abs(delta)!==1?'ões':'ão'}`:'ficou estável');
    const desde=hdates[firstIdx].split('-').reverse().join('/');
    h+=`<div class="ma-sec"><h4>📈 Sua jornada no bolão</h4>
      <div style="font-size:12.5px;color:var(--ink-dim);margin-bottom:6px">Desde ${desde}, você ${deltaTxt} (${firstRank}º → ${lastRank}º).</div>
      ${journeySVG(rs)}
    </div>`;
  }

  const picks=p.picks;
  if(!picks){
    h+=`<div class="ma-nodata">📋 O detalhe dos palpites aparece com os dados reais — esta é a simulação de exemplo.</div>`;
  } else {
    const mm={}; (DATA.matches||[]).forEach(x=>mm[x.match_id]=x);
    // ---- 🏆 Meus palpites — MATA-MATA (no topo: é o que importa agora) ----
    // confronto REAL (só slots com times definidos) + o placar que VAI VALER (used = Form OU original).
    const koEntries=Object.entries(picks.knockout||{}).map(([slot,k])=>(
        {mid:slot, m:mm[slot], ph:k.used[0], pa:k.used[1], pts:k.pts, changed:k.changed, orig:k.orig}))
      .filter(e=>e.m)
      // NÃO-jogados primeiro (a fase que importa agora, ex.: oitavas), depois os encerrados —
      // senão a fase atual fica soterrada sob os jogos já disputados. Dentro de cada grupo, por horário.
      .sort((a,b)=> ((a.m.status==='finished')-(b.m.status==='finished'))
                    || (new Date(a.m.kickoff_sao_paulo||0)-new Date(b.m.kickoff_sao_paulo||0)));
    if(koEntries.length){
      const koPts=koEntries.reduce((s,e)=> s+(e.pts||0),0);
      const koBtn = DATA.knockout_form_url
        ? `<a href="${esc(DATA.knockout_form_url)}" target="_blank" rel="noopener" style="display:block;text-align:center;margin-top:10px;padding:11px;background:var(--gold);color:#0a3d2c;font-weight:800;border-radius:10px;text-decoration:none">✏️ Atualizar meus palpites do mata-mata</a>`
        : '';
      // divisória "já encerrados" entre os pendentes e os jogados (só quando há os dois)
      const hasP=koEntries.some(e=>e.m.status!=='finished'), hasD=koEntries.some(e=>e.m.status==='finished');
      let koRows='', div=false;
      for(const e of koEntries){
        if(hasP && hasD && !div && e.m.status==='finished'){
          koRows+='<div style="font-size:10.5px;color:var(--ink-faint);text-transform:uppercase;letter-spacing:.6px;margin:11px 0 5px">— já encerrados —</div>';
          div=true;
        }
        koRows+=maPickRow(e);
      }
      h+=`<div class="ma-sec"><h4>🏆 Meus palpites — mata-mata <span style="float:right;color:var(--gold);font-weight:700;font-size:13px">+${koPts} pts</span></h4>
        ${koRows}${koBtn}</div>`;
    }
    const entries=Object.entries(picks.groups||{}).map(([mid,a])=>({mid,m:mm[mid],ph:a[0],pa:a[1],pts:a[2]}))
      .filter(e=>e.m).sort((a,b)=> new Date(a.m.kickoff_sao_paulo||0)-new Date(b.m.kickoff_sao_paulo||0));
    const played=entries.filter(e=>e.m.status==='finished');
    const upcoming=entries.filter(e=>e.m.status!=='finished');
    // fim da 1ª fase (nada mais a jogar): cai pra "Já jogados" pra não abrir numa aba vazia
    if(maTab==='upcoming' && !upcoming.length && played.length) maTab='played';
    const list=maTab==='played'?played:upcoming;
    h+=`<div class="ma-sec"><h4>⚽ Meus palpites — fase de grupos</h4>
      <div class="ma-tabs" id="maTabs">
        <button class="ma-tab ${maTab==='upcoming'?'active':''}" data-t="upcoming">A jogar (${upcoming.length})</button>
        <button class="ma-tab ${maTab==='played'?'active':''}" data-t="played">Já jogados (${played.length})</button>
      </div>${list.length?list.map(maPickRow).join(''):'<div class="ma-pend">Nada nesta aba ainda.</div>'}</div>`;

    const rf=DATA.final_result||{}, fr=picks.final||{};
    h+=`<div class="ma-sec"><h4>🏆 Minha classificação final</h4>`+
      [['champion','Campeã',15],['vice','Vice',10],['third','3º lugar',5]].map(([k,lab,pt])=>{
        const g=fr[k]||'—'; const real=rf[k];
        const mark = (real!==null&&real!==undefined&&real!=='')
          ? (maNorm(real)===maNorm(g)?`<span class="ma-ok">✓ +${pt} · você cravou!</span>`:'<span class="ma-pend">não veio 😅</span>')
          : '<span class="ma-pend">a definir</span>';
        return `<div class="ma-final-row"><span><span class="pos">${lab}:</span> ${g!=='—'?flag(g):''}${esc(g)}</span>${mark}</div>`;
      }).join('')+`</div>`;

    const exVals=picks.extras||{};
    const exRows=EXTRAS_DEF.map(d=>{
      const g=exVals[d.key];
      if(g===null||g===undefined||g==='') return '';
      const fact=(DATA.extras_summary||[]).find(x=>x.key===d.key);
      const real=fact?fact.real:null;
      let mark='<span class="ma-pend">a definir</span>';
      if(real!==null&&real!==undefined&&real!==''){
        // usa a MESMA lista de vencedores já calculada no motor (fact.winners, list-aware p/
        // empate) em vez de recomparar string aqui — evita divergir do card agregado de Extras
        // quando o real é um EMPATE ("Empate: A, B, C"): comparar a string toda contra o palpite
        // individual (ex. "Austrália") nunca bateria, mesmo pra quem realmente cravou.
        const cravou=(fact.winners||[]).includes(p.alias);
        mark=cravou
          ? `<span class="ma-ok">✓ +${d.points} · você cravou!</span>`
          : '<span class="ma-pend">não veio dessa vez 😅</span>';
      } else if(fact&&fact.partial){
        // "no páreo" SÓ com match confiante (palpite nomeado aparece no parcial); nunca afirma
        // "fora" (um líder pode estar truncado). Pula palpite numérico (substring de número engana).
        const gs=String(g).trim(), num=/^\d+$/.test(gs);
        const alive = !num && gs.length>=3 && maNorm(fact.partial).includes(maNorm(gs));
        mark = alive ? '<span class="ma-ok">📡 no páreo</span>' : '<span class="ma-pend">📡 em disputa</span>';
      }
      return `<div class="ma-final-row"><span><span class="pos">${d.label}</span><br>${esc(String(g))}</span>${mark}</div>`;
    }).filter(Boolean).join('');
    h+=`<div class="ma-sec"><h4>🎯 Minhas categorias extras</h4>${exRows||'<div class="ma-pend">Sem categorias preenchidas.</div>'}</div>`;
  }
  card.innerHTML=h;
}

function maSelect(alias){
  maSelected=alias; maTab='upcoming';
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
    ? hits.map(p=>`<div class="ma-sugg" data-a="${esc(p.alias)}"><span>${esc(p.alias)}</span><span class="r">${p.rank}º</span></div>`).join('')
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

// rotating tagline
let ti=0; const tEl=document.getElementById('tagline');
// Frases da LANTERNA: dinâmicas — usam o último colocado ATUAL. textContent (sem risco XSS).
const LANTERNA_LINES = [
  "🔦 {x} brilhando na lanterna: luz própria.",
  "🔦 Temos campeão da lanterna: {x}. O bolão todo torce… pra você ficar.",
  "🔦 {x} de novo na lanterna? Já dá pra pagar aluguel."
];
function taglinePool(){
  const pool = [...TAGLINES];
  const P = DATA.participants || [];
  if(P.length){
    const last = [...P].sort((a,b)=> (b.rank-a.rank) || (a.score-b.score))[0];
    if(last && last.alias) LANTERNA_LINES.forEach(t => pool.push(t.replace('{x}', last.alias)));
  }
  return pool;
}
function rotate(){ const pool=taglinePool(); tEl.textContent = pool[ti % pool.length]; ti++; }
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
let lastStamp=null;
// Auto-refresh AO VIVO: rebusca o data.json e só redesenha quando o robô publicou algo novo
// (compara meta.last_data_update). Preserva a aba de jogos e pausa enquanto você digita na
// busca/Minha Aposta, pra não atrapalhar. lbFilter/lbSearch/lbExpanded, maSelected e pelLens
// são variáveis de módulo → o render() já os mantém.
async function refreshData(){
  checkFreshness();   // atualiza o selo de frescura mesmo quando não há dado novo (badge de atraso)
  const ae=document.activeElement;
  if(ae && (ae.id==='lbSearch' || ae.id==='maInput')) return;   // não interrompe digitação
  let live=null;
  try{
    const got=await Promise.all(DATA_SOURCES.map(async src=>{
      try{ const r=await fetch(src+'?ts='+Date.now(),{cache:'no-store'}); if(r.ok) return await r.json(); }catch(e){}
      return null;
    }));
    live=got.filter(Boolean).sort((a,b)=> new Date(b.meta?.last_data_update||0)-new Date(a.meta?.last_data_update||0))[0]||null;
  }catch(e){ return; }
  if(!live) return;
  const stamp=live.meta && live.meta.last_data_update;
  if(!stamp || stamp===lastStamp) return;          // nada novo → não mexe na tela
  lastStamp=stamp;
  DATA=live;
  if(Array.isArray(live.history)) HISTORY.splice(0, HISTORY.length, ...live.history);
  const tab=document.querySelector('#matchTabs .tab.active')?.dataset.f;   // única coisa que o render() reseta
  render();
  if(tab){ document.querySelectorAll('#matchTabs .tab').forEach(t=>t.classList.toggle('active',t.dataset.f===tab)); renderMatches(tab); }
}
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
      PRECOPA = live;                                   // passa a refletir os dados reais
      if(Array.isArray(live.history)) HISTORY.splice(0, HISTORY.length, ...live.history);
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
  lastStamp = (DATA.meta && DATA.meta.last_data_update) || null;
  startLivePolling();   // ao vivo de verdade (ESPN direto) por cima do dado do robô
  setInterval(refreshData, 30000);  // a cada 30s: pega os dados novos do robô (final/pontos) rápido, sem reload
}
boot();
