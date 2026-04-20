from django.urls import path  #Importo funzione per definire URL
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView  #Importo viste JWT
from . import views  #Importo tutte le view locali

urlpatterns = [  #Definisco lista delle rotte API
    #Auth
    path('auth/register/',       views.RegisterView.as_view()),  #Endpoint registrazione utente
    path('auth/login/',          TokenObtainPairView.as_view()),  #Endpoint login JWT (access + refresh)
    path('auth/token/refresh/',  TokenRefreshView.as_view()),  #Endpoint refresh token JWT
    path('auth/me/',             views.MeView.as_view()),  #Endpoint dati utente autenticato

    #Categorie
    path('categorie/',           views.CategoriaListCreateView.as_view()),  #Lista e creazione categorie
    path('categorie/<int:pk>/',  views.CategoriaDetailView.as_view()),  #Dettaglio, update e delete categoria

    #Prodotti
    path('prodotti/',            views.ProdottoListCreateView.as_view()),  #Lista e creazione prodotti
    path('prodotti/<int:pk>/',   views.ProdottoDetailView.as_view()),  #Dettaglio prodotto
    path('prodotti/<int:pk>/immagine/', views.ProdottoImmagineView.as_view()),  #Upload immagine prodotto

    #Ordini
    path('ordini/',              views.OrdineListCreateView.as_view()),  #Lista e creazione ordini
    path('ordini/<int:pk>/',     views.OrdineDetailView.as_view()),  #Dettaglio ordine
    path('ordini/<int:pk>/stato/', views.OrdineStatoView.as_view()),  #Cambio stato ordine

    #Statistiche admin
    path('admin/stats/',         views.AdminStatsView.as_view()),  #Endpoint statistiche amministratore
]