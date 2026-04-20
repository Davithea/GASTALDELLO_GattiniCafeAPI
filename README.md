# 🐱 Gattini Cafe API

Pallino, il proprietario - un maestoso Maine Coon con un debole per i cappuccini - ha un problema: il suo sistema di ordinazioni è ancora cartaceo, e i suoi colleghi felini continuano a perdere i foglietti tra un pisolino e l'altro. Il progetto consiste nello sviluppo di un'API REST moderna che gestisca il menu e gli ordini del suo localino.

---

## Requisiti

- Python 3.10+
- pip

---

## Installazione

### 1. Clona il repository

```bash
git clone https://github.com/tuo-username/GASTALDELLO_GattiniCafeAPI.git
cd GASTALDELLO_GattiniCafeAPI
```

### 2. Crea e attiva il virtualenv

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Verifica che il file database sia presente

Il file `gattini_cafe.db` deve trovarsi nella root del progetto (stessa cartella di `manage.py`).  
Il database contiene già categorie, prodotti e ordini di esempio.

### 5. Crea il superuser admin

Le password degli utenti di test nel DB sono state resettate.  
Crea un nuovo admin con:

```bash
python manage.py createsuperuser
```

Oppure usa le credenziali di test già configurate (vedi sezione **Credenziali**).

---

## Avvio del server

```bash
python manage.py runserver
```

Il server parte su `http://127.0.0.1:8000/`.

---

## Credenziali di test

| Ruolo | Username | Password |
|-------|----------|----------|
| Admin (is_staff=True) | `admin` | `admin1234` |
| Utente normale | `gatto1` | `pass1234` |

> Per creare queste credenziali: `python manage.py createsuperuser` e segui il wizard.

---

## Struttura del progetto

```
GASTALDELLO_GattiniCafeAPI/
├── manage.py
├── gattini_cafe.db          ← database SQLite fornito
├── requirements.txt
├── README.md
├── GASTALDELLO_GattiniCafeAPI/   ← configurazione Django (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/                          ← app principale
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── permissions.py
│   ├── test_runner.py
│   └── tests.py
└── client/                       ← client HTML/PHP (bonus)
    └── index.html
```

---

## Endpoint disponibili

### Autenticazione

| Metodo | Endpoint | Auth | Descrizione |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Registrazione nuovo utente |
| POST | `/api/auth/login/` | No | Login — restituisce access + refresh token |
| POST | `/api/auth/token/refresh/` | No | Rinnova l'access token |
| GET | `/api/auth/me/` | Sì | Dati dell'utente autenticato |

### Menu (pubblici)

| Metodo | Endpoint | Auth | Descrizione |
|--------|----------|------|-------------|
| GET | `/api/categorie/` | No | Lista categorie |
| GET | `/api/categorie/{id}/` | No | Dettaglio categoria |
| GET | `/api/prodotti/` | No | Lista prodotti (supporta filtri) |
| GET | `/api/prodotti/{id}/` | No | Dettaglio prodotto |

**Filtri disponibili su `/api/prodotti/`:**
- `?categoria=<id>` — filtra per categoria
- `?disponibile=true` — solo prodotti disponibili
- `?search=<testo>` — ricerca per nome o descrizione

### Gestione menu (solo admin)

| Metodo | Endpoint | Auth | Descrizione |
|--------|----------|------|-------------|
| POST | `/api/categorie/` | Admin | Crea categoria |
| PUT/PATCH | `/api/categorie/{id}/` | Admin | Modifica categoria |
| DELETE | `/api/categorie/{id}/` | Admin | Elimina categoria |
| POST | `/api/prodotti/` | Admin | Crea prodotto |
| PUT/PATCH | `/api/prodotti/{id}/` | Admin | Modifica prodotto |
| DELETE | `/api/prodotti/{id}/` | Admin | Elimina prodotto |
| POST | `/api/prodotti/{id}/immagine/` | Admin | Upload immagine prodotto |

### Ordini (utente autenticato)

| Metodo | Endpoint | Auth | Descrizione |
|--------|----------|------|-------------|
| GET | `/api/ordini/` | Sì | Lista ordini (propri o tutti se admin) |
| POST | `/api/ordini/` | Sì | Crea nuovo ordine |
| GET | `/api/ordini/{id}/` | Sì | Dettaglio ordine |
| PATCH | `/api/ordini/{id}/stato/` | Admin | Aggiorna stato ordine |

**Filtri disponibili su `/api/ordini/`:**
- `?data_da=YYYY-MM-DD` — ordini da questa data
- `?data_a=YYYY-MM-DD` — ordini fino a questa data

### Bonus

| Metodo | Endpoint | Auth | Descrizione |
|--------|----------|------|-------------|
| GET | `/api/admin/stats/` | Admin | Statistiche (ordini per stato, prodotto più venduto, incasso oggi) |

---

## Esempi di chiamate API

### 1. Registrazione

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "micio", "password": "pass1234", "email": "micio@gattini.cafe"}'
```

Risposta:
```json
{
  "user": {"id": 3, "username": "micio", "email": "micio@gattini.cafe", "is_staff": false},
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 2. Login e ottenimento token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin1234"}'
```

Risposta:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### 3. Lista prodotti disponibili filtrati per categoria

```bash
curl http://127.0.0.1:8000/api/prodotti/?categoria=1&disponibile=true
```

Risposta (paginata):
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {"id": 1, "nome": "Cappuccino", "prezzo": 2.5, "disponibile": true, "categoria": 1},
    ...
  ]
}
```

---

### 4. Crea un ordine (richiede token JWT)

```bash
curl -X POST http://127.0.0.1:8000/api/ordini/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "note": "Senza glutine!",
    "prodotti": [
      {"prodotto_id": 1, "quantita": 2},
      {"prodotto_id": 3, "quantita": 1}
    ]
  }'
```

Risposta:
```json
{
  "id": 7,
  "utente": 2,
  "stato": "in_attesa",
  "totale": 7.2,
  "note": "Senza glutine!",
  "data_ordine": "2024-11-15T10:30:00Z",
  "prodotti_dettaglio": [
    {"prodotto_id": 1, "nome": "Cappuccino", "prezzo": 2.5, "quantita": 2, "subtotale": 5.0},
    {"prodotto_id": 3, "nome": "Cornetto", "prezzo": 2.2, "quantita": 1, "subtotale": 2.2}
  ]
}
```

---

### 5. Statistiche admin

```bash
curl http://127.0.0.1:8000/api/admin/stats/ \
  -H "Authorization: Bearer <access_token_admin>"
```

Risposta:
```json
{
  "ordini_per_stato": {
    "in_attesa": 5,
    "in_preparazione": 2,
    "completato": 12,
    "annullato": 1
  },
  "prodotto_piu_venduto": {
    "id": 1,
    "nome": "Cappuccino",
    "prezzo": 2.5,
    "unita_vendute": 47
  },
  "incasso_oggi": 38.5
}
```

---

## Esecuzione dei test

```bash
python manage.py test api
```

I test usano un custom test runner (`api/test_runner.py`) che crea automaticamente le tabelle `managed=False` nel database di test tramite SQL raw.

Copertura: 15 test su autenticazione, categorie, prodotti, ordini e permessi.

---

## Client web (bonus)

Il client HTML/PHP si trova nella cartella `client/`.

### Requisiti client

- PHP 7.4+ con `php -S` oppure un server Apache/Nginx con PHP
- Il backend Django deve essere in esecuzione su `http://127.0.0.1:8000`

### Avvio client (con php -S)

```bash
cd client
php -S localhost:8080
```

Apri il browser su `http://localhost:8080`.

### Avvio client (con XAMPP)
- Mettere il file `index.php` all'interno della cartella `/htdocs`.
- Avviare con XAMPP il server Apache.
- Aprire la pagina php tramite la sezione `Admin` fornita da XAMPP.

### Funzionalità client

- Login con salvataggio del token JWT in sessione PHP
- Visualizzazione menu: categorie e prodotti disponibili
- Creazione ordine con uno o più prodotti
- Gestione errori (token scaduto, prodotto non disponibile, errori di rete)

---

## Note di sviluppo

- La `SECRET_KEY` va sostituita con una chiave sicura in produzione.
- I file media (immagini prodotti) vengono salvati in `media/prodotti/`.