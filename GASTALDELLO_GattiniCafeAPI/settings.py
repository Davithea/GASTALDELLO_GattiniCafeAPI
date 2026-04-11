from pathlib import Path #Importo Path per gestire i percorsi dei file in modo cross-platform

BASE_DIR = Path(__file__).resolve().parent.parent #Percorso base del progetto, usato per costruire tutti gli altri percorsi

SECRET_KEY = 'django-insecure-v5p)=)9_0jfhsdylch=k6vgm80wm2or2!3pk0c)b4=s60rjsis' #Chiave segreta usata da Django per firmare cookie e token, da cambiare in produzione

DEBUG = True #Modalità debug attiva, mostra errori dettagliati nel browser

ALLOWED_HOSTS = [] #Lista degli host autorizzati a servire l'applicazione, vuota in sviluppo

INSTALLED_APPS = [
    'django.contrib.admin', #Interfaccia di amministrazione di Django
    'django.contrib.auth', #Sistema di autenticazione built-in di Django
    'django.contrib.contenttypes', #Framework per i tipi di contenuto
    'django.contrib.sessions', #Gestione delle sessioni utente
    'django.contrib.messages', #Sistema di messaggi flash
    'django.contrib.staticfiles', #Gestione dei file statici
    'rest_framework', #Django REST Framework per la creazione delle API
    'corsheaders', #Gestione delle policy CORS per le richieste cross-origin
    'api', #La nostra applicazione con modelli, view e serializer
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', #Middleware CORS, deve stare PRIMA di tutti gli altri per funzionare correttamente
    'django.middleware.security.SecurityMiddleware', #Middleware per la sicurezza HTTP
    'django.contrib.sessions.middleware.SessionMiddleware', #Middleware per la gestione delle sessioni
    'django.middleware.common.CommonMiddleware', #Middleware per funzionalità comuni HTTP
    'django.middleware.csrf.CsrfViewMiddleware', #Middleware per la protezione CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', #Middleware per l'autenticazione utente
    'django.contrib.messages.middleware.MessageMiddleware', #Middleware per i messaggi flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware', #Middleware per la protezione dal clickjacking
]

ROOT_URLCONF = 'GASTALDELLO_GattiniCafeAPI.urls' #Modulo Python che contiene la configurazione principale degli URL

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates', #Uso il backend di template predefinito di Django
        'DIRS': [], #Cartelle aggiuntive dove cercare i template, vuota per ora
        'APP_DIRS': True, #Cerco automaticamente i template nelle cartelle templates/ di ogni app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request', #Aggiunge la request al contesto
                'django.contrib.auth.context_processors.auth', #Aggiunge i dati utente al contesto
                'django.contrib.messages.context_processors.messages', #Aggiunge i messaggi flash al contesto
            ],
        },
    },
]

WSGI_APPLICATION = 'GASTALDELLO_GattiniCafeAPI.wsgi.application' #Percorso dell'applicazione WSGI per il deployment

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', #Uso SQLite come motore del database
        'NAME': BASE_DIR / 'gattini_cafe.db', #Percorso del file database fornito dall'esercizio
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, #Impedisce password simili ai dati dell'utente
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, #Impone una lunghezza minima per la password
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, #Blocca le password troppo comuni
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}, #Blocca le password composte solo da numeri
]

LANGUAGE_CODE = 'en-us' #Lingua predefinita dell'applicazione

TIME_ZONE = 'UTC' #Fuso orario usato per le date nel database

USE_I18N = True #Abilito il sistema di internazionalizzazione di Django

USE_TZ = True #Abilito il supporto ai fusi orari nelle date

STATIC_URL = 'static/' #URL base per i file statici

CORS_ALLOW_ALL_ORIGINS = True #Permetto richieste da qualsiasi origine, va bene solo in sviluppo

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication', #Uso JWT come metodo di autenticazione predefinito
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated', #Per default tutti gli endpoint richiedono autenticazione, salvo override nelle singole view
    ),
}