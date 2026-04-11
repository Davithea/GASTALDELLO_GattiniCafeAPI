from rest_framework import generics, filters #Importo generics per le view predefinite e filters per la ricerca
from rest_framework.views import APIView #Importo APIView per creare view personalizzate
from rest_framework.response import Response #Importo Response per restituire risposte HTTP
from rest_framework.permissions import IsAuthenticated, AllowAny #Importo i permessi predefiniti di DRF
from rest_framework_simplejwt.tokens import RefreshToken #Importo RefreshToken per generare i token JWT
from django.contrib.auth.models import User #Importo il modello User built-in di Django

from .models import Categoria, Prodotto, Ordine #Importo i modelli definiti nella nostra app
from .serializers import ( #Importo i serializer definiti nella nostra app
    CategoriaSerializer, ProdottoSerializer,
    OrdineSerializer, UserSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin #Importo i permessi personalizzati definiti nella nostra app


#Auth

class RegisterView(APIView): #View per la registrazione di un nuovo utente
    permission_classes = [AllowAny] #Permetto l'accesso a tutti senza autenticazione

    def post(self, request): #Metodo chiamato quando arriva una richiesta POST
        username = request.data.get('username') #Estraggo il campo username dal body della richiesta
        password = request.data.get('password') #Estraggo il campo password dal body della richiesta
        email = request.data.get('email', '') #Estraggo il campo email dal body della richiesta, opzionale

        if not username or not password: #Controllo che username e password siano presenti
            return Response({'error': 'Username e password obbligatori'}, status=400) #Restituisco errore 400 se mancano

        if User.objects.filter(username=username).exists(): #Controllo se esiste già un utente con questo username
            return Response({'error': 'Username già esistente'}, status=400) #Restituisco errore 400 se username già usato

        user = User.objects.create_user(username=username, password=password, email=email) #Creo il nuovo utente nel database con la password hashata
        refresh = RefreshToken.for_user(user) #Genero i token JWT per il nuovo utente

        return Response({ #Restituisco i dati dell'utente e i token generati
            'user': UserSerializer(user).data, #Dati dell'utente serializzati
            'access': str(refresh.access_token), #Token di accesso da usare nelle richieste protette
            'refresh': str(refresh), #Token di refresh per rinnovare l'access token
        }, status=201) #Codice 201 indica che la risorsa è stata creata con successo


class MeView(APIView): #View per ottenere i dati dell'utente attualmente autenticato
    permission_classes = [IsAuthenticated] #Solo gli utenti autenticati possono accedere

    def get(self, request): #Metodo chiamato quando arriva una richiesta GET
        return Response(UserSerializer(request.user).data) #Restituisco i dati dell'utente corrente serializzati


#Categorie

class CategoriaListCreateView(generics.ListCreateAPIView): #View per listare tutte le categorie o crearne una nuova
    queryset = Categoria.objects.all() #Recupero tutte le categorie dal database
    serializer_class = CategoriaSerializer #Uso il serializer delle categorie
    permission_classes = [IsAdminOrReadOnly] #Lettura pubblica, scrittura solo admin


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView): #View per ottenere, modificare o eliminare una singola categoria
    queryset = Categoria.objects.all() #Recupero tutte le categorie dal database
    serializer_class = CategoriaSerializer #Uso il serializer delle categorie
    permission_classes = [IsAdminOrReadOnly] #Lettura pubblica, scrittura solo admin


#Prodotti

class ProdottoListCreateView(generics.ListCreateAPIView): #View per listare tutti i prodotti o crearne uno nuovo
    serializer_class = ProdottoSerializer #Uso il serializer dei prodotti
    permission_classes = [IsAdminOrReadOnly] #Lettura pubblica, scrittura solo admin
    filter_backends = [filters.SearchFilter] #Abilito il filtro di ricerca testuale
    search_fields = ['nome', 'descrizione'] #Definisco i campi su cui effettuare la ricerca con ?search=

    def get_queryset(self): #Metodo per personalizzare il queryset in base ai parametri della richiesta
        queryset = Prodotto.objects.all() #Parto con tutti i prodotti

        categoria = self.request.query_params.get('categoria') #Leggo il parametro ?categoria= dalla URL
        if categoria: #Se il parametro è presente
            queryset = queryset.filter(categoria_id=categoria) #Filtro i prodotti per categoria

        disponibile = self.request.query_params.get('disponibile') #Leggo il parametro ?disponibile= dalla URL
        if disponibile == 'true': #Se il parametro è 'true'
            queryset = queryset.filter(disponibile=True) #Filtro solo i prodotti disponibili

        return queryset #Restituisco il queryset filtrato


class ProdottoDetailView(generics.RetrieveUpdateDestroyAPIView): #View per ottenere, modificare o eliminare un singolo prodotto
    queryset = Prodotto.objects.all() #Recupero tutti i prodotti dal database
    serializer_class = ProdottoSerializer #Uso il serializer dei prodotti
    permission_classes = [IsAdminOrReadOnly] #Lettura pubblica, scrittura solo admin


#Ordini

class OrdineListCreateView(generics.ListCreateAPIView): #View per listare gli ordini o crearne uno nuovo
    serializer_class = OrdineSerializer #Uso il serializer degli ordini
    permission_classes = [IsAuthenticated] #Solo gli utenti autenticati possono accedere

    def get_queryset(self): #Metodo per personalizzare il queryset in base al ruolo dell'utente
        if self.request.user.is_staff: #Se l'utente è admin
            return Ordine.objects.all() #Restituisco tutti gli ordini
        return Ordine.objects.filter(utente=self.request.user) #Altrimenti restituisco solo gli ordini dell'utente corrente

    def perform_create(self, serializer): #Metodo chiamato automaticamente durante la creazione di un ordine
        serializer.save(utente=self.request.user) #Assegno automaticamente l'utente loggato come proprietario dell'ordine


class OrdineDetailView(generics.RetrieveAPIView): #View per ottenere il dettaglio di un singolo ordine
    serializer_class = OrdineSerializer #Uso il serializer degli ordini
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin] #Solo autenticati e solo se proprietari o admin

    def get_queryset(self): #Metodo per personalizzare il queryset in base al ruolo dell'utente
        if self.request.user.is_staff: #Se l'utente è admin
            return Ordine.objects.all() #Restituisco tutti gli ordini
        return Ordine.objects.filter(utente=self.request.user) #Altrimenti restituisco solo gli ordini dell'utente corrente


class OrdineStatoView(APIView): #View personalizzata per aggiornare lo stato di un ordine
    permission_classes = [IsAuthenticated] #Solo gli utenti autenticati possono accedere

    def patch(self, request, pk): #Metodo chiamato quando arriva una richiesta PATCH
        if not request.user.is_staff: #Controllo se l'utente è admin
            return Response({'error': 'Solo gli admin possono cambiare lo stato'}, status=403) #Restituisco errore 403 se non è admin

        try:
            ordine = Ordine.objects.get(pk=pk) #Cerco l'ordine nel database tramite il suo ID
        except Ordine.DoesNotExist: #Se l'ordine non esiste
            return Response({'error': 'Ordine non trovato'}, status=404) #Restituisco errore 404

        nuovo_stato = request.data.get('stato') #Estraggo il nuovo stato dal body della richiesta
        stati_validi = ['in_attesa', 'in_preparazione', 'completato', 'annullato'] #Lista degli stati ammessi

        if nuovo_stato not in stati_validi: #Controllo che lo stato inviato sia tra quelli validi
            return Response({'error': f'Stato non valido. Scegli tra: {stati_validi}'}, status=400) #Restituisco errore 400 se lo stato non è valido

        ordine.stato = nuovo_stato #Aggiorno lo stato dell'ordine
        ordine.save() #Salvo le modifiche nel database
        return Response(OrdineSerializer(ordine).data) #Restituisco l'ordine aggiornato serializzato