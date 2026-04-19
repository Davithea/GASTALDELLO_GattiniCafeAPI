"""
Custom test runner per Gattini Cafe API.

Problema: i modelli Categoria, Prodotto, Ordine, OrdineProdotto hanno
managed = False, quindi Django non li crea nel DB di test.

Soluzione: sovrascriviamo setup_databases() per creare le tabelle
con SQL raw PRIMA che i test partano, disabilitando temporaneamente
i foreign key check di SQLite (richiesto dallo schema editor di Django).

Configurazione in settings.py:
    TEST_RUNNER = 'api.test_runner.UnmanagedTablesTestRunner'
"""

from django.test.runner import DiscoverRunner
from django.db import connection


CREATE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS categoria (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nome        VARCHAR(100) NOT NULL,
        descrizione TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS prodotto (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        nome         VARCHAR(200) NOT NULL,
        descrizione  TEXT,
        prezzo       REAL NOT NULL,
        disponibile  INTEGER NOT NULL DEFAULT 1,
        immagine_url VARCHAR(500),
        categoria_id INTEGER REFERENCES categoria(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ordine (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        utente_id   INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
        data_ordine DATETIME NOT NULL,
        stato       VARCHAR(20) NOT NULL DEFAULT 'in_attesa',
        totale      REAL NOT NULL DEFAULT 0,
        note        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ordine_prodotto (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ordine_id   INTEGER NOT NULL REFERENCES ordine(id) ON DELETE CASCADE,
        prodotto_id INTEGER NOT NULL REFERENCES prodotto(id) ON DELETE CASCADE,
        quantita    INTEGER NOT NULL
    )
    """,
]

DROP_STATEMENTS = [
    "DROP TABLE IF EXISTS ordine_prodotto",
    "DROP TABLE IF EXISTS ordine",
    "DROP TABLE IF EXISTS prodotto",
    "DROP TABLE IF EXISTS categoria",
]


class UnmanagedTablesTestRunner(DiscoverRunner):
    """
    Test runner che crea/distrugge le tabelle unmanaged
    attorno all'intera suite di test.
    """

    def setup_databases(self, **kwargs):
        # Prima chiama il setup standard (crea il DB di test con le tabelle managed)
        result = super().setup_databases(**kwargs)

        # Poi crea le nostre tabelle unmanaged via SQL raw
        # PRAGMA foreign_keys = OFF non serve perché usiamo IF NOT EXISTS
        # e creiamo nell'ordine corretto (padre prima del figlio)
        with connection.cursor() as cursor:
            for sql in CREATE_STATEMENTS:
                cursor.execute(sql)

        return result

    def teardown_databases(self, old_config, **kwargs):
        # Rimuove le tabelle unmanaged prima che Django distrugga il DB di test
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            for sql in DROP_STATEMENTS:
                cursor.execute(sql)
            cursor.execute("PRAGMA foreign_keys = ON")

        super().teardown_databases(old_config, **kwargs)