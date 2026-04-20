from pathlib import Path  #Importo Path per gestire i percorsi dei file in modo sicuro

BASE_DIR = Path(__file__).resolve().parent.parent  #Definisco la directory base del progetto risalendo di due livelli dal file corrente

SECRET_KEY = 'django-insecure-v5p)=)9_0jfhsdylch=k6vgm80wm2or2!3pk0c)b4=s60rjsis'  #Definisco la chiave segreta usata da Django per sicurezza crittografica

DEBUG = True  #Attivo la modalità debug per vedere errori dettagliati durante lo sviluppo

ALLOWED_HOSTS = []  #Definisco la lista degli host consentiti (vuota in sviluppo)

INSTALLED_APPS = [
    'django.contrib.admin',  #Aggiungo il pannello di amministrazione Django
    'django.contrib.auth',  #Aggiungo il sistema di autenticazione utenti
    'django.contrib.contenttypes',  #Aggiungo il supporto per tipi di contenuto
    'django.contrib.sessions',  #Aggiungo la gestione delle sessioni
    'django.contrib.messages',  #Aggiungo il sistema di messaggi
    'django.contrib.staticfiles',  #Aggiungo la gestione dei file statici
    'rest_framework',  #Aggiungo Django REST Framework per creare API
    'corsheaders',  #Aggiungo il supporto CORS per richieste da altri domini
    'api',  #Aggiungo la mia app personalizzata
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  #Abilito il middleware per gestire le richieste CORS
    'django.middleware.security.SecurityMiddleware',  #Aggiungo middleware per sicurezza generale
    'django.contrib.sessions.middleware.SessionMiddleware',  #Gestisco le sessioni degli utenti
    'django.middleware.common.CommonMiddleware',  #Aggiungo funzionalità comuni per richieste/risposte
    'django.middleware.csrf.CsrfViewMiddleware',  #Proteggo contro attacchi CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',  #Gestisco autenticazione utenti
    'django.contrib.messages.middleware.MessageMiddleware',  #Gestisco messaggi temporanei
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  #Proteggo contro attacchi clickjacking
]

ROOT_URLCONF = 'GASTALDELLO_GattiniCafeAPI.urls'  #Definisco il file principale delle URL del progetto

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  #Uso il backend template di Django
        'DIRS': [],  #Definisco eventuali directory personalizzate per template (vuoto)
        'APP_DIRS': True,  #Abilito la ricerca dei template nelle app installate
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',  #Aggiungo request al contesto
                'django.contrib.auth.context_processors.auth',  #Aggiungo informazioni utente al contesto
                'django.contrib.messages.context_processors.messages',  #Aggiungo messaggi al contesto
            ],
        },
    },
]

WSGI_APPLICATION = 'GASTALDELLO_GattiniCafeAPI.wsgi.application'  #Definisco l'applicazione WSGI per il deploy

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  #Uso SQLite come database
        'NAME': BASE_DIR / 'gattini_cafe.db',  #Definisco il percorso del database
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},  #Evito password simili ai dati utente
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},  #Imposto lunghezza minima password
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},  #Evito password comuni
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},  #Evito password solo numeriche
]

LANGUAGE_CODE = 'en-us'  #Imposto la lingua del progetto
TIME_ZONE = 'UTC'  #Imposto il fuso orario
USE_I18N = True  #Abilito internazionalizzazione
USE_TZ = True  #Abilito gestione timezone

STATIC_URL = 'static/'  #Definisco URL per file statici

MEDIA_URL = '/media/'  #Definisco URL per file media
MEDIA_ROOT = BASE_DIR / 'media'  #Definisco directory dei file media

CORS_ALLOW_ALL_ORIGINS = True  #Permetto richieste CORS da qualsiasi origine

TEST_RUNNER = 'api.test_runner.UnmanagedTablesTestRunner'  #Definisco un test runner personalizzato

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',  #Uso autenticazione JWT
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  #Richiedo autenticazione per default
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',  #Uso paginazione standard
    'PAGE_SIZE': 10,  #Definisco il numero di elementi per pagina
}