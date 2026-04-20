<?php
// ─── Configurazione ───────────────────────────────────────────────────────────
define('API_BASE', 'http://127.0.0.1:8000/api');
session_start();

// ─── Helper: chiamata all'API ─────────────────────────────────────────────────
function api_call(string $method, string $endpoint, array $data = [], bool $auth = false): array {
    $url = API_BASE . $endpoint;
    $headers = ['Content-Type: application/json'];

    if ($auth && isset($_SESSION['access_token'])) {
        $headers[] = 'Authorization: Bearer ' . $_SESSION['access_token'];
    }

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curl_error = curl_error($ch);
    curl_close($ch);

    if ($curl_error) {
        return ['error' => 'Impossibile connettersi al server API. Assicurati che Django sia in esecuzione su ' . API_BASE, 'code' => 0];
    }

    $decoded = json_decode($response, true) ?? [];
    $decoded['_http_code'] = $http_code;
    return $decoded;
}

// ─── Azioni POST ──────────────────────────────────────────────────────────────
$message = '';
$message_type = '';

// Logout
if (isset($_POST['action']) && $_POST['action'] === 'logout') {
    session_destroy();
    header('Location: ' . $_SERVER['PHP_SELF']);
    exit;
}

// Login
if (isset($_POST['action']) && $_POST['action'] === 'login') {
    $result = api_call('POST', '/auth/login/', [
        'username' => trim($_POST['username'] ?? ''),
        'password' => $_POST['password'] ?? '',
    ]);

    if (isset($result['access'])) {
        $_SESSION['access_token']  = $result['access'];
        $_SESSION['refresh_token'] = $result['refresh'];

        // Recupero i dati utente
        $me = api_call('GET', '/auth/me/', [], true);
        $_SESSION['username'] = $me['username'] ?? $_POST['username'];
        $_SESSION['is_staff']  = $me['is_staff'] ?? false;

        header('Location: ' . $_SERVER['PHP_SELF']);
        exit;
    } else {
        $message = 'Credenziali non valide. Riprova.';
        if (isset($result['detail'])) $message = $result['detail'];
        $message_type = 'error';
    }
}

// Crea ordine
if (isset($_POST['action']) && $_POST['action'] === 'crea_ordine' && isset($_SESSION['access_token'])) {
    $prodotti_raw = $_POST['prodotti'] ?? [];
    $note = trim($_POST['note'] ?? '');
    $prodotti = [];

    foreach ($prodotti_raw as $pid => $qty) {
        $qty = (int)$qty;
        if ($qty > 0) {
            $prodotti[] = ['prodotto_id' => (int)$pid, 'quantita' => $qty];
        }
    }

    if (empty($prodotti)) {
        $message = 'Seleziona almeno un prodotto con quantità maggiore di 0.';
        $message_type = 'error';
    } else {
        $payload = ['prodotti' => $prodotti];
        if ($note !== '') $payload['note'] = $note;

        $result = api_call('POST', '/ordini/', $payload, true);

        if (isset($result['id'])) {
            $message = "Ordine #" . $result['id'] . " creato! Totale: €" . number_format($result['totale'], 2, ',', '.') . " — Stato: " . $result['stato'];
            $message_type = 'success';
        } elseif ($result['_http_code'] === 401) {
            $message = 'Sessione scaduta. Effettua di nuovo il login.';
            $message_type = 'error';
            session_destroy();
            header('Location: ' . $_SERVER['PHP_SELF']);
            exit;
        } else {
            $message = 'Errore nella creazione dell\'ordine: ' . json_encode($result);
            $message_type = 'error';
        }
    }
}

// ─── Recupero dati per la pagina ─────────────────────────────────────────────
$logged_in = isset($_SESSION['access_token']);
$categorie = [];
$prodotti_per_categoria = [];
$ordini = [];

if ($logged_in) {
    // Categorie
    $res_cat = api_call('GET', '/categorie/?page_size=100', [], false);
    $categorie = $res_cat['results'] ?? $res_cat;

    // Prodotti disponibili
    $res_prod = api_call('GET', '/prodotti/?disponibile=true&page_size=100', [], false);
    $tutti_prodotti = $res_prod['results'] ?? $res_prod;

    foreach ($tutti_prodotti as $p) {
        $cat_id = $p['categoria'] ?? 0;
        $prodotti_per_categoria[$cat_id][] = $p;
    }

    // Ordini dell'utente
    $res_ord = api_call('GET', '/ordini/', [], true);
    $ordini = $res_ord['results'] ?? $res_ord;
    if (isset($ordini['_http_code'])) $ordini = [];
}

// Mappa categorie per nome
$cat_map = [];
foreach ($categorie as $c) {
    $cat_map[$c['id']] = $c['nome'];
}

// Colori stato ordine
$stato_color = [
    'in_attesa'       => '#854F0B',
    'in_preparazione' => '#185FA5',
    'completato'      => '#3B6D11',
    'annullato'       => '#A32D2D',
];
$stato_bg = [
    'in_attesa'       => '#FAEEDA',
    'in_preparazione' => '#E6F1FB',
    'completato'      => '#EAF3DE',
    'annullato'       => '#FCEBEB',
];
?>
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🐱 Gattini Cafe</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 15px;
    color: #1a1a1a;
    background: #f5f4f0;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: #fff;
    border-bottom: 0.5px solid #e0ddd4;
    padding: 0 2rem;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .logo { font-size: 18px; font-weight: 500; display: flex; align-items: center; gap: 8px; }
  .header-right { display: flex; align-items: center; gap: 12px; }
  .badge-user {
    font-size: 13px; color: #5F5E5A;
    background: #F1EFE8; padding: 4px 10px;
    border-radius: 99px;
  }

  /* ── Layout ── */
  main { max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }

  /* ── Card ── */
  .card {
    background: #fff;
    border: 0.5px solid #e0ddd4;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }
  .card-title {
    font-size: 16px; font-weight: 500;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 0.5px solid #e0ddd4;
  }

  /* ── Form ── */
  .form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 1rem; }
  label { font-size: 13px; color: #5F5E5A; font-weight: 500; }
  input[type=text], input[type=password], textarea {
    width: 100%; padding: 9px 12px;
    border: 0.5px solid #c8c6bc; border-radius: 8px;
    font-size: 14px; font-family: inherit;
    background: #fff; color: #1a1a1a;
    transition: border-color .15s;
  }
  input:focus, textarea:focus { outline: none; border-color: #1D9E75; }
  textarea { resize: vertical; min-height: 60px; }

  /* ── Buttons ── */
  .btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; border-radius: 8px; font-size: 14px;
    font-family: inherit; cursor: pointer; border: 0.5px solid #c8c6bc;
    background: #fff; color: #1a1a1a; transition: background .15s;
    text-decoration: none;
  }
  .btn:hover { background: #F1EFE8; }
  .btn:active { transform: scale(0.98); }
  .btn-primary {
    background: #1D9E75; color: #fff; border-color: #1D9E75; font-weight: 500;
  }
  .btn-primary:hover { background: #0F6E56; border-color: #0F6E56; }
  .btn-sm { padding: 5px 10px; font-size: 13px; }

  /* ── Alert ── */
  .alert {
    padding: 12px 16px; border-radius: 8px;
    margin-bottom: 1.25rem; font-size: 14px;
    border: 0.5px solid;
  }
  .alert-success { background: #EAF3DE; color: #3B6D11; border-color: #C0DD97; }
  .alert-error   { background: #FCEBEB; color: #A32D2D; border-color: #F7C1C1; }

  /* ── Login box ── */
  .login-wrap {
    max-width: 400px; margin: 3rem auto;
  }
  .login-logo {
    text-align: center; font-size: 42px; margin-bottom: .5rem;
  }
  .login-title {
    text-align: center; font-size: 22px; font-weight: 500; margin-bottom: .25rem;
  }
  .login-sub {
    text-align: center; font-size: 14px; color: #5F5E5A; margin-bottom: 1.5rem;
  }

  /* ── Grid menu ── */
  .menu-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 10px;
  }
  .prodotto-card {
    border: 0.5px solid #e0ddd4; border-radius: 8px;
    padding: 12px; background: #fff;
    display: flex; flex-direction: column; gap: 6px;
  }
  .prodotto-nome { font-size: 14px; font-weight: 500; }
  .prodotto-prezzo { font-size: 13px; color: #3B6D11; font-weight: 500; }
  .prodotto-cat { font-size: 11px; color: #888780; }
  .qty-input {
    width: 60px; padding: 5px 8px;
    border: 0.5px solid #c8c6bc; border-radius: 6px;
    font-size: 13px; text-align: center;
  }
  .qty-row { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
  .qty-label { font-size: 12px; color: #5F5E5A; }

  /* ── Sezione categorie ── */
  .cat-section { margin-bottom: 1.25rem; }
  .cat-title {
    font-size: 13px; font-weight: 500; color: #5F5E5A;
    text-transform: uppercase; letter-spacing: .05em;
    margin-bottom: 8px;
  }

  /* ── Ordini ── */
  .ordine-row {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 0; border-bottom: 0.5px solid #F1EFE8;
  }
  .ordine-row:last-child { border-bottom: none; }
  .ordine-id { font-size: 13px; color: #888780; min-width: 60px; }
  .ordine-info { flex: 1; }
  .ordine-note { font-size: 12px; color: #5F5E5A; margin-top: 2px; }
  .stato-badge {
    font-size: 11px; font-weight: 500;
    padding: 3px 8px; border-radius: 99px;
  }
  .ordine-totale { font-size: 14px; font-weight: 500; }

  /* ── Tab nav ── */
  .tabs { display: flex; gap: 4px; margin-bottom: 1.5rem; }
  .tab {
    padding: 7px 16px; border-radius: 8px; font-size: 14px;
    cursor: pointer; border: 0.5px solid transparent;
    background: transparent; color: #5F5E5A; font-family: inherit;
  }
  .tab.active {
    background: #fff; border-color: #e0ddd4; color: #1a1a1a; font-weight: 500;
  }
  .tab:hover:not(.active) { background: #F1EFE8; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  .empty { color: #888780; font-size: 14px; text-align: center; padding: 2rem 0; }
</style>
</head>
<body>

<header>
  <div class="logo">🐱 Gattini Cafe</div>
  <div class="header-right">
    <?php if ($logged_in): ?>
      <span class="badge-user">
        <?= htmlspecialchars($_SESSION['username']) ?>
        <?= $_SESSION['is_staff'] ? ' · admin' : '' ?>
      </span>
      <form method="post" style="margin:0">
        <input type="hidden" name="action" value="logout">
        <button type="submit" class="btn btn-sm">Esci</button>
      </form>
    <?php endif; ?>
  </div>
</header>

<main>

<?php if (!$logged_in): ?>
<!-- ══════════════════════════════════════════════════════════════ LOGIN ══ -->
<div class="login-wrap">
  <div class="login-logo">☕</div>
  <div class="login-title">Gattini Cafe</div>
  <div class="login-sub">Accedi per ordinare</div>

  <?php if ($message): ?>
    <div class="alert alert-<?= $message_type ?>"><?= htmlspecialchars($message) ?></div>
  <?php endif; ?>

  <div class="card">
    <form method="post">
      <input type="hidden" name="action" value="login">
      <div class="form-row">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" required
               value="<?= htmlspecialchars($_POST['username'] ?? '') ?>"
               placeholder="es. admin">
      </div>
      <div class="form-row">
        <label for="password">Password</label>
        <input type="password" id="password" name="password" required placeholder="••••••••">
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:.5rem">
        Accedi
      </button>
    </form>
  </div>
  <p style="text-align:center;font-size:13px;color:#888780;margin-top:1rem">
    Backend: <code><?= API_BASE ?></code>
  </p>
</div>

<?php else: ?>
<!-- ═══════════════════════════════════════════════════════════ DASHBOARD ══ -->

<?php if ($message): ?>
  <div class="alert alert-<?= $message_type ?>"><?= htmlspecialchars($message) ?></div>
<?php endif; ?>

<!-- Tab nav -->
<div class="tabs">
  <button class="tab active" onclick="mostraTab('menu', this)">Menu</button>
  <button class="tab" onclick="mostraTab('ordina', this)">Crea ordine</button>
  <button class="tab" onclick="mostraTab('ordini', this)">I miei ordini</button>
</div>

<!-- ── Tab: Menu ──────────────────────────────────────────────────────────── -->
<div id="tab-menu" class="tab-content active">
  <div class="card">
    <div class="card-title">Menu disponibile</div>

    <?php if (empty($tutti_prodotti)): ?>
      <p class="empty">Nessun prodotto disponibile al momento.</p>
    <?php else: ?>
      <?php foreach ($categorie as $cat): ?>
        <?php $prods = $prodotti_per_categoria[$cat['id']] ?? []; ?>
        <?php if (!empty($prods)): ?>
          <div class="cat-section">
            <div class="cat-title"><?= htmlspecialchars($cat['nome']) ?></div>
            <div class="menu-grid">
              <?php foreach ($prods as $p): ?>
                <div class="prodotto-card">
                  <div class="prodotto-nome"><?= htmlspecialchars($p['nome']) ?></div>
                  <?php if (!empty($p['descrizione'])): ?>
                    <div style="font-size:12px;color:#5F5E5A"><?= htmlspecialchars(mb_strimwidth($p['descrizione'], 0, 60, '…')) ?></div>
                  <?php endif; ?>
                  <div class="prodotto-prezzo">€<?= number_format($p['prezzo'], 2, ',', '.') ?></div>
                </div>
              <?php endforeach; ?>
            </div>
          </div>
        <?php endif; ?>
      <?php endforeach; ?>
    <?php endif; ?>
  </div>
</div>

<!-- ── Tab: Crea ordine ───────────────────────────────────────────────────── -->
<div id="tab-ordina" class="tab-content">
  <div class="card">
    <div class="card-title">Nuovo ordine</div>

    <?php if (empty($tutti_prodotti)): ?>
      <p class="empty">Nessun prodotto disponibile.</p>
    <?php else: ?>
      <form method="post">
        <input type="hidden" name="action" value="crea_ordine">

        <?php foreach ($categorie as $cat): ?>
          <?php $prods = $prodotti_per_categoria[$cat['id']] ?? []; ?>
          <?php if (!empty($prods)): ?>
            <div class="cat-section">
              <div class="cat-title"><?= htmlspecialchars($cat['nome']) ?></div>
              <div class="menu-grid">
                <?php foreach ($prods as $p): ?>
                  <div class="prodotto-card">
                    <div class="prodotto-nome"><?= htmlspecialchars($p['nome']) ?></div>
                    <div class="prodotto-prezzo">€<?= number_format($p['prezzo'], 2, ',', '.') ?></div>
                    <div class="qty-row">
                      <label class="qty-label" for="qty_<?= $p['id'] ?>">Qty</label>
                      <input
                        type="number"
                        class="qty-input"
                        id="qty_<?= $p['id'] ?>"
                        name="prodotti[<?= $p['id'] ?>]"
                        min="0" max="99" value="0"
                        onchange="aggiornaTotale()">
                    </div>
                  </div>
                <?php endforeach; ?>
              </div>
            </div>
          <?php endif; ?>
        <?php endforeach; ?>

        <div style="margin-top:1.25rem;padding-top:1rem;border-top:.5px solid #e0ddd4">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
            <div style="font-size:15px;font-weight:500">
              Totale stimato: <span id="totale-preview" style="color:#1D9E75">€0,00</span>
            </div>
          </div>

          <div class="form-row">
            <label for="note">Note speciali (opzionale)</label>
            <textarea id="note" name="note" placeholder="es. Senza lattosio, allergie..."></textarea>
          </div>

          <button type="submit" class="btn btn-primary">
            Conferma ordine
          </button>
        </div>
      </form>

      <script>
        // Prezzi prodotti per il calcolo lato client (stima visiva, il server ricalcola)
        const prezzi = {
          <?php foreach ($tutti_prodotti as $p): ?>
            <?= $p['id'] ?>: <?= $p['prezzo'] ?>,
          <?php endforeach; ?>
        };

        function aggiornaTotale() {
          let tot = 0;
          document.querySelectorAll('[name^="prodotti["]').forEach(input => {
            const match = input.name.match(/prodotti\[(\d+)\]/);
            if (match) {
              const pid = parseInt(match[1]);
              const qty = parseInt(input.value) || 0;
              if (prezzi[pid] && qty > 0) tot += prezzi[pid] * qty;
            }
          });
          document.getElementById('totale-preview').textContent =
            '€' + tot.toFixed(2).replace('.', ',');
        }
      </script>
    <?php endif; ?>
  </div>
</div>

<!-- ── Tab: I miei ordini ─────────────────────────────────────────────────── -->
<div id="tab-ordini" class="tab-content">
  <div class="card">
    <div class="card-title">
      <?= $_SESSION['is_staff'] ? 'Tutti gli ordini' : 'I miei ordini' ?>
    </div>

    <?php if (empty($ordini)): ?>
      <p class="empty">Nessun ordine trovato.</p>
    <?php else: ?>
      <?php foreach ($ordini as $o): ?>
        <?php
          $stato = $o['stato'] ?? 'in_attesa';
          $bg  = $stato_bg[$stato]  ?? '#F1EFE8';
          $col = $stato_color[$stato] ?? '#444441';
        ?>
        <div class="ordine-row">
          <div class="ordine-id">#<?= $o['id'] ?></div>
          <div class="ordine-info">
            <div style="font-size:13px;color:#444441">
              <?= date('d/m/Y H:i', strtotime($o['data_ordine'])) ?>
              <?php if (!empty($o['note'])): ?>
                &nbsp;·&nbsp;<span class="ordine-note"><?= htmlspecialchars($o['note']) ?></span>
              <?php endif; ?>
            </div>
            <?php if (!empty($o['prodotti_dettaglio'])): ?>
              <div style="font-size:12px;color:#888780;margin-top:3px">
                <?php
                  $nomi = array_map(fn($d) => $d['nome'] . ' ×' . $d['quantita'], $o['prodotti_dettaglio']);
                  echo htmlspecialchars(implode(', ', $nomi));
                ?>
              </div>
            <?php endif; ?>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            <span class="stato-badge" style="background:<?= $bg ?>;color:<?= $col ?>">
              <?= str_replace('_', ' ', $stato) ?>
            </span>
            <span class="ordine-totale">€<?= number_format($o['totale'], 2, ',', '.') ?></span>
          </div>
        </div>
      <?php endforeach; ?>
    <?php endif; ?>
  </div>
</div>

<script>
  function mostraTab(nome, el) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + nome).classList.add('active');
    el.classList.add('active');
  }
</script>

<?php endif; ?>
</main>
</body>
</html>