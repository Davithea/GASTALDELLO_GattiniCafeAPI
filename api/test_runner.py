from django.test.runner import DiscoverRunner  #Importo il test runner base di Django
from django.db import connection  #Importo la connessione al database


CREATE_STATEMENTS = [  #Definisco le query SQL per creare tabelle
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

DROP_STATEMENTS = [  #Definisco le query SQL per eliminare le tabelle
    "DROP TABLE IF EXISTS ordine_prodotto",
    "DROP TABLE IF EXISTS ordine",
    "DROP TABLE IF EXISTS prodotto",
    "DROP TABLE IF EXISTS categoria",
]


class UnmanagedTablesTestRunner(DiscoverRunner):  #Definisco un test runner personalizzato

    """
    Test runner che crea/distrugge le tabelle unmanaged
    attorno all'intera suite di test.
    """

    def setup_databases(self, **kwargs):  #Override setup database di test
        result = super().setup_databases(**kwargs)  #Eseguo setup standard Django

        with connection.cursor() as cursor:  #Apro cursore database
            for sql in CREATE_STATEMENTS:  #Itero query di creazione
                cursor.execute(sql)  #Eseguo creazione tabella

        return result  #Ritorno configurazione database

    def teardown_databases(self, old_config, **kwargs):  #Override teardown database
        with connection.cursor() as cursor:  #Apro cursore database
            cursor.execute("PRAGMA foreign_keys = OFF")  #Disabilito vincoli foreign key

            for sql in DROP_STATEMENTS:  #Itero query di drop
                cursor.execute(sql)  #Elimino tabella

            cursor.execute("PRAGMA foreign_keys = ON")  #Riabilito foreign key

        super().teardown_databases(old_config, **kwargs)  #Chiamo teardown standard Django