from django.test import TestCase #importo TestCase da Django per creare i miei test unitari
from django.contrib.auth.models import User #importo il modello User built-in di Django per creare utenti di test
from rest_framework.test import APIClient #importo APIClient di DRF per simulare le chiamate HTTP alle API
from rest_framework import status #importo il modulo status di DRF per usare i codici HTTP con nomi leggibili

from .models import Categoria, Prodotto, Ordine, OrdineProdotto #importo i modelli della mia app per creare dati di test


#─── Helper: factory functions ────────────────────────────────────────────────

def crea_categoria(nome='Bevande Calde'): #definisco una funzione helper per creare una categoria di test con valore di default
    return Categoria.objects.create(nome=nome, descrizione='Test') #creo e restituisco una nuova categoria nel database di test


def crea_prodotto(categoria, nome='Cappuccino', prezzo=2.50, disponibile=True): #definisco una funzione helper per creare un prodotto di test con valori di default
    return Prodotto.objects.create( #creo e restituisco un nuovo prodotto nel database di test
        nome=nome, prezzo=prezzo, disponibile=disponibile, categoria=categoria #passo i parametri ricevuti al metodo create
    )


def crea_utente(username='utente_test', password='pass1234', is_staff=False): #definisco una funzione helper per creare un utente di test con valori di default
    return User.objects.create_user(username=username, password=password, is_staff=is_staff) #creo e restituisco un utente con la password già hashata


def token_per(client, username, password): #definisco una funzione helper che esegue il login e restituisce il token JWT
    """Esegue il login e restituisce l'access token JWT.""" #docstring che descrive lo scopo della funzione
    resp = client.post('/api/auth/login/', {'username': username, 'password': password}) #eseguo una richiesta POST all'endpoint di login con le credenziali ricevute
    return resp.data.get('access') #estraggo e restituisco l'access token dalla risposta


#─── Test 1-3: Autenticazione ─────────────────────────────────────────────────

class TestRegistrazione(TestCase): #definisco la classe di test per la registrazione, estende TestCase di Django

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP

    #Test 1: registrazione valida → 201 + token restituiti
    def test_registrazione_valida(self): #definisco il test per la registrazione con dati validi
        resp = self.client.post('/api/auth/register/', { #eseguo una POST all'endpoint di registrazione
            'username': 'pallino', #passo il nome utente da registrare
            'password': 'maine_coon_123', #passo la password da associare all'utente
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED) #verifico che la risposta abbia codice 201 (risorsa creata)
        self.assertIn('access', resp.data) #verifico che la risposta contenga il campo access token
        self.assertIn('refresh', resp.data) #verifico che la risposta contenga il campo refresh token
        self.assertEqual(resp.data['user']['username'], 'pallino') #verifico che lo username restituito corrisponda a quello inviato

    #Test 2: username già esistente → 400
    def test_registrazione_username_duplicato(self): #definisco il test per la registrazione con username già in uso
        crea_utente('pallino') #creo preventivamente un utente con lo stesso username
        resp = self.client.post('/api/auth/register/', { #tento di registrare un secondo utente con lo stesso username
            'username': 'pallino', #username già esistente nel database
            'password': 'qualsiasi123', #passo una password qualsiasi
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST) #verifico che la risposta sia 400 (richiesta non valida)
        self.assertIn('error', resp.data) #verifico che la risposta contenga un campo error con il messaggio di errore

    #Test 3: login valido → restituisce access + refresh token
    def test_login_restituisce_token(self): #definisco il test per verificare che il login restituisca i token JWT
        crea_utente('micio', 'pass5678') #creo l'utente che userò per il login
        resp = self.client.post('/api/auth/login/', { #eseguo la richiesta di login con le credenziali dell'utente creato
            'username': 'micio', #passo lo username dell'utente creato
            'password': 'pass5678', #passo la password dell'utente creato
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che il login abbia avuto successo con codice 200
        self.assertIn('access', resp.data) #verifico che la risposta contenga l'access token
        self.assertIn('refresh', resp.data) #verifico che la risposta contenga il refresh token


#─── Test 4: /auth/me/ ────────────────────────────────────────────────────────

class TestMe(TestCase): #definisco la classe di test per l'endpoint /auth/me/

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        crea_utente('fuffi', 'pass1234') #creo l'utente che userò nei test di questa classe

    #Test 4a: con token valido → 200 + dati utente corretti
    def test_me_autenticato(self): #definisco il test per l'accesso a /auth/me/ con token valido
        token = token_per(self.client, 'fuffi', 'pass1234') #ottengo il token JWT facendo il login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header Authorization con il token ottenuto
        resp = self.client.get('/api/auth/me/') #eseguo la richiesta GET all'endpoint /auth/me/
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta abbia codice 200
        self.assertEqual(resp.data['username'], 'fuffi') #verifico che lo username restituito sia quello dell'utente autenticato

    #Test 4b: senza token → 401
    def test_me_non_autenticato(self): #definisco il test per l'accesso a /auth/me/ senza token
        resp = self.client.get('/api/auth/me/') #eseguo la richiesta GET senza impostare nessun header di autenticazione
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED) #verifico che la risposta sia 401 (non autorizzato)


#─── Test 5-6: Categorie ──────────────────────────────────────────────────────

class TestCategorie(TestCase): #definisco la classe di test per gli endpoint delle categorie

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        crea_categoria('Bevande Calde') #creo la prima categoria di test nel database
        crea_categoria('Dolci') #creo la seconda categoria di test nel database
        crea_utente('admin_test', 'admin123', is_staff=True) #creo un utente admin che userò nel test di creazione categoria

    #Test 5: GET /api/categorie/ è pubblico → 200 senza token
    def test_lista_categorie_pubblica(self): #definisco il test per verificare che la lista categorie sia pubblica
        resp = self.client.get('/api/categorie/') #eseguo la richiesta GET senza token di autenticazione
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200 anche senza autenticazione
        count = resp.data.get('count', len(resp.data)) #leggo il conteggio dalla risposta paginata oppure dalla lista diretta
        self.assertEqual(count, 2) #verifico che le categorie restituite siano esattamente 2 come quelle create nel setUp

    #Test 6: POST /api/categorie/ → utente normale riceve 403, admin 201
    def test_creazione_categoria_solo_admin(self): #definisco il test per verificare che solo l'admin possa creare categorie
        crea_utente('normale', 'pass1234') #creo un utente normale senza permessi di staff

        #Utente normale → 403
        token = token_per(self.client, 'normale', 'pass1234') #ottengo il token JWT dell'utente normale
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header con il token dell'utente normale
        resp = self.client.post('/api/categorie/', {'nome': 'Supercat'}) #tento di creare una categoria come utente normale
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN) #verifico che la risposta sia 403 (accesso negato)

        #Admin → 201
        token_admin = token_per(self.client, 'admin_test', 'admin123') #ottengo il token JWT dell'utente admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}') #imposto l'header con il token dell'admin
        resp = self.client.post('/api/categorie/', {'nome': 'Supercat'}) #creo una categoria come admin
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED) #verifico che la risposta sia 201 (categoria creata)


#─── Test 7: Filtro prodotti ──────────────────────────────────────────────────

class TestFiltroProdotti(TestCase): #definisco la classe di test per i filtri dell'endpoint prodotti

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        cat = crea_categoria() #creo una categoria da associare ai prodotti di test
        crea_prodotto(cat, 'Cappuccino', 2.50, disponibile=True) #creo un prodotto disponibile
        crea_prodotto(cat, 'Latte macchiato', 2.00, disponibile=True) #creo un secondo prodotto disponibile
        crea_prodotto(cat, 'Torta esaurita', 5.00, disponibile=False) #creo un prodotto non disponibile che non dovrà apparire nel filtro

    #Test 7: ?disponibile=true esclude i prodotti esauriti
    def test_filtro_disponibile(self): #definisco il test per verificare che il filtro ?disponibile=true funzioni correttamente
        resp = self.client.get('/api/prodotti/?disponibile=true') #eseguo la richiesta con il filtro attivo
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200
        risultati = resp.data.get('results', resp.data) #estraggo i risultati dalla risposta paginata oppure dalla lista diretta
        nomi = [p['nome'] for p in risultati] #costruisco una lista con i nomi dei prodotti restituiti
        self.assertNotIn('Torta esaurita', nomi) #verifico che il prodotto non disponibile non sia presente nei risultati
        self.assertIn('Cappuccino', nomi) #verifico che il primo prodotto disponibile sia presente
        self.assertIn('Latte macchiato', nomi) #verifico che il secondo prodotto disponibile sia presente


#─── Test 8-10: Ordini ────────────────────────────────────────────────────────

class TestOrdini(TestCase): #definisco la classe di test per gli endpoint degli ordini

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        self.utente1 = crea_utente('gatto1', 'pass1234') #creo il primo utente che userò per creare ordini
        self.utente2 = crea_utente('gatto2', 'pass5678') #creo il secondo utente per verificare l'isolamento degli ordini
        self.admin   = crea_utente('admin_cafe', 'admin123', is_staff=True) #creo l'utente admin per testare il cambio stato
        cat = crea_categoria() #creo una categoria da associare ai prodotti di test
        self.prod1 = crea_prodotto(cat, 'Espresso', 1.50) #creo il primo prodotto e lo salvo per usarlo nei test
        self.prod2 = crea_prodotto(cat, 'Cornetto', 1.20) #creo il secondo prodotto e lo salvo per usarlo nei test

    def _autentica(self, username, password): #definisco un metodo privato per autenticare rapidamente il client con un dato utente
        token = token_per(self.client, username, password) #ottengo il token JWT eseguendo il login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header Authorization con il token ottenuto

    #Test 8: creazione ordine → totale calcolato automaticamente dal server
    def test_crea_ordine_totale_automatico(self): #definisco il test per verificare il calcolo automatico del totale
        self._autentica('gatto1', 'pass1234') #autentico il client come gatto1
        payload = { #costruisco il payload dell'ordine con i prodotti e le quantità
            'note': 'Senza lattosio', #aggiungo una nota speciale all'ordine
            'prodotti': [ #lista dei prodotti con le rispettive quantità
                {'prodotto_id': self.prod1.id, 'quantita': 2},  #2 × 1.50 = 3.00
                {'prodotto_id': self.prod2.id, 'quantita': 1},  #1 × 1.20 = 1.20
            ]
        }
        resp = self.client.post('/api/ordini/', payload, format='json') #eseguo la POST per creare l'ordine
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED) #verifico che l'ordine sia stato creato con codice 201
        self.assertAlmostEqual(float(resp.data['totale']), 4.20, places=2) #verifico che il totale calcolato dal server sia 4.20
        self.assertEqual(resp.data['stato'], 'in_attesa') #verifico che lo stato iniziale dell'ordine sia in_attesa

    #Test 9: ogni utente vede solo i propri ordini
    def test_utente_vede_solo_propri_ordini(self): #definisco il test per verificare l'isolamento degli ordini tra utenti
        #gatto1 crea un ordine
        self._autentica('gatto1', 'pass1234') #autentico il client come gatto1
        self.client.post('/api/ordini/', { #creo un ordine per gatto1
            'prodotti': [{'prodotto_id': self.prod1.id, 'quantita': 1}] #ordino un solo prodotto
        }, format='json')

        #gatto2 non deve vederlo nella propria lista
        self._autentica('gatto2', 'pass5678') #cambio autenticazione e mi autentico come gatto2
        resp = self.client.get('/api/ordini/') #richiedo la lista ordini come gatto2
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200
        risultati = resp.data.get('results', resp.data) #estraggo i risultati dalla risposta paginata o dalla lista diretta
        self.assertEqual(len(risultati), 0) #verifico che gatto2 non veda nessun ordine perché non ne ha creati

    #Test 10: cambio stato → 403 per utente normale, 200 per admin
    def test_cambio_stato_solo_admin(self): #definisco il test per verificare che solo l'admin possa cambiare lo stato
        #gatto1 crea un ordine
        self._autentica('gatto1', 'pass1234') #autentico il client come gatto1
        resp = self.client.post('/api/ordini/', { #creo un ordine come gatto1
            'prodotti': [{'prodotto_id': self.prod1.id, 'quantita': 1}] #ordino un solo prodotto
        }, format='json')
        ordine_id = resp.data['id'] #salvo l'id dell'ordine appena creato per usarlo nei passaggi successivi

        #gatto1 prova a cambiare stato → 403
        resp = self.client.patch( #tento di aggiornare lo stato come utente normale (gatto1 è ancora autenticato)
            f'/api/ordini/{ordine_id}/stato/', {'stato': 'completato'} #invio il nuovo stato nell'endpoint dedicato
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN) #verifico che gatto1 riceva 403 perché non è admin

        #admin può cambiarlo → 200 con stato aggiornato
        self._autentica('admin_cafe', 'admin123') #cambio autenticazione e mi autentico come admin
        resp = self.client.patch( #aggiorno lo stato dell'ordine come admin
            f'/api/ordini/{ordine_id}/stato/', {'stato': 'completato'} #passo il nuovo stato nell'endpoint
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che l'admin riesca ad aggiornare lo stato con codice 200
        self.assertEqual(resp.data['stato'], 'completato') #verifico che lo stato nell'ordine restituito sia effettivamente aggiornato


class TestTokenRefresh(TestCase): #definisco la classe di test per il rinnovo del token JWT

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        crea_utente('refresh_user', 'pass1234') #creo l'utente che userò per testare il refresh

    def test_refresh_token(self): #definisco il test per verificare che il refresh token funzioni correttamente
        #login per ottenere refresh
        resp = self.client.post('/api/auth/login/', { #eseguo il login per ottenere i token iniziali
            'username': 'refresh_user', #passo lo username dell'utente creato nel setUp
            'password': 'pass1234', #passo la password dell'utente creato nel setUp
        })
        refresh = resp.data['refresh'] #estraggo il refresh token dalla risposta di login

        #richiesta nuovo access token
        resp = self.client.post('/api/auth/token/refresh/', { #invio il refresh token all'endpoint di rinnovo
            'refresh': refresh #passo il refresh token ottenuto al passo precedente
        })

        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200
        self.assertIn('access', resp.data) #verifico che la risposta contenga un nuovo access token


class TestDettaglioProdotto(TestCase): #definisco la classe di test per il dettaglio di un singolo prodotto

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        cat = crea_categoria() #creo una categoria da associare al prodotto di test
        self.prodotto = crea_prodotto(cat, 'Espresso', 1.50) #creo il prodotto di test e lo salvo come attributo della classe

    def test_dettaglio_prodotto(self): #definisco il test per verificare che il dettaglio di un prodotto sia accessibile pubblicamente
        resp = self.client.get(f'/api/prodotti/{self.prodotto.id}/') #eseguo la GET sul dettaglio del prodotto senza token

        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200 anche senza autenticazione
        self.assertEqual(resp.data['nome'], 'Espresso') #verifico che il nome del prodotto corrisponda a quello creato
        self.assertEqual(float(resp.data['prezzo']), 1.50) #verifico che il prezzo del prodotto corrisponda a quello impostato


class TestAdminOrdini(TestCase): #definisco la classe di test per verificare che l'admin veda tutti gli ordini

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        self.utente1 = crea_utente('user1', 'pass1234') #creo il primo utente che creerà un ordine
        self.utente2 = crea_utente('user2', 'pass5678') #creo il secondo utente (non creerà ordini in questo test)
        self.admin = crea_utente('admin', 'admin123', is_staff=True) #creo l'utente admin che dovrà vedere tutti gli ordini

        cat = crea_categoria() #creo una categoria da associare al prodotto di test
        prod = crea_prodotto(cat, 'Caffè', 1.00) #creo il prodotto che userò per creare l'ordine

        #crea ordine per utente1
        token = token_per(self.client, 'user1', 'pass1234') #ottengo il token di user1 per autenticarmi
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header con il token di user1
        self.client.post('/api/ordini/', { #creo un ordine come user1
            'prodotti': [{'prodotto_id': prod.id, 'quantita': 1}] #ordino un prodotto
        }, format='json')

    def test_admin_vede_tutti_ordini(self): #definisco il test per verificare che l'admin veda gli ordini di tutti gli utenti
        token = token_per(self.client, 'admin', 'admin123') #ottengo il token dell'admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header con il token dell'admin

        resp = self.client.get('/api/ordini/') #richiedo la lista ordini come admin
        self.assertEqual(resp.status_code, status.HTTP_200_OK) #verifico che la risposta sia 200

        risultati = resp.data.get('results', resp.data) #estraggo i risultati dalla risposta paginata o dalla lista diretta
        self.assertGreaterEqual(len(risultati), 1) #verifico che l'admin veda almeno l'ordine creato da user1 nel setUp


class TestDeleteCategoria(TestCase): #definisco la classe di test per verificare che solo l'admin possa eliminare categorie

    def setUp(self): #metodo eseguito automaticamente prima di ogni test della classe
        self.client = APIClient() #inizializzo il client API per simulare le richieste HTTP
        self.admin = crea_utente('admin_del', 'admin123', is_staff=True) #creo l'utente admin che potrà eliminare categorie
        self.user = crea_utente('user_del', 'pass1234') #creo l'utente normale che non potrà eliminare categorie
        self.categoria = crea_categoria('Da eliminare') #creo la categoria di test che tenteremo di eliminare

    def test_delete_categoria_solo_admin(self): #definisco il test per verificare che la DELETE sia riservata all'admin
        #utente normale → 403
        token = token_per(self.client, 'user_del', 'pass1234') #ottengo il token dell'utente normale
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header con il token dell'utente normale
        resp = self.client.delete(f'/api/categorie/{self.categoria.id}/') #tento di eliminare la categoria come utente normale
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN) #verifico che riceva 403 perché non è admin

        #admin → 204
        token = token_per(self.client, 'admin_del', 'admin123') #ottengo il token dell'admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}') #imposto l'header con il token dell'admin
        resp = self.client.delete(f'/api/categorie/{self.categoria.id}/') #elimino la categoria come admin
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT) #verifico che la risposta sia 204 (eliminazione riuscita)