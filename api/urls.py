from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [

    # Auth
    path('auth/register/',       views.RegisterView.as_view()),
    path('auth/login/',          TokenObtainPairView.as_view()),
    path('auth/token/refresh/',  TokenRefreshView.as_view()),
    path('auth/me/',             views.MeView.as_view()),

    # Categorie
    path('categorie/',           views.CategoriaListCreateView.as_view()),
    path('categorie/<int:pk>/',  views.CategoriaDetailView.as_view()),

    # Prodotti
    path('prodotti/',            views.ProdottoListCreateView.as_view()),
    path('prodotti/<int:pk>/',   views.ProdottoDetailView.as_view()),
    # ✅ BONUS: upload immagine prodotto
    path('prodotti/<int:pk>/immagine/', views.ProdottoImmagineView.as_view()),

    # Ordini
    path('ordini/',              views.OrdineListCreateView.as_view()),
    path('ordini/<int:pk>/',     views.OrdineDetailView.as_view()),
    path('ordini/<int:pk>/stato/', views.OrdineStatoView.as_view()),

    # ✅ BONUS: statistiche admin
    path('admin/stats/',         views.AdminStatsView.as_view()),
]