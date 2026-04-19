from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Categoria, Prodotto, Ordine, OrdineProdotto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class ProdottoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prodotto
        fields = '__all__'


class OrdineProdottoInputSerializer(serializers.Serializer):
    prodotto_id = serializers.PrimaryKeyRelatedField(queryset=Prodotto.objects.all())
    quantita = serializers.IntegerField(min_value=1)


class OrdineSerializer(serializers.ModelSerializer):
    prodotti = OrdineProdottoInputSerializer(many=True, write_only=True)
    prodotti_dettaglio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ordine
        # ✅ FIX: aggiunto 'utente' per mostrare il proprietario nelle risposte in lettura
        fields = ['id', 'utente', 'stato', 'totale', 'note', 'data_ordine', 'prodotti', 'prodotti_dettaglio']
        read_only_fields = ['totale', 'stato', 'data_ordine', 'utente']  # utente è read-only: lo assegna la view

    def get_prodotti_dettaglio(self, obj):
        items = OrdineProdotto.objects.filter(ordine=obj)
        return [
            {
                'prodotto_id': item.prodotto.id,
                'nome': item.prodotto.nome,
                'prezzo': item.prodotto.prezzo,
                'quantita': item.quantita,
                'subtotale': item.prodotto.prezzo * item.quantita
            }
            for item in items
        ]

    def create(self, validated_data):
        prodotti_data = validated_data.pop('prodotti')
        totale = 0
        ordine = Ordine.objects.create(**validated_data)
        for item in prodotti_data:
            prodotto = item['prodotto_id']
            quantita = item['quantita']
            totale += prodotto.prezzo * quantita
            OrdineProdotto.objects.create(ordine=ordine, prodotto=prodotto, quantita=quantita)
        ordine.totale = totale
        ordine.save()
        return ordine


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']