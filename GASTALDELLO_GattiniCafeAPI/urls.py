from django.contrib import admin #Importo il modulo admin di Django per gestire il pannello di amministrazione
from django.urls import path, include #Importo path per definire gli URL e include per collegare altri file di URL

urlpatterns = [ #Lista che contiene tutti i pattern URL principali del progetto
    path('admin/', admin.site.urls), #URL per accedere al pannello di amministrazione di Django
    path('api/', include('api.urls')), #URL base per tutte le API, rimanda al file urls.py della nostra app
]