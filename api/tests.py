"""
Test unitari per Gattini Cafe API.
Esegui con: python manage.py test api

Le tabelle unmanaged (categoria, prodotto, ordine, ordine_prodotto) vengono
create automaticamente dal custom test runner configurato in settings.py:
    TEST_RUNNER = 'api.test_runner.UnmanagedTablesTestRunner'
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from .models import Categoria, Prodotto, Ordine, OrdineProdotto


# ─── Helper: factory functions ────────────────────────────────────────────────

def crea_categoria(nome='Bevande Calde'):
    return Categoria.objects.create(nome=nome, descrizione='Test')


def crea_prodotto(categoria, nome='Cappuccino', prezzo=2.50, disponibile=True):
    return Prodotto.objects.create(
        nome=nome, prezzo=prezzo, disponibile=disponibile, categoria=categoria
    )


def crea_utente(username='utente_test', password='pass1234', is_staff=False):
    return User.objects.create_user(username=username, password=password, is_staff=is_staff)


def token_per(client, username, password):
    """Esegue il login e restituisce l'access token JWT."""
    resp = client.post('/api/auth/login/', {'username': username, 'password': password})
    return resp.data.get('access')


# ─── Test 1-3: Autenticazione ─────────────────────────────────────────────────

class TestRegistrazione(TestCase):

    def setUp(self):
        self.client = APIClient()

    # Test 1: registrazione valida → 201 + token restituiti
    def test_registrazione_valida(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'pallino',
            'password': 'maine_coon_123',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertEqual(resp.data['user']['username'], 'pallino')

    # Test 2: username già esistente → 400
    def test_registrazione_username_duplicato(self):
        crea_utente('pallino')
        resp = self.client.post('/api/auth/register/', {
            'username': 'pallino',
            'password': 'qualsiasi123',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', resp.data)

    # Test 3: login valido → restituisce access + refresh token
    def test_login_restituisce_token(self):
        crea_utente('micio', 'pass5678')
        resp = self.client.post('/api/auth/login/', {
            'username': 'micio',
            'password': 'pass5678',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)


# ─── Test 4: /auth/me/ ────────────────────────────────────────────────────────

class TestMe(TestCase):

    def setUp(self):
        self.client = APIClient()
        crea_utente('fuffi', 'pass1234')

    # Test 4a: con token valido → 200 + dati utente corretti
    def test_me_autenticato(self):
        token = token_per(self.client, 'fuffi', 'pass1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'fuffi')

    # Test 4b: senza token → 401
    def test_me_non_autenticato(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ─── Test 5-6: Categorie ──────────────────────────────────────────────────────

class TestCategorie(TestCase):

    def setUp(self):
        self.client = APIClient()
        crea_categoria('Bevande Calde')
        crea_categoria('Dolci')
        crea_utente('admin_test', 'admin123', is_staff=True)

    # Test 5: GET /api/categorie/ è pubblico → 200 senza token
    def test_lista_categorie_pubblica(self):
        resp = self.client.get('/api/categorie/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        count = resp.data.get('count', len(resp.data))
        self.assertEqual(count, 2)

    # Test 6: POST /api/categorie/ → utente normale riceve 403, admin 201
    def test_creazione_categoria_solo_admin(self):
        crea_utente('normale', 'pass1234')

        # Utente normale → 403
        token = token_per(self.client, 'normale', 'pass1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.post('/api/categorie/', {'nome': 'Supercat'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Admin → 201
        token_admin = token_per(self.client, 'admin_test', 'admin123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')
        resp = self.client.post('/api/categorie/', {'nome': 'Supercat'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


# ─── Test 7: Filtro prodotti ──────────────────────────────────────────────────

class TestFiltroProdotti(TestCase):

    def setUp(self):
        self.client = APIClient()
        cat = crea_categoria()
        crea_prodotto(cat, 'Cappuccino', 2.50, disponibile=True)
        crea_prodotto(cat, 'Latte macchiato', 2.00, disponibile=True)
        crea_prodotto(cat, 'Torta esaurita', 5.00, disponibile=False)

    # Test 7: ?disponibile=true esclude i prodotti esauriti
    def test_filtro_disponibile(self):
        resp = self.client.get('/api/prodotti/?disponibile=true')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        risultati = resp.data.get('results', resp.data)
        nomi = [p['nome'] for p in risultati]
        self.assertNotIn('Torta esaurita', nomi)
        self.assertIn('Cappuccino', nomi)
        self.assertIn('Latte macchiato', nomi)


# ─── Test 8-10: Ordini ────────────────────────────────────────────────────────

class TestOrdini(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.utente1 = crea_utente('gatto1', 'pass1234')
        self.utente2 = crea_utente('gatto2', 'pass5678')
        self.admin   = crea_utente('admin_cafe', 'admin123', is_staff=True)
        cat = crea_categoria()
        self.prod1 = crea_prodotto(cat, 'Espresso', 1.50)
        self.prod2 = crea_prodotto(cat, 'Cornetto', 1.20)

    def _autentica(self, username, password):
        token = token_per(self.client, username, password)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    # Test 8: creazione ordine → totale calcolato automaticamente dal server
    def test_crea_ordine_totale_automatico(self):
        self._autentica('gatto1', 'pass1234')
        payload = {
            'note': 'Senza lattosio',
            'prodotti': [
                {'prodotto_id': self.prod1.id, 'quantita': 2},  # 2 × 1.50 = 3.00
                {'prodotto_id': self.prod2.id, 'quantita': 1},  # 1 × 1.20 = 1.20
            ]
        }
        resp = self.client.post('/api/ordini/', payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertAlmostEqual(float(resp.data['totale']), 4.20, places=2)
        self.assertEqual(resp.data['stato'], 'in_attesa')

    # Test 9: ogni utente vede solo i propri ordini
    def test_utente_vede_solo_propri_ordini(self):
        # gatto1 crea un ordine
        self._autentica('gatto1', 'pass1234')
        self.client.post('/api/ordini/', {
            'prodotti': [{'prodotto_id': self.prod1.id, 'quantita': 1}]
        }, format='json')

        # gatto2 non deve vederlo nella propria lista
        self._autentica('gatto2', 'pass5678')
        resp = self.client.get('/api/ordini/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        risultati = resp.data.get('results', resp.data)
        self.assertEqual(len(risultati), 0)

    # Test 10: cambio stato → 403 per utente normale, 200 per admin
    def test_cambio_stato_solo_admin(self):
        # gatto1 crea un ordine
        self._autentica('gatto1', 'pass1234')
        resp = self.client.post('/api/ordini/', {
            'prodotti': [{'prodotto_id': self.prod1.id, 'quantita': 1}]
        }, format='json')
        ordine_id = resp.data['id']

        # gatto1 prova a cambiare stato → 403
        resp = self.client.patch(
            f'/api/ordini/{ordine_id}/stato/', {'stato': 'completato'}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # admin può cambiarlo → 200 con stato aggiornato
        self._autentica('admin_cafe', 'admin123')
        resp = self.client.patch(
            f'/api/ordini/{ordine_id}/stato/', {'stato': 'completato'}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['stato'], 'completato')

class TestTokenRefresh(TestCase):

    def setUp(self):
        self.client = APIClient()
        crea_utente('refresh_user', 'pass1234')

    def test_refresh_token(self):
        # login per ottenere refresh
        resp = self.client.post('/api/auth/login/', {
            'username': 'refresh_user',
            'password': 'pass1234',
        })
        refresh = resp.data['refresh']

        # richiesta nuovo access token
        resp = self.client.post('/api/auth/token/refresh/', {
            'refresh': refresh
        })

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

class TestDettaglioProdotto(TestCase):

    def setUp(self):
        self.client = APIClient()
        cat = crea_categoria()
        self.prodotto = crea_prodotto(cat, 'Espresso', 1.50)

    def test_dettaglio_prodotto(self):
        resp = self.client.get(f'/api/prodotti/{self.prodotto.id}/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nome'], 'Espresso')
        self.assertEqual(float(resp.data['prezzo']), 1.50)

class TestAdminOrdini(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.utente1 = crea_utente('user1', 'pass1234')
        self.utente2 = crea_utente('user2', 'pass5678')
        self.admin = crea_utente('admin', 'admin123', is_staff=True)

        cat = crea_categoria()
        prod = crea_prodotto(cat, 'Caffè', 1.00)

        # crea ordine per utente1
        token = token_per(self.client, 'user1', 'pass1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.client.post('/api/ordini/', {
            'prodotti': [{'prodotto_id': prod.id, 'quantita': 1}]
        }, format='json')

    def test_admin_vede_tutti_ordini(self):
        token = token_per(self.client, 'admin', 'admin123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.get('/api/ordini/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        risultati = resp.data.get('results', resp.data)
        self.assertGreaterEqual(len(risultati), 1)

class TestDeleteCategoria(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = crea_utente('admin_del', 'admin123', is_staff=True)
        self.user = crea_utente('user_del', 'pass1234')
        self.categoria = crea_categoria('Da eliminare')

    def test_delete_categoria_solo_admin(self):
        # utente normale → 403
        token = token_per(self.client, 'user_del', 'pass1234')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.delete(f'/api/categorie/{self.categoria.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # admin → 204
        token = token_per(self.client, 'admin_del', 'admin123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.delete(f'/api/categorie/{self.categoria.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)