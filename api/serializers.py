from rest_framework import serializers #Importo il modulo serializers di Django REST Framework
from django.contrib.auth.models import User #Importo il modello User built-in di Django per gestire gli utenti
from .models import Categoria, Prodotto, Ordine, OrdineProdotto #Importo tutti i modelli definiti nella nostra app


class CategoriaSerializer(serializers.ModelSerializer): #Definisco il serializer per il modello Categoria
    class Meta: #Classe interna per configurare il serializer
        model = Categoria #Specifico il modello da serializzare
        fields = '__all__' #Includo tutti i campi del modello nella serializzazione


class ProdottoSerializer(serializers.ModelSerializer): #Definisco il serializer per il modello Prodotto
    class Meta: #Classe interna per configurare il serializer
        model = Prodotto #Specifico il modello da serializzare
        fields = '__all__' #Includo tutti i campi del modello nella serializzazione


class OrdineProdottoInputSerializer(serializers.Serializer): #Definisco il serializer per i prodotti in ingresso nell'ordine, non legato a un modello
    prodotto_id = serializers.PrimaryKeyRelatedField(queryset=Prodotto.objects.all()) #Campo che accetta un ID e lo converte automaticamente nell'oggetto Prodotto corrispondente
    quantita = serializers.IntegerField(min_value=1) #Campo intero per la quantità, deve essere almeno 1


class OrdineSerializer(serializers.ModelSerializer): #Definisco il serializer per il modello Ordine
    prodotti = OrdineProdottoInputSerializer(many=True, write_only=True) #Campo per ricevere la lista di prodotti in ingresso, solo in scrittura
    prodotti_dettaglio = serializers.SerializerMethodField(read_only=True) #Campo calcolato per mostrare i dettagli dei prodotti, solo in lettura

    class Meta: #Classe interna per configurare il serializer
        model = Ordine #Specifico il modello da serializzare
        fields = ['id', 'stato', 'totale', 'note', 'data_ordine', 'prodotti', 'prodotti_dettaglio'] #Elenco esplicito dei campi da includere
        read_only_fields = ['totale', 'stato', 'data_ordine'] #Questi campi non possono essere modificati dall'utente in ingresso

    def get_prodotti_dettaglio(self, obj): #Metodo chiamato automaticamente da SerializerMethodField per costruire il campo prodotti_dettaglio
        items = OrdineProdotto.objects.filter(ordine=obj) #Recupero tutti i prodotti associati a questo ordine dal database
        return [ #Restituisco una lista di dizionari con i dettagli di ogni prodotto
            {
                'prodotto_id': item.prodotto.id, #ID del prodotto
                'nome': item.prodotto.nome, #Nome del prodotto
                'prezzo': item.prodotto.prezzo, #Prezzo unitario del prodotto
                'quantita': item.quantita, #Quantità ordinata
                'subtotale': item.prodotto.prezzo * item.quantita #Subtotale calcolato moltiplicando prezzo per quantità
            }
            for item in items #Itero su ogni riga della tabella ponte OrdineProdotto
        ]

    def create(self, validated_data): #Metodo chiamato quando si crea un nuovo ordine tramite POST
        prodotti_data = validated_data.pop('prodotti') #Estraggo e rimuovo la lista prodotti dai dati validati
        totale = 0 #Inizializzo il totale a zero
        ordine = Ordine.objects.create(**validated_data) #Creo l'ordine nel database con i dati rimanenti
        for item in prodotti_data: #Itero su ogni prodotto ricevuto nel payload
            prodotto = item['prodotto_id'] #Recupero l'oggetto Prodotto già risolto da PrimaryKeyRelatedField
            quantita = item['quantita'] #Recupero la quantità richiesta
            totale += prodotto.prezzo * quantita #Aggiungo al totale il subtotale di questo prodotto
            OrdineProdotto.objects.create(ordine=ordine, prodotto=prodotto, quantita=quantita) #Creo la riga nella tabella ponte OrdineProdotto
        ordine.totale = totale #Assegno il totale calcolato all'ordine
        ordine.save() #Salvo l'ordine aggiornato nel database
        return ordine #Restituisco l'ordine creato


class UserSerializer(serializers.ModelSerializer): #Definisco il serializer per il modello User di Django
    class Meta: #Classe interna per configurare il serializer
        model = User #Specifico il modello User built-in di Django
        fields = ['id', 'username', 'email', 'is_staff'] #Includo solo questi campi, escludendo la password per sicurezza