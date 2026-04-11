#!/usr/bin/env python #Indica al sistema operativo di usare Python per eseguire questo script
"""Django's command-line utility for administrative tasks."""
import os #Importo il modulo os per interagire con il sistema operativo
import sys #Importo il modulo sys per accedere agli argomenti passati da riga di comando


def main(): #Funzione principale che avvia i comandi di gestione Django
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GASTALDELLO_GattiniCafeAPI.settings') #Imposto la variabile d'ambiente che indica a Django quale file settings.py usare
    try:
        from django.core.management import execute_from_command_line #Importo la funzione che esegue i comandi Django (runserver, migrate, ecc.)
    except ImportError as exc:
        raise ImportError( #Sollevo un errore chiaro se Django non è installato o il virtualenv non è attivo
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv) #Eseguo il comando Django passato come argomento dalla riga di comando


if __name__ == '__main__': #Controllo che lo script venga eseguito direttamente e non importato come modulo
    main() #Chiamo la funzione principale