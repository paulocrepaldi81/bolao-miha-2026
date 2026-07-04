/**
 * BOLÃO MIHA 2026 — Gerador do Google Form do MATA-MATA (R16 / OITAVAS de final)
 * ---------------------------------------------------------------------------------------
 * Cópia fiel do criar_form_R32.gs — só mudaram FASE, os 8 confrontos e o texto do prazo.
 *
 * COMO USAR (leva ~3 min):
 *  1) Abra https://script.google.com  ->  Novo projeto.
 *  2) Apague tudo e cole ESTE arquivo inteiro. (As 8 oitavas já estão preenchidas e definitivas.)
 *  3) Menu: Executar -> criarFormularioR16. Autorize quando pedir.
 *  4) No painel "Registros de execução" vão aparecer 3 links: PUBLICO (mandar no zap),
 *     EDITAR (seu) e PLANILHA (respostas). Guarde os três.
 *  5) >>> IMPORTANTÍSSIMO <<< na PLANILHA de respostas: Arquivo -> Configurações ->
 *     Fuso horário -> (GMT-03:00) São Paulo. Faça 1 envio de teste e confira que o
 *     carimbo bate com a hora real de Brasília. (Se o fuso estiver errado, o robô
 *     descarta apostas legítimas em silêncio — é o risco nº1.)
 *  6) Na planilha: Arquivo -> Compartilhar -> Publicar na web -> aba de respostas +
 *     "Valores separados por vírgula (.csv)" -> Publicar. Copie a URL .csv e me mande
 *     (junto com o link PÚBLICO), pra eu ligar a rodada R16 no knockout_forms.json.
 *
 * Os confrontos já vêm com as SELEÇÕES REAIS das oitavas, na ordem/mando dos slots R16-01..08.
 * NÃO reordene os jogos (o "Jogo N" tem que casar com o slot R16-NN).
 *
 * REGRA DE PRAZO (combinada): prazo ÚNICO — todas as oitavas fecham SÁBADO 04/07 ÀS 13H (GMT-3, Brasília)
 * (antes do 1º jogo, que é 14h). Quem não mexer num jogo (branco ou "Manter meu palpite original")
 * fica com o placar da APOSTA ORIGINAL da planilha. A trava real é feita pelo robô.
 */

// ====== EDITE AQUI (só se precisar) ======
var FASE = 'Mata-mata · Oitavas de final';

// Pasta do Google Drive onde o Form e a planilha de respostas serão salvos (a mesma do R32).
var PASTA_ID = '16F9MjNdz7dIZqmbZjNOSxCEkj1K9-nph';

// Confrontos REAIS das oitavas — ordem = slot R16-NN, home = mandante (orientação do bracket).
// Os 8 já estão definitivos (o R32 encerrou; Colômbia bateu Gana e pegou a Suíça no Jogo 8).
var MATCHES = [
  { n: 1, home: 'Paraguai',   away: 'França',          quando: '04/07 · 18h00' }, // R16-01
  { n: 2, home: 'Canadá',     away: 'Marrocos',        quando: '04/07 · 14h00' }, // R16-02 (⭐ especial)
  { n: 3, home: 'Portugal',   away: 'Espanha',         quando: '06/07 · 16h00' }, // R16-03
  { n: 4, home: 'EUA',        away: 'Bélgica',         quando: '06/07 · 21h00' }, // R16-04 (⭐ especial)
  { n: 5, home: 'Brasil',     away: 'Noruega',         quando: '05/07 · 17h00' }, // R16-05
  { n: 6, home: 'México',     away: 'Inglaterra',      quando: '05/07 · 21h00' }, // R16-06 (⭐ especial)
  { n: 7, home: 'Argentina',  away: 'Egito',           quando: '07/07 · 13h00' }, // R16-07
  { n: 8, home: 'Suíça',      away: 'Colômbia',        quando: '07/07 · 17h00' }, // R16-08 (⭐ especial)
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

function criarFormularioR16() {
  var form = FormApp.create('Bolão Miha 2026 — ' + FASE);
  form.setDescription(
    '🏆 Chegamos às OITAVAS! Agora é mata-mata puro. Você pode mudar (ou manter) seus palpites.\n\n' +
    '✅ Para cada jogo, escolha o placar OU deixe "Manter meu palpite original". O que você NÃO mexer ' +
    'fica com o placar que você já tinha na sua aposta da planilha — ou seja, NÃO precisa preencher tudo, ' +
    'só o que quiser mudar.\n\n' +
    '⏰ PRAZO: todas as oitavas fecham SÁBADO 04/07 ÀS 13H — GMT-3, Brasília (antes do 1º jogo, 14h). Pode reenviar ' +
    'quantas vezes quiser até lá: vale o último envio dentro do prazo.\n\n' +
    '📝 Tem mais de uma aposta? Preencha UM formulário para cada apelido.\n\n' +
    '⚽ Os placares contam até o FIM DA PRORROGAÇÃO — pênaltis não dão pontos.'
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

  // Os 8 jogos — nomes reais + data/hora; em branco = mantém o original
  var sl = _scorelines();
  MATCHES.forEach(function (m) {
    form.addListItem()
      .setTitle('Jogo ' + m.n + ' — ' + m.home + ' × ' + m.away)
      .setHelpText('Placar ' + m.home + ' (casa) × ' + m.away + '. Fecha sáb 04/07 às 13h (GMT-3). ' +
                   'Em branco ou "Manter meu palpite original" = fica com seu palpite original.')
      .setChoiceValues(sl)
      .setRequired(false);
  });

  // Conferência final — força um segundo olhar
  form.addCheckboxItem().setTitle('Confirmação')
    .setChoiceValues(['Conferi meus palpites e quero enviar.']).setRequired(true);

  form.setConfirmationMessage(
    '✅ Recebido! Seus palpites das oitavas estão salvos.\n' +
    'Quer mudar algo antes de sábado às 13h? Use o MESMO link e edite sua resposta — vale a última.\n' +
    'Tem outra aposta? Preencha de novo com o outro apelido.'
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
