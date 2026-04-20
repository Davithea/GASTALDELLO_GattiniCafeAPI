from rest_framework import serializers  #Importo serializers da Django REST Framework
from django.contrib.auth.models import User  #Importo il modello User
from .models import Categoria, Prodotto, Ordine, OrdineProdotto  #Importo i modelli della mia app


class CategoriaSerializer(serializers.ModelSerializer):  #Definisco serializer per Categoria
    class Meta:  #Configuro il serializer
        model = Categoria  #Associo il modello Categoria
        fields = '__all__'  #Includo tutti i campi del modello


class ProdottoSerializer(serializers.ModelSerializer):  #Definisco serializer per Prodotto
    class Meta:  #Configuro il serializer
        model = Prodotto  #Associo il modello Prodotto
        fields = '__all__'  #Includo tutti i campi


class OrdineProdottoInputSerializer(serializers.Serializer):  #Definisco serializer per input prodotti ordine
    prodotto_id = serializers.PrimaryKeyRelatedField(queryset=Prodotto.objects.all())  #Collego un prodotto tramite ID
    quantita = serializers.IntegerField(min_value=1)  #Definisco quantità minima 1


class OrdineSerializer(serializers.ModelSerializer):  #Definisco serializer per Ordine
    prodotti = OrdineProdottoInputSerializer(many=True, write_only=True)  #Campo prodotti solo in scrittura
    prodotti_dettaglio = serializers.SerializerMethodField(read_only=True)  #Campo calcolato per dettagli prodotti

    class Meta:  #Configuro il serializer
        model = Ordine  #Associo il modello Ordine
        fields = ['id', 'utente', 'stato', 'totale', 'note', 'data_ordine', 'prodotti', 'prodotti_dettaglio']  #Definisco i campi
        read_only_fields = ['totale', 'stato', 'data_ordine', 'utente']  #Campi non modificabili

    def get_prodotti_dettaglio(self, obj):  #Metodo per costruire dettagli prodotti
        items = OrdineProdotto.objects.filter(ordine=obj)  #Recupero prodotti associati all'ordine
        return [  #Ritorno lista dettagli
            {
                'prodotto_id': item.prodotto.id,  #ID prodotto
                'nome': item.prodotto.nome,  #Nome prodotto
                'prezzo': item.prodotto.prezzo,  #Prezzo prodotto
                'quantita': item.quantita,  #Quantità ordinata
                'subtotale': item.prodotto.prezzo * item.quantita  #Calcolo subtotale
            }
            for item in items  #Itero ogni prodotto ordine
        ]

    def create(self, validated_data):  #Metodo per creare un ordine
        prodotti_data = validated_data.pop('prodotti')  #Estraggo prodotti dal payload
        totale = 0  #Inizializzo totale
        ordine = Ordine.objects.create(**validated_data)  #Creo ordine base

        for item in prodotti_data:  #Itero sui prodotti
            prodotto = item['prodotto_id']  #Recupero prodotto
            quantita = item['quantita']  #Recupero quantità
            totale += prodotto.prezzo * quantita  #Aggiorno totale
            OrdineProdotto.objects.create(ordine=ordine, prodotto=prodotto, quantita=quantita)  #Creo relazione ordine-prodotto

        ordine.totale = totale  #Salvo totale calcolato
        ordine.save()  #Aggiorno ordine nel database
        return ordine  #Ritorno ordine creato


class UserSerializer(serializers.ModelSerializer):  #Definisco serializer per utente
    class Meta:  #Configuro serializer
        model = User  #Associo modello User
        fields = ['id', 'username', 'email', 'is_staff']  #Definisco campi esposti