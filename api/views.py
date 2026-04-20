from rest_framework import generics, filters  #Importo view generiche e filtri DRF
from rest_framework.views import APIView  #Importo APIView per endpoint custom
from rest_framework.response import Response  #Importo Response per risposte API
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser  #Importo permessi DRF
from rest_framework.parsers import MultiPartParser, FormParser  #Importo parser per upload file
from rest_framework_simplejwt.tokens import RefreshToken  #Importo JWT refresh token
from django.contrib.auth.models import User  #Importo modello User
from django.db.models import Sum, Count  #Importo funzioni di aggregazione database
from django.utils import timezone  #Importo gestione tempo Django
import os  #Importo os per gestione file system

from .models import Categoria, Prodotto, Ordine, OrdineProdotto  #Importo modelli progetto
from .serializers import (  #Importo serializer
    CategoriaSerializer, ProdottoSerializer,
    OrdineSerializer, UserSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin  #Importo permessi custom


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterView(APIView):  #Definisco endpoint registrazione
    permission_classes = [AllowAny]  #Permetto accesso pubblico

    def post(self, request):  #Gestisco richiesta POST
        username = request.data.get('username')  #Recupero username
        password = request.data.get('password')  #Recupero password
        email = request.data.get('email', '')  #Recupero email opzionale

        if not username or not password:  #Controllo campi obbligatori
            return Response({'error': 'Username e password obbligatori'}, status=400)  #Errore input

        if User.objects.filter(username=username).exists():  #Controllo duplicato username
            return Response({'error': 'Username già esistente'}, status=400)  #Errore duplicazione

        user = User.objects.create_user(username=username, password=password, email=email)  #Creo utente
        refresh = RefreshToken.for_user(user)  #Genero token JWT

        return Response({  #Restituisco risposta
            'user': UserSerializer(user).data,  #Dati utente
            'access': str(refresh.access_token),  #Access token
            'refresh': str(refresh),  #Refresh token
        }, status=201)  #Status creazione


class MeView(APIView):  #Definisco endpoint utente corrente
    permission_classes = [IsAuthenticated]  #Richiedo autenticazione

    def get(self, request):  #Gestisco GET
        return Response(UserSerializer(request.user).data)  #Restituisco dati utente


# ─── Categorie ────────────────────────────────────────────────────────────────

class CategoriaListCreateView(generics.ListCreateAPIView):  #Lista + creazione categorie
    queryset = Categoria.objects.all()  #Definisco queryset
    serializer_class = CategoriaSerializer  #Definisco serializer
    permission_classes = [IsAdminOrReadOnly]  #Permessi lettura pubblica scrittura admin


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):  #Dettaglio categoria CRUD
    queryset = Categoria.objects.all()  #Query categorie
    serializer_class = CategoriaSerializer  #Serializer categoria
    permission_classes = [IsAdminOrReadOnly]  #Permessi


# ─── Prodotti ─────────────────────────────────────────────────────────────────

class ProdottoListCreateView(generics.ListCreateAPIView):  #Lista e creazione prodotti
    serializer_class = ProdottoSerializer  #Serializer prodotti
    permission_classes = [IsAdminOrReadOnly]  #Permessi
    filter_backends = [filters.SearchFilter]  #Abilito ricerca
    search_fields = ['nome', 'descrizione']  #Campi ricercabili

    def get_queryset(self):  #Definisco query dinamica
        queryset = Prodotto.objects.all()  #Parto da tutti i prodotti
        categoria = self.request.query_params.get('categoria')  #Filtro categoria
        if categoria:  #Se presente filtro
            queryset = queryset.filter(categoria_id=categoria)  #Applico filtro
        disponibile = self.request.query_params.get('disponibile')  #Filtro disponibilità
        if disponibile == 'true':  #Se true
            queryset = queryset.filter(disponibile=True)  #Filtro disponibili
        return queryset  #Ritorno queryset filtrato


class ProdottoDetailView(generics.RetrieveUpdateDestroyAPIView):  #CRUD singolo prodotto
    queryset = Prodotto.objects.all()  #Query prodotti
    serializer_class = ProdottoSerializer  #Serializer prodotti
    permission_classes = [IsAdminOrReadOnly]  #Permessi


# ─── Upload immagine prodotto ────────────────────────────────────────────────

class ProdottoImmagineView(APIView):  #Endpoint upload immagine
    permission_classes = [IsAuthenticated, IsAdminUser]  #Solo admin autenticato
    parser_classes = [MultiPartParser, FormParser]  #Supporto upload file

    def post(self, request, pk):  #Gestisco upload
        try:
            prodotto = Prodotto.objects.get(pk=pk)  #Cerco prodotto
        except Prodotto.DoesNotExist:  #Se non trovato
            return Response({'error': 'Prodotto non trovato'}, status=404)  #Errore 404

        file = request.FILES.get('immagine')  #Recupero file upload
        if not file:  #Se mancante
            return Response({'error': 'Nessun file ricevuto. Usa il campo "immagine".'}, status=400)  #Errore

        estensioni_ammesse = ['.jpg', '.jpeg', '.png', '.webp', '.gif']  #Lista estensioni valide
        _, estensione = os.path.splitext(file.name.lower())  #Estraggo estensione file
        if estensione not in estensioni_ammesse:  #Controllo formato
            return Response({'error': 'Formato non supportato'}, status=400)  #Errore formato

        from django.core.files.storage import default_storage  #Import storage Django
        from django.core.files.base import ContentFile  #Import file wrapper

        nome_file = f'prodotti/prodotto_{pk}_{file.name}'  #Genero nome file
        percorso = default_storage.save(nome_file, ContentFile(file.read()))  #Salvo file
        url = default_storage.url(percorso)  #Genero URL file

        prodotto.immagine_url = url  #Salvo URL nel prodotto
        prodotto.save()  #Aggiorno database

        return Response({  #Restituisco risposta
            'messaggio': 'Immagine caricata con successo',
            'immagine_url': url,
            'prodotto': ProdottoSerializer(prodotto).data,
        }, status=200)  #Status OK


# ─── Ordini ───────────────────────────────────────────────────────────────────

class OrdineListCreateView(generics.ListCreateAPIView):  #Lista e creazione ordini
    serializer_class = OrdineSerializer  #Serializer ordini
    permission_classes = [IsAuthenticated]  #Solo utenti autenticati

    def get_queryset(self):  #Query ordini dinamica
        if self.request.user.is_staff:  #Se admin
            queryset = Ordine.objects.all()  #Vede tutti
        else:
            queryset = Ordine.objects.filter(utente=self.request.user)  #Solo propri ordini

        data_da = self.request.query_params.get('data_da')  #Filtro data inizio
        data_a = self.request.query_params.get('data_a')  #Filtro data fine
        if data_da:  #Se presente
            queryset = queryset.filter(data_ordine__date__gte=data_da)  #Applico filtro
        if data_a:  #Se presente
            queryset = queryset.filter(data_ordine__date__lte=data_a)  #Applico filtro

        return queryset  #Ritorno queryset

    def perform_create(self, serializer):  #Override creazione
        serializer.save(utente=self.request.user)  #Associo utente loggato


class OrdineDetailView(generics.RetrieveAPIView):  #Dettaglio ordine
    serializer_class = OrdineSerializer  #Serializer ordine
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]  #Permessi

    def get_queryset(self):  #Query ordini
        if self.request.user.is_staff:  #Se admin
            return Ordine.objects.all()  #Tutti ordini
        return Ordine.objects.filter(utente=self.request.user)  #Solo propri ordini


class OrdineStatoView(APIView):  #Endpoint cambio stato ordine
    permission_classes = [IsAuthenticated, IsAdminUser]  #Solo admin

    def patch(self, request, pk):  #Metodo PATCH
        try:
            ordine = Ordine.objects.get(pk=pk)  #Cerco ordine
        except Ordine.DoesNotExist:  #Se non esiste
            return Response({'error': 'Ordine non trovato'}, status=404)  #Errore

        nuovo_stato = request.data.get('stato')  #Recupero nuovo stato
        stati_validi = ['in_attesa', 'in_preparazione', 'completato', 'annullato']  #Stati validi
        if nuovo_stato not in stati_validi:  #Controllo validità
            return Response({'error': 'Stato non valido'}, status=400)  #Errore

        ordine.stato = nuovo_stato  #Aggiorno stato
        ordine.save()  #Salvo modifica
        return Response(OrdineSerializer(ordine).data)  #Ritorno ordine aggiornato


# ─── Statistiche Admin ────────────────────────────────────────────────────────

class AdminStatsView(APIView):  #Endpoint statistiche admin
    permission_classes = [IsAuthenticated, IsAdminUser]  #Solo admin

    def get(self, request):  #Metodo GET

        righe_stati = (  #Query conteggio ordini per stato
            Ordine.objects
            .values('stato')
            .annotate(conteggio=Count('id'))
        )
        stato_map = {r['stato']: r['conteggio'] for r in righe_stati}  #Mappa stato->conteggio

        top = (  #Query prodotto più venduto
            OrdineProdotto.objects
            .values('prodotto__id', 'prodotto__nome', 'prodotto__prezzo')
            .annotate(unita_vendute=Sum('quantita'))
            .order_by('-unita_vendute')
            .first()
        )

        oggi = timezone.now().date()  #Recupero data odierna
        incasso_oggi = (  #Calcolo incasso giornaliero
            Ordine.objects
            .filter(stato='completato', data_ordine__date=oggi)
            .aggregate(totale=Sum('totale'))
        )['totale'] or 0  #Fallback a 0

        return Response({  #Risposta finale API
            'ordini_per_stato': {
                'in_attesa': stato_map.get('in_attesa', 0),
                'in_preparazione': stato_map.get('in_preparazione', 0),
                'completato': stato_map.get('completato', 0),
                'annullato': stato_map.get('annullato', 0),
            },
            'prodotto_piu_venduto': {
                'id': top['prodotto__id'],
                'nome': top['prodotto__nome'],
                'prezzo': top['prodotto__prezzo'],
                'unita_vendute': top['unita_vendute'],
            } if top else None,
            'incasso_oggi': round(incasso_oggi, 2),
        })  #Fine risposta