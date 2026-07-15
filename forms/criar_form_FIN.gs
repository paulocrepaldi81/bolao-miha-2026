/**
 * BOLÃO MIHA 2026 — Gerador do Google Form da FINAL + DISPUTA DE 3º LUGAR (rodada "FIN")
 * ---------------------------------------------------------------------------------------
 * Cópia fiel do criar_form_QF.gs — com uma diferença importante: Final e Disputa de 3º Lugar
 * têm o MESMO prazo (jogam no mesmo fim de semana), então vêm JUNTAS neste ÚNICO Form.
 *
 * IMPORTANTE PRO ROBÔ: "Jogo 1" deste Form = a FINAL (slot "FIN"); "Jogo 2" = a Disputa de
 * 3º Lugar (slot "TER"). engine/knockout.py::parse_form_csv já trata a rodada "FIN" como caso
 * especial exatamente por isso — NÃO troque a ordem dos 2 jogos abaixo.
 *
 * Os 2 confrontos já são reais e DEFINITIVOS (chaveamento fechado, conferido em
 * engine/data/knockout_bracket.json): Espanha×Argentina (Final) e França×Inglaterra ⭐
 * (3º lugar, especial). Os 2 jogos começam depois do meio-dia de 18/07 (o prazo) — TER tem 6h
 * de folga (18h), FIN quase 28h (19/07 16h) — conferido com o painel de agentes, sem exceção
 * de slot_deadlines necessária. PRONTO PRA RODAR, sem editar nada.
 *
 * COMO USAR (leva ~3 min):
 *  1) Abra https://script.google.com  ->  Novo projeto.
 *  2) Apague tudo e cole ESTE arquivo inteiro (os 2 jogos já estão prontos, sem editar nada).
 *  3) Menu: Executar -> criarFormularioFIN. Autorize quando pedir.
 *  4) No painel "Registros de execução" vão aparecer 3 links: PUBLICO (mandar no zap),
 *     EDITAR (seu) e PLANILHA (respostas). Guarde os três.
 *  5) >>> IMPORTANTÍSSIMO <<< na PLANILHA de respostas: Arquivo -> Configurações ->
 *     Fuso horário -> (GMT-03:00) São Paulo. Faça 1 envio de teste e confira que o
 *     carimbo bate com a hora real de Brasília. (Se o fuso estiver errado, o robô
 *     descarta apostas legítimas em silêncio — é o risco nº1.)
 *  6) Na planilha: Arquivo -> Compartilhar -> Publicar na web -> aba de respostas +
 *     "Valores separados por vírgula (.csv)" -> Publicar. Copie a URL .csv e me mande
 *     (junto com o link PÚBLICO), pra eu ligar a rodada FIN no knockout_forms.json.
 *
 * REGRA DE PRAZO (RUNBOOK-fases.md): prazo ÚNICO — Final E 3º lugar fecham SÁBADO 18/07 AO
 * MEIO-DIA (12h, GMT-3, Brasília) — meio-dia do próprio dia do 1º jogo dessa rodada, mesma
 * regra usada desde as Quartas. É a ÚLTIMA atualização de palpites da Copa inteira.
 */

// ====== EDITE AQUI (só se precisar) ======
var FASE = 'Mata-mata · Final e Disputa de 3º Lugar';

// Pasta do Google Drive onde o Form e a planilha de respostas serão salvos (a mesma das fases anteriores).
var PASTA_ID = '16F9MjNdz7dIZqmbZjNOSxCEkj1K9-nph';

// Confrontos REAIS — Jogo 1 = FINAL (slot "FIN"), Jogo 2 = 3º LUGAR (slot "TER"). Os 2 já são
// definitivos (chaveamento fechado). NÃO troque a ordem — é o que casa com FIN/TER no robô.
var MATCHES = [
  { n: 1, home: 'Espanha', away: 'Argentina',   quando: '19/07 · 16h00' },   // FIN
  { n: 2, home: 'França',  away: 'Inglaterra',  quando: '18/07 · 18h00' },   // TER (⭐ especial)
];

// 88 apostas (apelidos). Cada aposta = 1 envio. Quem tem mais de uma, preenche 1 vez por apelido.
var ALIASES = [
  'Andrei Mitev','André Melaragno','André Pires','Beto Ribeiro I','Beto Ribeiro II','Charles Miller',
  'Clarinha','Claudio Pasqualin 1','Claudio Pasqualin 2','Dani Cleim','Daniel Villar','Fabio Terzian','FB',
  'Felipe Tadeu','Fernando Mihalik','Fla Mihalik','Pelé','Fred Paz','Gab Miha Crep','Gilvan','Glauco Marcondes',
  'Grazi Marcondes','Gual Lencina','Guilherme Marcondes','Guiherme Reis','Inimigo do Acerto','Ivana Dalla Zanna',
  'João Mihalik','João Sergio','Laura Mihalik','Leonardo Reis - Hexa Vem Aí','Leonardo Reis - Zebra','Luis Luengo',
  'Maradona','Marcelo Morganti','Marcio Lauria 1','Marcio Lauria 2','Marcio Lauria 3','Marina Mihalik',
  'Melhor Amigo do Fred','Melhor Inimigo do Fred','Mengão Malvadão','MENGÃO TETRA','MENGO AREQUIPA','Miha88',
  'MMIFLY','MP68','Nando Lorris','Náro','Nelson Reis','Pati Mihalik','Paulo Ciasca','Paulo Crepaldi - Cenário B',
  'Paulo Crepaldi - Codex','Pedro Mitev 1','Pedro Mitev 2','Pedro Marcondes','PereiraB','PereiraP','Ponti FC',
  'Profeta da Copa','Profeta','Puglia','Rabelo','Rafael Garcia','Rebecca Marcondes','Reinaldo Ribeiro',
  'Renato Kassab','Renato Pasqualin','Ric Mel','Ricardo Mihalik','Rmorganti','Roberto Mihalik','Ruy Monaco',
  'San Lencina','SD','Signor Panini','Só Te Vejo pelo Retrovisor','Tacito Andrade','Theo Reis',
  'Thiago Profili 1860','Thiago Profili 1910','Thiago Rosa','Tiago Okamoto','Ticão','VARíola dos Palpites',
  'Vitor e Dani','Zé Artur'
];

// ====== NÃO precisa editar daqui pra baixo ======

function _scorelines() {
  // Lista única por jogo: "Manter original" no topo, depois TODOS os placares até 8×8,
  // ordenados por total de gols (os placares comuns de mata-mata aparecem primeiro → quase
  // ninguém precisa rolar). Cobre qualquer resultado realista — sem "Outro placar".
  var out = ['Manter meu palpite original'];
  var combos = [];
  for (var h = 0; h <= 8; h++) {
    for (var a = 0; a <= 8; a++) { combos.push([h, a]); }
  }
  combos.sort(function (x, y) {
    return (x[0] + x[1]) - (y[0] + y[1]) || y[0] - x[0];   // menor total primeiro; mandante na frente
  });
  combos.forEach(function (c) { out.push(c[0] + ' × ' + c[1]); });
  return out;
}

function criarFormularioFIN() {
  var form = FormApp.create('Bolão Miha 2026 — ' + FASE);
  form.setDescription(
    '🏆 CHEGAMOS À FINAL! Última chance de mudar (ou manter) seus palpites — Final E Disputa de ' +
    '3º Lugar vêm juntas aqui, já que fecham no mesmo prazo.\n\n' +
    '✅ Para cada jogo, escolha o placar OU deixe "Manter meu palpite original". O que você NÃO mexer ' +
    'fica com o placar que você já tinha na sua aposta da planilha — ou seja, NÃO precisa preencher tudo, ' +
    'só o que quiser mudar.\n\n' +
    '⏰ PRAZO: os dois jogos fecham SÁBADO 18/07 AO MEIO-DIA (12h) — GMT-3, Brasília. Última ' +
    'atualização de palpites da Copa inteira! Pode reenviar quantas vezes quiser até lá: vale o ' +
    'último envio dentro do prazo.\n\n' +
    '📝 Tem mais de uma aposta? Preencha UM formulário para cada apelido.\n\n' +
    '⚽ Os placares contam até o FIM DA PRORROGAÇÃO — pênaltis não dão pontos (só decidem quem é campeão).'
  );
  form.setCollectEmail(false);
  form.setAllowResponseEdits(true);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(true);

  // Identificação — APELIDO primeiro (é A APOSTA, é o que o robô usa)
  form.addListItem().setTitle('1) Sua aposta (escolha seu APELIDO)')
    .setHelpText('Esta é a sua APOSTA. Tem mais de uma? Preencha um formulário para cada apelido. ' +
                 'Na dúvida, é o nome que aparece na planilha do bolão.')
    .setChoiceValues(ALIASES).setRequired(true);
  form.addTextItem().setTitle('2) Seu nome (só pra eu conferir)').setRequired(true);

  // Jogo 1 = FINAL, Jogo 2 = 3º LUGAR — nessa ordem exata (casa com os slots FIN/TER no robô)
  var sl = _scorelines();
  MATCHES.forEach(function (m) {
    var rotulo = m.n === 1 ? 'FINAL' : 'Disputa de 3º Lugar';
    form.addListItem()
      .setTitle('Jogo ' + m.n + ' — ' + rotulo + ': ' + m.home + ' × ' + m.away)
      .setHelpText('Placar ' + m.home + ' (casa) × ' + m.away + '. Fecha sáb 18/07 ao meio-dia (GMT-3). ' +
                   'Em branco ou "Manter meu palpite original" = fica com seu palpite original.')
      .setChoiceValues(sl)
      .setRequired(false);
  });

  // Conferência final — força um segundo olhar
  form.addCheckboxItem().setTitle('Confirmação')
    .setChoiceValues(['Conferi meus palpites e quero enviar.']).setRequired(true);

  form.setConfirmationMessage(
    '✅ Recebido! Seus palpites da Final e do 3º Lugar estão salvos.\n' +
    'Quer mudar algo antes de sábado 18/07 ao meio-dia? Use o MESMO link e edite sua resposta — vale a última.\n' +
    'Tem outra aposta? Preencha de novo com o outro apelido.\n\n' +
    '🏆 Boa sorte até o fim da Copa!'
  );

  // Planilha de respostas
  var ss = SpreadsheetApp.create('Bolão Miha 2026 — Respostas ' + FASE);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // Move o formulário E a planilha de respostas para a sua pasta do Drive.
  var pasta = DriveApp.getFolderById(PASTA_ID);
  DriveApp.getFileById(form.getId()).moveTo(pasta);
  DriveApp.getFileById(ss.getId()).moveTo(pasta);

  Logger.log('================ LINKS (guarde os três) ================');
  Logger.log('PASTA do Drive:         ' + pasta.getUrl());
  Logger.log('PUBLICO (mande no zap): ' + form.getPublishedUrl());
  Logger.log('EDITAR (seu):           ' + form.getEditUrl());
  Logger.log('PLANILHA (respostas):   ' + ss.getUrl());
  Logger.log('>>> AJUSTE O FUSO DA PLANILHA para (GMT-03:00) São Paulo e faça 1 envio de teste! <<<');
  Logger.log('Depois: PLANILHA -> Arquivo -> Compartilhar -> Publicar na web -> aba de respostas + CSV -> Publicar. Mande a URL .csv + o link PUBLICO.');
}
