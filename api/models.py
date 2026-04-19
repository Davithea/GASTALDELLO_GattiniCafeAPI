from django.db import models #Importo il modulo models da Django
from django.contrib.auth.models import User #Importo il modello User built-in di Django per gestire gli utenti

class Categoria(models.Model): #Definisco il modello Categoria che estende la classe base Model di Django
    nome = models.CharField(max_length=100) #Campo testo per il nome della categoria con lunghezza massima 100 caratteri
    descrizione = models.TextField(blank=True, null=True) #Campo testo lungo per la descrizione, opzionale sia nel form che nel DB

    class Meta: #Classe interna per configurare il comportamento del modello
        ordering = ['id']
        managed = False #Dico a Django di non creare/modificare questa tabella, esiste già nel DB
        db_table = 'categoria' #Specifico il nome esatto della tabella nel database

    def __str__(self): #Metodo per la rappresentazione testuale dell'oggetto
        return self.nome #Restituisco il nome della categoria come stringa


class Prodotto(models.Model): #Definisco il modello Prodotto che estende la classe base Model di Django
    nome = models.CharField(max_length=200) #Campo testo per il nome del prodotto con lunghezza massima 200 caratteri
    descrizione = models.TextField(blank=True, null=True) #Campo testo lungo per la descrizione, opzionale sia nel form che nel DB
    prezzo = models.FloatField() #Campo numerico decimale per il prezzo del prodotto
    disponibile = models.BooleanField(default=True) #Campo booleano per indicare se il prodotto è disponibile, default True
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True) #Chiave esterna verso Categoria, se la categoria viene eliminata il campo diventa NULL
    immagine_url = models.CharField(max_length=500, blank=True, null=True) #Campo testo per l'URL dell'immagine, opzionale

    class Meta: #Classe interna per configurare il comportamento del modello
        ordering = ['id']
        managed = False #Dico a Django di non creare/modificare questa tabella, esiste già nel DB
        db_table = 'prodotto' #Specifico il nome esatto della tabella nel database

    def __str__(self): #Metodo per la rappresentazione testuale dell'oggetto
        return self.nome #Restituisco il nome del prodotto come stringa


class Ordine(models.Model): #Definisco il modello Ordine che estende la classe base Model di Django
    STATI = [ #Lista di tuple che definisce i valori possibili per il campo stato
        ('in_attesa', 'In Attesa'), #Stato iniziale dell'ordine appena creato
        ('in_preparazione', 'In Preparazione'), #Stato quando l'ordine è in lavorazione
        ('completato', 'Completato'), #Stato quando l'ordine è stato consegnato
        ('annullato', 'Annullato'), #Stato quando l'ordine è stato cancellato
    ]
    utente = models.ForeignKey(User, on_delete=models.CASCADE) #Chiave esterna verso l'utente, se l'utente viene eliminato vengono eliminati anche i suoi ordini
    data_ordine = models.DateTimeField(auto_now_add=True) #Campo data/ora impostato automaticamente al momento della creazione
    stato = models.CharField(max_length=20, choices=STATI, default='in_attesa') #Campo testo per lo stato, accetta solo i valori definiti in STATI, default in_attesa
    totale = models.FloatField(default=0) #Campo numerico decimale per il totale dell'ordine, calcolato automaticamente
    note = models.TextField(blank=True, null=True) #Campo testo per note speciali sull'ordine, opzionale

    class Meta: #Classe interna per configurare il comportamento del modello
        ordering = ['id']
        managed = False #Dico a Django di non creare/modificare questa tabella, esiste già nel DB
        db_table = 'ordine' #Specifico il nome esatto della tabella nel database

    def __str__(self): #Metodo per la rappresentazione testuale dell'oggetto
        return f"Ordine #{self.id} - {self.utente.username}" #Restituisco una stringa con id e username dell'utente


class OrdineProdotto(models.Model): #Definisco il modello OrdineProdotto, tabella ponte tra Ordine e Prodotto
    ordine = models.ForeignKey(Ordine, on_delete=models.CASCADE, related_name='prodotti') #Chiave esterna verso Ordine, se l'ordine viene eliminato vengono eliminati anche i suoi prodotti
    prodotto = models.ForeignKey(Prodotto, on_delete=models.CASCADE) #Chiave esterna verso Prodotto, se il prodotto viene eliminato vengono eliminati anche i riferimenti
    quantita = models.IntegerField() #Campo intero per la quantità del prodotto nell'ordine

    class Meta: #Classe interna per configurare il comportamento del modello
        ordering = ['id']
        managed = False #Dico a Django di non creare/modificare questa tabella, esiste già nel DB
        db_table = 'ordine_prodotto' #Specifico il nome esatto della tabella ponte nel database