from django.urls import path #Importo la funzione path per definire i pattern degli URL
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView #Importo le view predefinite di Simple JWT per il login e il refresh del token
from . import views #Importo le view definite nella nostra app

urlpatterns = [ #Lista che contiene tutti i pattern URL dell'applicazione

    #Auth
    path('auth/register/', views.RegisterView.as_view()), #URL per la registrazione di un nuovo utente, non richiede autenticazione
    path('auth/login/', TokenObtainPairView.as_view()), #URL per il login, restituisce access token e refresh token
    path('auth/token/refresh/', TokenRefreshView.as_view()), #URL per rinnovare l'access token usando il refresh token
    path('auth/me/', views.MeView.as_view()), #URL per ottenere i dati dell'utente attualmente autenticato

    #Categorie
    path('categorie/', views.CategoriaListCreateView.as_view()), #URL per ottenere la lista delle categorie (GET pubblico) o crearne una nuova (POST solo admin)
    path('categorie/<int:pk>/', views.CategoriaDetailView.as_view()), #URL per ottenere, modificare o eliminare una singola categoria tramite il suo ID

    #Prodotti
    path('prodotti/', views.ProdottoListCreateView.as_view()), #URL per ottenere la lista dei prodotti (GET pubblico) o crearne uno nuovo (POST solo admin)
    path('prodotti/<int:pk>/', views.ProdottoDetailView.as_view()), #URL per ottenere, modificare o eliminare un singolo prodotto tramite il suo ID

    #Ordini
    path('ordini/', views.OrdineListCreateView.as_view()), #URL per ottenere la lista degli ordini o crearne uno nuovo, richiede autenticazione
    path('ordini/<int:pk>/', views.OrdineDetailView.as_view()), #URL per ottenere il dettaglio di un singolo ordine tramite il suo ID, richiede autenticazione
    path('ordini/<int:pk>/stato/', views.OrdineStatoView.as_view()), #URL per aggiornare lo stato di un ordine tramite il suo ID, richiede autenticazione admin
]