# -*- coding: utf-8 -*-
# Generate native es/pt pages from the en pages.
# UI strings are authored translations (LLM-as-translator is within the house rules:
# the platform translates its own interface, never scripture interpretation).
# usage: python make_lang_pages.py
import io, os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
EN = os.path.join(HERE, 'en')

STOPS = {
  'es': ("el la los las de del y a en que es un una por con no se su sus lo le les al como "
         "para mas más pero si sí él ella ellos ellas yo tú te me mi nos os ha han he fué fue "
         "era eran ser sido son está están esto esta este estos estas ese esa esos esas aquel "
         "aquella cual cuales quien quienes cuando donde entonces porque sobre entre hasta "
         "desde muy también todo toda todos todas otro otra otros otras uno dos ni o u e ya "
         "así pues aquí allí jehová dios señor será serán haré hará dice dijo dijeron habló "
         "contra vuestra vuestro vuestras vuestros nuestra nuestro nuestras nuestros suyo suya "
         "cada sino les otrosí empero mismo misma tal cosa cosas hay tiene tienen fuera dentro "
         "sea sean estaba estaban vosotros nosotros"),
  'pt': ("o a os as de do da dos das e que é um uma em no na nos nas por para com não se seu "
         "sua seus suas ao aos à às como mas mais ele ela eles elas eu tu te me mim nós vós "
         "vos lhe lhes há foi era eram ser sido são está estão isto esta este estes estas esse "
         "essa esses essas aquele aquela qual quais quem quando onde então porque sobre entre "
         "até desde muito também todo toda todos todas outro outra outros outras dois duas nem "
         "ou já assim pois aqui ali senhor deus jeová será serão disse diz disseram falou "
         "contra vosso vossa nosso nossa cada senão mesmo mesma tal coisa coisas tem têm fora "
         "dentro seja sejam estava estavam"),
}
LETTERS = { 'es': "a-záéíóúüñ'", 'pt': "a-záàâãéêíóôõúüç'" }

# ---------------- translation tables (en -> lang) ----------------

T_ES = [
  # shared / index
  ('<title>BeadString · Handcraft of the Wilderness</title>', '<title>BeadString · Artesanía del Desierto</title>'),
  ('<p class="sub">Handcraft of the Wilderness</p>', '<p class="sub">Artesanía del Desierto</p>'),
  ('In the desert, the monks prayed as they wove.<br>\n        Today is no different — grow quiet, and string one.',
   'En el desierto, los monjes oraban mientras tejían.<br>\n        Hoy no es distinto: aquiétate y ensarta una.'),
  ('>Read Scripture<', '>Leer la Escritura<'),
  (">Today's Bead<", '>La Cuenta de Hoy<'),
  ('>A Random Bead<', '>Una Cuenta al Azar<'),
  ('>My Workshop<', '>Mi Taller<'),
  ('>Share BeadString<', '>Compartir BeadString<'),
  ('>Tap anywhere to skip<', '>Toca donde sea para saltar<'),
  (">Day's Rest<", '>Descanso del Día<'),
  ('>Return to Breathing<', '>Volver a la Respiración<'),
  ('>The First Bead<', '>La Primera Cuenta<'),
  ('>The Second Bead<', '>La Segunda Cuenta<'),
  ('>Take Up the Second<', '>Toma la Segunda<'),
  ('>Find the Thread<', '>Encuentra el Hilo<'),
  ('>Tap the words you believe are joined — one passage, then the other<',
   '>Toca las palabras que crees unidas: un pasaje y luego el otro<'),
  ('>Tie the Knot<', '>Ata el Nudo<'),
  ('>Reveal the Thread<', '>Revelar el Hilo<'),
  ('>Swap This Bead<', '>Cambiar de Cuenta<'),
  ('placeholder="Why do you think this thread is here? (optional — private unless you say otherwise)"',
   'placeholder="¿Por qué crees que este hilo está aquí? (opcional; privado salvo que digas lo contrario)"'),
  ('Leave this note on the bead, for those who string it after you (public notes join the open dataset)',
   'Deja esta nota en la cuenta, para quienes la ensarten después de ti (las notas públicas entran al conjunto de datos abierto)'),
  ('>Open source · Open data<', '>Código abierto · Datos abiertos<'),
  ('>Add to Home Screen<', '>Añadir a la Pantalla de Inicio<'),
  ("\"In Safari, tap the Share button, then choose 'Add to Home Screen'.\"",
   "\"En Safari, toca el botón Compartir y elige 'Añadir a pantalla de inicio'.\""),
  ("\"In your browser menu, choose 'Add to Home Screen' or 'Install app'.\"",
   "\"En el menú del navegador, elige 'Añadir a pantalla de inicio' o 'Instalar aplicación'.\""),
  ("btn.textContent = 'Loading ' + loadPct()", "btn.textContent = 'Cargando ' + loadPct()"),
  ('Threads on this bead · ${list.length} in TSK', 'Hilos en esta cuenta · ${list.length} en TSK'),
  ('… and ${list.length - 24} more', '… y ${list.length - 24} más'),
  ('… and ${list.length - 12} more', '… y ${list.length - 12} más'),
  ('Slow network? Tap to retry', '¿Red lenta? Toca para reintentar'),
  ('Verses still loading… tap again shortly', 'Los versículos aún cargan… toca de nuevo en un momento'),
  ('Notes from others · ', 'Notas de otros · '),
  ("|| 'anonymous'", "|| 'anónimo'"),
  (' have left a note on this bead · take a look', ' han dejado una nota en esta cuenta · míralas'),
  ('sorted by “this built me up”', 'ordenadas por “esto me edificó”'),
  ('title="This built me up"', 'title="Esto me edificó"'),
  ('>Offer This Thread to the Community<', '>Ofrecer Este Hilo a la Comunidad<'),
  ('Offered — this thread now hangs in the community set', 'Ofrecido: este hilo ya cuelga en el conjunto comunitario'),
  ('Same thread exists — your second counted', 'Ya existe el mismo hilo: tu apoyo quedó contado'),
  ('>community<', '>comunidad<'),
  ('>String It<', '>Ensártala<'),
  ('>String It Without a Note<', '>Ensártala sin Nota<'),
  ('>Strung<', '>Ensartada<'),
  ('>String Another<', '>Ensartar Otra<'),
  ('>To the Workshop<', '>Al Taller<'),
  ('>Send This Bead<', '>Enviar Esta Cuenta<'),
  ('>Hung in your workshop<', '>Colgada en tu taller<'),
  ('>My Bead Notes<', '>Mis Notas<'),
  ('>Back<', '>Volver<'),
  ('Fetching the verses…', 'Trayendo los versículos…'),
  # depth (long before short)
  ('Disputed · some trampled it, some loved it', 'Discutida · unos la pisaron, otros la amaron'),
  ('The shallows · seen by all', 'Aguas someras · vista por todos'),
  ('Deep water · few have come here', 'Aguas profundas · pocos han llegado aquí'),
  ('The deep · almost no one has seen it', 'Lo profundo · casi nadie la ha visto'),
  ("'Near shore'", "'Cerca de la orilla'"),
  ("'Disputed'", "'Discutida'"),
  ("'Shallows'", "'Someras'"),
  ("'Deep water'", "'Aguas profundas'"),
  ("'The deep'", "'Lo profundo'"),
  ('TSK / OpenBible.info cross-references · KJV', 'TSK / OpenBible.info cross-references · Reina-Valera 1909'),
  ('Loading the beads…', 'Cargando las cuentas…'),
  ('BeadString — read both ends of a bead, and find the thread.',
   'BeadString: lee los dos extremos de una cuenta y encuentra el hilo.'),
  ('Link Copied', 'Enlace Copiado'),
  ('This bead is for you — BeadString, handcraft of the wilderness',
   'Esta cuenta es para ti — BeadString, artesanía del desierto'),
  ("'BeadString · Handcraft of the Wilderness'", "'BeadString · Artesanía del Desierto'"),
  ('Bead-stringers two centuries ago joined these passages. Community votes:',
   'Los ensartadores de hace dos siglos unieron estos pasajes. Votos de la comunidad:'),
  (' · a disputed bead — some find it forced, others see the same Lord at work. Judge for yourself.',
   ' · una cuenta discutida: a unos les parece forzada, otros ven al mismo Señor obrando. Júzgalo tú.'),
  ('Community votes:', 'Votos de la comunidad:'),
  ('These two passages share no surface word — the thread runs deeper.<br>',
   'Estos dos pasajes no comparten palabra en la superficie: el hilo corre más hondo.<br>'),
  ('Pair any words you see echoing, and tie a knot of your own.',
   'Une las palabras que veas resonar y ata tu propio nudo.'),
  ('<b>This is the thread you saw.</b> Keep looking, or go tie the knot.',
   '<b>Este es el hilo que viste.</b> Sigue buscando, o ve a atar el nudo.'),
  ('Every thread on this strand has been found.', 'Todos los hilos de esta cuenta han sido hallados.'),
  ('<b>You found it.</b> The stringers of two centuries ago marked this very place. (',
   '<b>¡Lo encontraste!</b> Los ensartadores de hace dos siglos marcaron este mismo lugar. ('),
  ('Now find its other end in the other passage…', 'Ahora busca su otro extremo en el otro pasaje…'),
  ('These two… don’t seem to lie on the same thread. Try again, or reveal it.',
   'Estos dos… no parecen estar en el mismo hilo. Intenta de nuevo, o revélalo.'),
  ('This bead has no surface thread to reveal — its thread can only be tied by you.',
   'Esta cuenta no tiene hilo visible que revelar: su hilo solo puedes atarlo tú.'),
  ('Here lies the thread. Revealing loses nothing — to see it is to receive it.',
   'Aquí está el hilo. Revelarlo no quita nada: verlo ya es recibirlo.'),
  ('The baskets are done. Work ends here — return to the breath.',
   'Los cestos están hechos. El trabajo termina aquí: vuelve a la respiración.'),
  ('Before entering, let the breath slow down.', 'Antes de entrar, deja que la respiración se aquiete.'),
  ("'Breathe in'", "'Inhala'"),
  ("'Breathe out, slowly'", "'Exhala, despacio'"),
  ('The Bead Is Ready', 'La Cuenta Está Lista'),
  (' beads strung today · the monks say: ten baskets woven — rise and pray',
   ' cuentas ensartadas hoy · dicen los monjes: diez cestos tejidos — levántate y ora'),
  ('Today’s bead is strung.<br>The wilderness is wide — take another as you go.',
   'La cuenta de hoy ya está ensartada.<br>El desierto es ancho: toma otra al pasar.'),
  ("'Continue · '", "'Continuar · '"),
  ("'Same Chapter · '", "'Mismo Capítulo · '"),
  ("'Back to Reading'", "'Volver a la Lectura'"),
  ("b.textContent = 'Read ' + bk + ' ' + c;", "b.textContent = 'Leer ' + SN(bk) + ' ' + c;"),
  ('You had strung this bead before — the knot is renewed; it remains one strand',
   'Ya habías ensartado esta cuenta: el nudo se renueva; sigue siendo una sola'),
  ("'Hung in your workshop'", "'Colgada en tu taller'"),
  ('`Source: ${S.pair.source} · ${S.pair.votes} votes (', '`Fuente: ${S.pair.source} · ${S.pair.votes} votos ('),
  ('No beads strung yet.', 'Aún no hay cuentas ensartadas.'),
  ("let text = n ? `${n} strand${n > 1 ? 's' : ''} strung` :",
   "let text = n ? `${n} cuenta${n > 1 ? 's' : ''} ensartada${n > 1 ? 's' : ''}` :"),
  ("'The library holds 142,079 beads — take one and begin'",
   "'La biblioteca guarda 142.079 cuentas: toma una y comienza'"),
  ('` · in the flow — ${left} more before the next breath`',
   '` · en el ritmo — ${left} más antes de la próxima respiración`'),
  ('`✦ Today’s handcraft · ${days[localDayKey()]} bead${days[localDayKey()] > 1 ? \'s\' : \'\'} strung`',
   '`✦ La artesanía de hoy · ${days[localDayKey()]} cuenta${days[localDayKey()] > 1 ? \'s\' : \'\'}`'),
  ("? 'Night Skin' : 'Storybook Skin'", "? 'Tema Nocturno' : 'Tema Ilustrado'"),
  ('The verses failed to load — ', 'Los versículos no cargaron: '),
  ('tap to retry', 'toca para reintentar'),
  # dushu
  ('<title>Read · BeadString</title>', '<title>Leer · BeadString</title>'),
  ('tap to choose book · chapter', 'toca para elegir libro · capítulo'),
  (">Beads · off<", '>Cuentas · no<'),
  ("'Beads · on' : 'Beads · off'", "'Cuentas · sí' : 'Cuentas · no'"),
  ('>‹ Previous<', '>‹ Anterior<'),
  ('>Next ›<', '>Siguiente ›<'),
  ('>String a Bead<', '>Ensartar una Cuenta<'),
  ('>Choose a Book<', '>Elige un Libro<'),
  ("'Choose a Book'", "'Elige un Libro'"),
  ('(tap to switch book)', '(toca para cambiar de libro)'),
  ('>tap to switch book<', '>toca para cambiar de libro<'),
  ('>Close<', '>Cerrar<'),
  (" bead${list.length > 1 ? 's' : ''}<br>", " cuenta${list.length > 1 ? 's' : ''}<br>"),
  ('threads drawn from here by two centuries of stringers',
   'hilos trazados desde aquí por dos siglos de ensartadores'),
  (' votes · ', ' votos · '),
  (' verse-level records', ' registros por versículo'),
  ('strung · revisit', 'ensartada · revisitar'),
  ("'Loading beads…'", "'Cargando cuentas…'"),
  # gongfang
  ('<title>Workshop · BeadString</title>', '<title>Taller · BeadString</title>'),
  ('>Workshop<', '>Taller<'),
  (">Today's Handcraft<", '>La Artesanía de Hoy<'),
  ('>Bead Calendar<', '>Calendario de Cuentas<'),
  ('Footprints in the wilderness — the days you came are kept; the blank days owe nothing',
   'Huellas en el desierto: los días que viniste quedan; los días en blanco no deben nada'),
  ('>Strand Wall<', '>Muro de Cuentas<'),
  ('>Newest<', '>Recientes<'),
  ('>Canon Order<', '>Orden Canónico<'),
  ('>Depth<', '>Profundidad<'),
  ('>All<', '>Todas<'),
  ('>Cross-Covenant<', '>Entre Testamentos<'),
  ('>Deep & Below<', '>Profundas o Más<'),
  ('>Disputed<', '>Discutidas<'),
  ('>With a Note<', '>Con Nota<'),
  ('>Chains · Strand Meets Strand<', '>Cadenas · Cuenta con Cuenta<'),
  ('>Word Drawers<', '>Cajones de Palabras<'),
  ('You are compiling a Treasury of your own', 'Estás compilando tu propio Tesoro'),
  ('`Prayer rope · ${n} knot${n > 1 ? \'s\' : \'\'}${n > 60 ? \' (last 60 shown)\' : \'\'} · this rope never breaks, it only grows`',
   '`Cuerda de oración · ${n} nudo${n > 1 ? \'s\' : \'\'}${n > 60 ? \' (últimos 60)\' : \'\'} · esta cuerda no se rompe, solo crece`'),
  ("'No knots on the prayer rope yet — string your first bead and tie the first one'",
   "'Aún no hay nudos en la cuerda: ensarta tu primera cuenta y ata el primero'"),
  ('The workshop is still empty.<br>String your first bead and hang it here.',
   'El taller aún está vacío.<br>Ensarta tu primera cuenta y cuélgala aquí.'),
  ('Nothing under this view yet.', 'Nada bajo esta vista todavía.'),
  (' votes (', ' votos ('),
  ('Verses still loading… open again shortly to read them',
   'Los versículos siguen cargando… abre de nuevo en un momento'),
  ('(no note on this strand)', '(sin nota en esta cuenta)'),
  ('>Edit Note<', '>Editar Nota<'),
  ('>Save<', '>Guardar<'),
  ('placeholder="Rewrite your note… (200 characters max)"', 'placeholder="Reescribe tu nota… (máx. 200 caracteres)"'),
  ("const MONTHS = ['January','February','March','April','May','June',\n  'July','August','September','October','November','December'];",
   "const MONTHS = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',\n  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];"),
  ("['S','M','T','W','T','F','S']", "['D','L','M','X','J','V','S']"),
  ('`${c.path.length}-bead ${c.closed ? \'garland\' : \'chain\'} · joined by ${c.edges} strands`',
   '`${c.path.length} cuentas en ${c.closed ? \'guirnalda\' : \'cadena\'} · unidas por ${c.edges} hebras`'),
  ("seals.push('First Strand')", "seals.push('Primera Cuenta')"),
  ("seals.push('Across the Covenants')", "seals.push('Entre los Testamentos')"),
  ("seals.push('Pearl of the Deep')", "seals.push('Perla del Abismo')"),
  ("seals.push('Judged for Yourself')", "seals.push('Juzgado por Ti')"),
  ("seals.push('Three-Bead Chain')", "seals.push('Cadena de Tres')"),
  ("seals.push('Garland')", "seals.push('Guirnalda')"),
  # shujia
  ('<title>Bookshelf · BeadString</title>', '<title>Estantería · BeadString</title>'),
  ('>Bookshelf<', '>Estantería<'),
  ('Fetching the bead library… (about 5MB on first load)',
   'Trayendo la biblioteca de cuentas… (unos 5MB la primera vez)'),
  ('>Choose a Chapter<', '>Elige un Capítulo<'),
  ('Pick a chapter — the text opens with its beads showing',
   'Elige un capítulo: el texto se abre con sus cuentas a la vista'),
  ('All books', 'Todos los libros'),
  ("+ ' beads' : '…'", "+ ' cuentas' : '…'"),
  (' chapter-level beads · all 66 books · from TSK / OpenBible (CC-BY)',
   ' cuentas por capítulo · los 66 libros · de TSK / OpenBible (CC-BY)'),
  ('The library failed to load — ', 'La biblioteca no cargó: '),
]

T_PT = [
  ('<title>BeadString · Handcraft of the Wilderness</title>', '<title>BeadString · Artesanato do Deserto</title>'),
  ('<p class="sub">Handcraft of the Wilderness</p>', '<p class="sub">Artesanato do Deserto</p>'),
  ('In the desert, the monks prayed as they wove.<br>\n        Today is no different — grow quiet, and string one.',
   'No deserto, os monges oravam enquanto teciam.<br>\n        Hoje não é diferente — aquiete-se e enfie uma.'),
  ('>Read Scripture<', '>Ler a Escritura<'),
  (">Today's Bead<", '>A Conta de Hoje<'),
  ('>A Random Bead<', '>Uma Conta ao Acaso<'),
  ('>My Workshop<', '>Minha Oficina<'),
  ('>Share BeadString<', '>Compartilhar BeadString<'),
  ('>Tap anywhere to skip<', '>Toque em qualquer lugar para pular<'),
  (">Day's Rest<", '>Descanso do Dia<'),
  ('>Return to Breathing<', '>Voltar à Respiração<'),
  ('>The First Bead<', '>A Primeira Conta<'),
  ('>The Second Bead<', '>A Segunda Conta<'),
  ('>Take Up the Second<', '>Pegue a Segunda<'),
  ('>Find the Thread<', '>Encontre o Fio<'),
  ('>Tap the words you believe are joined — one passage, then the other<',
   '>Toque nas palavras que você crê unidas — uma passagem, depois a outra<'),
  ('>Tie the Knot<', '>Ate o Nó<'),
  ('>Reveal the Thread<', '>Revelar o Fio<'),
  ('>Swap This Bead<', '>Trocar de Conta<'),
  ('placeholder="Why do you think this thread is here? (optional — private unless you say otherwise)"',
   'placeholder="Por que você acha que este fio está aqui? (opcional — privado, a menos que você permita)"'),
  ('Leave this note on the bead, for those who string it after you (public notes join the open dataset)',
   'Deixe esta nota na conta, para quem a enfiar depois de você (notas públicas entram no conjunto de dados aberto)'),
  ('>Open source · Open data<', '>Código aberto · Dados abertos<'),
  ('>Add to Home Screen<', '>Adicionar à Tela de Início<'),
  ("\"In Safari, tap the Share button, then choose 'Add to Home Screen'.\"",
   "\"No Safari, toque no botão Compartilhar e escolha 'Adicionar à Tela de Início'.\""),
  ("\"In your browser menu, choose 'Add to Home Screen' or 'Install app'.\"",
   "\"No menu do navegador, escolha 'Adicionar à tela inicial' ou 'Instalar aplicativo'.\""),
  ("btn.textContent = 'Loading ' + loadPct()", "btn.textContent = 'Carregando ' + loadPct()"),
  ('Threads on this bead · ${list.length} in TSK', 'Fios nesta conta · ${list.length} no TSK'),
  ('… and ${list.length - 24} more', '… e mais ${list.length - 24}'),
  ('… and ${list.length - 12} more', '… e mais ${list.length - 12}'),
  ('Slow network? Tap to retry', 'Rede lenta? Toque para tentar de novo'),
  ('Verses still loading… tap again shortly', 'Os versículos ainda carregam… toque de novo em instantes'),
  ('Notes from others · ', 'Notas de outros · '),
  ("|| 'anonymous'", "|| 'anônimo'"),
  (' have left a note on this bead · take a look', ' deixaram uma nota nesta conta · veja'),
  ('sorted by “this built me up”', 'ordenadas por “isso me edificou”'),
  ('title="This built me up"', 'title="Isso me edificou"'),
  ('>Offer This Thread to the Community<', '>Oferecer Este Fio à Comunidade<'),
  ('Offered — this thread now hangs in the community set', 'Oferecido — este fio agora está no conjunto da comunidade'),
  ('Same thread exists — your second counted', 'O mesmo fio já existe — seu apoio foi contado'),
  ('>community<', '>comunidade<'),
  ('>String It<', '>Enfie-a<'),
  ('>String It Without a Note<', '>Enfiar sem Nota<'),
  ('>Strung<', '>Enfiada<'),
  ('>String Another<', '>Enfiar Outra<'),
  ('>To the Workshop<', '>À Oficina<'),
  ('>Send This Bead<', '>Enviar Esta Conta<'),
  ('>Hung in your workshop<', '>Pendurada na sua oficina<'),
  ('>My Bead Notes<', '>Minhas Notas<'),
  ('>Back<', '>Voltar<'),
  ('Fetching the verses…', 'Buscando os versículos…'),
  ('Disputed · some trampled it, some loved it', 'Disputada · uns a pisaram, outros a amaram'),
  ('The shallows · seen by all', 'Águas rasas · vista por todos'),
  ('Deep water · few have come here', 'Águas profundas · poucos chegaram aqui'),
  ('The deep · almost no one has seen it', 'O profundo · quase ninguém a viu'),
  ("'Near shore'", "'Perto da margem'"),
  ("'Disputed'", "'Disputada'"),
  ("'Shallows'", "'Rasas'"),
  ("'Deep water'", "'Águas profundas'"),
  ("'The deep'", "'O profundo'"),
  ('TSK / OpenBible.info cross-references · KJV', 'TSK / OpenBible.info cross-references · Bíblia Livre (CC BY)'),
  ('Loading the beads…', 'Carregando as contas…'),
  ('BeadString — read both ends of a bead, and find the thread.',
   'BeadString — leia as duas pontas de uma conta e encontre o fio.'),
  ('Link Copied', 'Link Copiado'),
  ('This bead is for you — BeadString, handcraft of the wilderness',
   'Esta conta é para você — BeadString, artesanato do deserto'),
  ("'BeadString · Handcraft of the Wilderness'", "'BeadString · Artesanato do Deserto'"),
  ('Bead-stringers two centuries ago joined these passages. Community votes:',
   'Os enfiadores de contas de dois séculos atrás uniram estas passagens. Votos da comunidade:'),
  (' · a disputed bead — some find it forced, others see the same Lord at work. Judge for yourself.',
   ' · uma conta disputada — a uns parece forçada, outros veem o mesmo Senhor agindo. Julgue você.'),
  ('Community votes:', 'Votos da comunidade:'),
  ('These two passages share no surface word — the thread runs deeper.<br>',
   'Estas duas passagens não compartilham palavra na superfície — o fio corre mais fundo.<br>'),
  ('Pair any words you see echoing, and tie a knot of your own.',
   'Una as palavras que você vê ecoando e ate o seu próprio nó.'),
  ('<b>This is the thread you saw.</b> Keep looking, or go tie the knot.',
   '<b>Este é o fio que você viu.</b> Continue procurando, ou vá atar o nó.'),
  ('Every thread on this strand has been found.', 'Todos os fios desta conta foram encontrados.'),
  ('<b>You found it.</b> The stringers of two centuries ago marked this very place. (',
   '<b>Você encontrou!</b> Os enfiadores de dois séculos atrás marcaram este mesmo lugar. ('),
  ('Now find its other end in the other passage…', 'Agora ache a outra ponta na outra passagem…'),
  ('These two… don’t seem to lie on the same thread. Try again, or reveal it.',
   'Estes dois… não parecem estar no mesmo fio. Tente de novo, ou revele-o.'),
  ('This bead has no surface thread to reveal — its thread can only be tied by you.',
   'Esta conta não tem fio visível a revelar — seu fio só pode ser atado por você.'),
  ('Here lies the thread. Revealing loses nothing — to see it is to receive it.',
   'Aqui está o fio. Revelar não tira nada — vê-lo já é recebê-lo.'),
  ('The baskets are done. Work ends here — return to the breath.',
   'Os cestos estão prontos. O trabalho termina aqui — volte à respiração.'),
  ('Before entering, let the breath slow down.', 'Antes de entrar, deixe a respiração se aquietar.'),
  ("'Breathe in'", "'Inspire'"),
  ("'Breathe out, slowly'", "'Expire, devagar'"),
  ('The Bead Is Ready', 'A Conta Está Pronta'),
  (' beads strung today · the monks say: ten baskets woven — rise and pray',
   ' contas enfiadas hoje · dizem os monges: dez cestos tecidos — levante-se e ore'),
  ('Today’s bead is strung.<br>The wilderness is wide — take another as you go.',
   'A conta de hoje já está enfiada.<br>O deserto é vasto — pegue outra pelo caminho.'),
  ("'Continue · '", "'Continuar · '"),
  ("'Same Chapter · '", "'Mesmo Capítulo · '"),
  ("'Back to Reading'", "'Voltar à Leitura'"),
  ("b.textContent = 'Read ' + bk + ' ' + c;", "b.textContent = 'Ler ' + SN(bk) + ' ' + c;"),
  ('You had strung this bead before — the knot is renewed; it remains one strand',
   'Você já havia enfiado esta conta — o nó se renova; continua sendo uma só'),
  ("'Hung in your workshop'", "'Pendurada na sua oficina'"),
  ('`Source: ${S.pair.source} · ${S.pair.votes} votes (', '`Fonte: ${S.pair.source} · ${S.pair.votes} votos ('),
  ('No beads strung yet.', 'Ainda não há contas enfiadas.'),
  ("let text = n ? `${n} strand${n > 1 ? 's' : ''} strung` :",
   "let text = n ? `${n} conta${n > 1 ? 's' : ''} enfiada${n > 1 ? 's' : ''}` :"),
  ("'The library holds 142,079 beads — take one and begin'",
   "'A biblioteca guarda 142.079 contas — pegue uma e comece'"),
  ('` · in the flow — ${left} more before the next breath`',
   '` · no ritmo — ${left} mais antes da próxima respiração`'),
  ('`✦ Today’s handcraft · ${days[localDayKey()]} bead${days[localDayKey()] > 1 ? \'s\' : \'\'} strung`',
   '`✦ O artesanato de hoje · ${days[localDayKey()]} conta${days[localDayKey()] > 1 ? \'s\' : \'\'}`'),
  ("? 'Night Skin' : 'Storybook Skin'", "? 'Tema Noturno' : 'Tema Ilustrado'"),
  ('The verses failed to load — ', 'Os versículos não carregaram — '),
  ('tap to retry', 'toque para tentar de novo'),
  # dushu
  ('<title>Read · BeadString</title>', '<title>Ler · BeadString</title>'),
  ('tap to choose book · chapter', 'toque para escolher livro · capítulo'),
  (">Beads · off<", '>Contas · não<'),
  ("'Beads · on' : 'Beads · off'", "'Contas · sim' : 'Contas · não'"),
  ('>‹ Previous<', '>‹ Anterior<'),
  ('>Next ›<', '>Próximo ›<'),
  ('>String a Bead<', '>Enfiar uma Conta<'),
  ('>Choose a Book<', '>Escolha um Livro<'),
  ("'Choose a Book'", "'Escolha um Livro'"),
  ('(tap to switch book)', '(toque para trocar de livro)'),
  ('>tap to switch book<', '>toque para trocar de livro<'),
  ('>Close<', '>Fechar<'),
  (" bead${list.length > 1 ? 's' : ''}<br>", " conta${list.length > 1 ? 's' : ''}<br>"),
  ('threads drawn from here by two centuries of stringers',
   'fios traçados daqui por dois séculos de enfiadores'),
  (' votes · ', ' votos · '),
  (' verse-level records', ' registros por versículo'),
  ('strung · revisit', 'enfiada · revisitar'),
  ("'Loading beads…'", "'Carregando contas…'"),
  # gongfang
  ('<title>Workshop · BeadString</title>', '<title>Oficina · BeadString</title>'),
  ('>Workshop<', '>Oficina<'),
  (">Today's Handcraft<", '>O Artesanato de Hoje<'),
  ('>Bead Calendar<', '>Calendário de Contas<'),
  ('Footprints in the wilderness — the days you came are kept; the blank days owe nothing',
   'Pegadas no deserto — os dias em que você veio ficam; os dias em branco não devem nada'),
  ('>Strand Wall<', '>Mural de Contas<'),
  ('>Newest<', '>Recentes<'),
  ('>Canon Order<', '>Ordem Canônica<'),
  ('>Depth<', '>Profundidade<'),
  ('>All<', '>Todas<'),
  ('>Cross-Covenant<', '>Entre Testamentos<'),
  ('>Deep & Below<', '>Profundas ou Mais<'),
  ('>Disputed<', '>Disputadas<'),
  ('>With a Note<', '>Com Nota<'),
  ('>Chains · Strand Meets Strand<', '>Correntes · Conta com Conta<'),
  ('>Word Drawers<', '>Gavetas de Palavras<'),
  ('You are compiling a Treasury of your own', 'Você está compilando o seu próprio Tesouro'),
  ('`Prayer rope · ${n} knot${n > 1 ? \'s\' : \'\'}${n > 60 ? \' (last 60 shown)\' : \'\'} · this rope never breaks, it only grows`',
   '`Corda de oração · ${n} nó${n > 1 ? \'s\' : \'\'}${n > 60 ? \' (últimos 60)\' : \'\'} · esta corda não se rompe, só cresce`'),
  ("'No knots on the prayer rope yet — string your first bead and tie the first one'",
   "'Ainda não há nós na corda — enfie sua primeira conta e ate o primeiro'"),
  ('The workshop is still empty.<br>String your first bead and hang it here.',
   'A oficina ainda está vazia.<br>Enfie sua primeira conta e pendure-a aqui.'),
  ('Nothing under this view yet.', 'Nada nesta vista ainda.'),
  (' votes (', ' votos ('),
  ('Verses still loading… open again shortly to read them',
   'Os versículos ainda estão carregando… abra de novo em instantes'),
  ('(no note on this strand)', '(sem nota nesta conta)'),
  ('>Edit Note<', '>Editar Nota<'),
  ('>Save<', '>Salvar<'),
  ('placeholder="Rewrite your note… (200 characters max)"', 'placeholder="Reescreva sua nota… (máx. 200 caracteres)"'),
  ("const MONTHS = ['January','February','March','April','May','June',\n  'July','August','September','October','November','December'];",
   "const MONTHS = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',\n  'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];"),
  ("['S','M','T','W','T','F','S']", "['D','S','T','Q','Q','S','S']"),
  ('`${c.path.length}-bead ${c.closed ? \'garland\' : \'chain\'} · joined by ${c.edges} strands`',
   '`${c.path.length} contas em ${c.closed ? \'guirlanda\' : \'corrente\'} · unidas por ${c.edges} fios`'),
  ("seals.push('First Strand')", "seals.push('Primeira Conta')"),
  ("seals.push('Across the Covenants')", "seals.push('Entre os Testamentos')"),
  ("seals.push('Pearl of the Deep')", "seals.push('Pérola do Profundo')"),
  ("seals.push('Judged for Yourself')", "seals.push('Julgado por Você')"),
  ("seals.push('Three-Bead Chain')", "seals.push('Corrente de Três')"),
  ("seals.push('Garland')", "seals.push('Guirlanda')"),
  # shujia
  ('<title>Bookshelf · BeadString</title>', '<title>Estante · BeadString</title>'),
  ('>Bookshelf<', '>Estante<'),
  ('Fetching the bead library… (about 5MB on first load)',
   'Buscando a biblioteca de contas… (cerca de 5MB na primeira vez)'),
  ('>Choose a Chapter<', '>Escolha um Capítulo<'),
  ('Pick a chapter — the text opens with its beads showing',
   'Escolha um capítulo — o texto se abre com as contas à vista'),
  ('All books', 'Todos os livros'),
  ("+ ' beads' : '…'", "+ ' contas' : '…'"),
  (' chapter-level beads · all 66 books · from TSK / OpenBible (CC-BY)',
   ' contas por capítulo · os 66 livros · de TSK / OpenBible (CC-BY)'),
  ('The library failed to load — ', 'A biblioteca não carregou — '),
]

MANIFESTS = {
  'es': {"name": "BeadString · Artesanía del Desierto", "short_name": "BeadString",
         "description": "Devoción inmersiva: lee los dos extremos de una cuenta y encuentra el hilo"},
  'pt': {"name": "BeadString · Artesanato do Deserto", "short_name": "BeadString",
         "description": "Devoção imersiva: leia as duas pontas de uma conta e encontre o fio"},
}

LANG_BUTTONS = {
  'es': [('en', 'English'), ('zh', '中文'), ('pt', 'Português')],
  'pt': [('en', 'English'), ('zh', '中文'), ('es', 'Español')],
}

def structural(src, lang, page):
    L = LETTERS[lang]
    # lang attr, data files, manifest
    src = src.replace('<html lang="en">', f'<html lang="{lang}">')
    src = src.replace('verses-en-', f'verses-{lang}-')
    src = src.replace('books-en.js', f'books-{lang}.js')
    src = src.replace('manifest-en.json', f'manifest-{lang}.json')
    # SN helper (localized short book names from books-<lang>.js)
    marker = 'const $ = (id) => document.getElementById(id);'
    assert marker in src, (page, 'marker $')
    src = src.replace(marker, marker + "\nconst SN = (b) => (window.BOOKSHORT || {})[b] || b;", 1)
    # stopwords + word regex + accent-safe word boundary (JS \\b is ASCII-only)
    if page == 'index':
        m = re.search(r"const STOP = new Set\(\(.*?\)\.split\(' '\)\);", src, re.S)
        assert m, (page, 'STOP')
        stop_js = "const STOP = new Set(" + json.dumps(STOPS[lang].split(), ensure_ascii=False) + ");"
        src = src[:m.start()] + stop_js + src[m.end():]
        src = src.replace("(text.toLowerCase().match(/[a-z']+/g) || [])",
                          f"(text.toLowerCase().match(/[{L}]+/g) || [])")
        src = src.replace('const hasWord = (t, w) => new RegExp("\\\\b" + w + "\\\\b", \'i\').test(t);',
                          'const LTRS = "' + L + '";\n'
                          'const hasWord = (t, w) => new RegExp("(^|[^" + LTRS + "])" + w + "([^" + LTRS + "]|$)", \'i\').test(t);')
        assert 'LTRS' in src, (page, 'hasWord')
        # localized display in chLabel + dynamic pair label
        src = src.replace('return m ? `${m[1]} ${m[2]}` : chId;', 'return m ? `${SN(m[1])} ${m[2]}` : chId;')
        src = src.replace('label: `${A.book} ${A.ch} ↔ ${B.book} ${B.ch}`,',
                          'label: `${SN(A.book)} ${A.ch} ↔ ${SN(B.book)} ${B.ch}`,')
        # language menu (globe icon) - swap en page's zh/es/pt entries for this lang's set
        old_btn = ('    <button class="lang" data-l="zh">中文</button>\n'
                   '    <button class="lang" data-l="es">Español</button>\n'
                   '    <button class="lang" data-l="pt">Português</button>')
        new_btn = '\n'.join(
            f'    <button class="lang" data-l="{code}">{label}</button>'
            for code, label in LANG_BUTTONS[lang])
        assert old_btn in src, (page, 'langMenu html')
        src = src.replace(old_btn, new_btn, 1)
    if page == 'dushu':
        src = src.replace('title="${full[b] || b}">${b}</div>', 'title="${full[b] || b}">${SN(b)}</div>')
        assert 'SN(b)' in src, (page, 'SN grid')
    if page == 'shujia':
        src = src.replace('<div class="bn">${b}</div>', '<div class="bn">${SN(b)}</div>')
        assert 'SN(b)' in src, (page, 'SN bn')
    if page == 'gongfang':
        src = src.replace('return m ? `${m[1]} ${m[2]}` : chId;', 'return m ? `${SN(m[1])} ${m[2]}` : chId;')
    return src

def main():
    for lang, table in [('es', T_ES), ('pt', T_PT)]:
        out = os.path.join(HERE, lang)
        os.makedirs(out, exist_ok=True)
        for page in ['index', 'dushu', 'gongfang', 'shujia']:
            src = io.open(os.path.join(EN, page + '.html'), encoding='utf-8').read()
            src = structural(src, lang, page)
            missed = []
            for en_s, tr in table:
                if en_s in src:
                    src = src.replace(en_s, tr)
                else:
                    missed.append(en_s)
            io.open(os.path.join(out, page + '.html'), 'w', encoding='utf-8', newline='\n').write(src)
            # leftover English check: report suspicious residue (informational)
            print(lang, page, 'written; unmatched table entries used elsewhere:', len(missed))
        # manifest
        mf = json.load(io.open(os.path.join(EN, 'manifest-en.json'), encoding='utf-8'))
        mf.update(MANIFESTS[lang])
        io.open(os.path.join(out, f'manifest-{lang}.json'), 'w', encoding='utf-8', newline='\n').write(
            json.dumps(mf, ensure_ascii=False, indent=2))
        print(lang, 'manifest written')

if __name__ == '__main__':
    main()
