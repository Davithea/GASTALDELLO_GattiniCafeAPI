from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser  # ✅ BONUS: per upload immagine
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Sum, Count  # ✅ BONUS: aggregazioni per statistiche
from django.utils import timezone        # ✅ BONUS: data odierna per incasso giornaliero
import os

from .models import Categoria, Prodotto, Ordine, OrdineProdotto
from .serializers import (
    CategoriaSerializer, ProdottoSerializer,
    OrdineSerializer, UserSerializer
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response({'error': 'Username e password obbligatori'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username già esistente'}, status=400)

        user = User.objects.create_user(username=username, password=password, email=email)
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=201)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ─── Categorie ────────────────────────────────────────────────────────────────

class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]


# ─── Prodotti ─────────────────────────────────────────────────────────────────

class ProdottoListCreateView(generics.ListCreateAPIView):
    serializer_class = ProdottoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'descrizione']

    def get_queryset(self):
        queryset = Prodotto.objects.all()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        disponibile = self.request.query_params.get('disponibile')
        if disponibile == 'true':
            queryset = queryset.filter(disponibile=True)
        return queryset


class ProdottoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Prodotto.objects.all()
    serializer_class = ProdottoSerializer
    permission_classes = [IsAdminOrReadOnly]


# ✅ BONUS: upload immagine prodotto
# POST /api/prodotti/{id}/immagine/  — multipart/form-data, campo "immagine"
# Richiede autenticazione JWT + is_staff=True
class ProdottoImmagineView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            prodotto = Prodotto.objects.get(pk=pk)
        except Prodotto.DoesNotExist:
            return Response({'error': 'Prodotto non trovato'}, status=404)

        file = request.FILES.get('immagine')
        if not file:
            return Response({'error': 'Nessun file ricevuto. Usa il campo "immagine".'}, status=400)

        estensioni_ammesse = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        _, estensione = os.path.splitext(file.name.lower())
        if estensione not in estensioni_ammesse:
            return Response({
                'error': f'Formato non supportato. Ammessi: {", ".join(estensioni_ammesse)}'
            }, status=400)

        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        # Salvo il file come media/prodotti/prodotto_<id>_<nomeoriginale>
        nome_file = f'prodotti/prodotto_{pk}_{file.name}'
        percorso = default_storage.save(nome_file, ContentFile(file.read()))
        url = default_storage.url(percorso)

        prodotto.immagine_url = url
        prodotto.save()

        return Response({
            'messaggio': 'Immagine caricata con successo',
            'immagine_url': url,
            'prodotto': ProdottoSerializer(prodotto).data,
        }, status=200)


# ─── Ordini ───────────────────────────────────────────────────────────────────

class OrdineListCreateView(generics.ListCreateAPIView):
    serializer_class = OrdineSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = Ordine.objects.all()
        else:
            queryset = Ordine.objects.filter(utente=self.request.user)

        data_da = self.request.query_params.get('data_da')
        data_a = self.request.query_params.get('data_a')
        if data_da:
            queryset = queryset.filter(data_ordine__date__gte=data_da)
        if data_a:
            queryset = queryset.filter(data_ordine__date__lte=data_a)

        return queryset

    def perform_create(self, serializer):
        serializer.save(utente=self.request.user)


class OrdineDetailView(generics.RetrieveAPIView):
    serializer_class = OrdineSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Ordine.objects.all()
        return Ordine.objects.filter(utente=self.request.user)


class OrdineStatoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, pk):
        try:
            ordine = Ordine.objects.get(pk=pk)
        except Ordine.DoesNotExist:
            return Response({'error': 'Ordine non trovato'}, status=404)

        nuovo_stato = request.data.get('stato')
        stati_validi = ['in_attesa', 'in_preparazione', 'completato', 'annullato']
        if nuovo_stato not in stati_validi:
            return Response({'error': f'Stato non valido. Scegli tra: {stati_validi}'}, status=400)

        ordine.stato = nuovo_stato
        ordine.save()
        return Response(OrdineSerializer(ordine).data)


# ─── Statistiche Admin ────────────────────────────────────────────────────────

# ✅ BONUS: GET /api/admin/stats/
# Richiede JWT + is_staff=True
# Risposta:
#   ordini_per_stato   — conteggio ordini per ciascuno dei 4 stati
#   prodotto_piu_venduto — prodotto con più unità totali ordinate
#   incasso_oggi       — somma dei totali degli ordini "completato" di oggi
class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 1. Ordini per stato
        righe_stati = (
            Ordine.objects
            .values('stato')
            .annotate(conteggio=Count('id'))
        )
        stato_map = {r['stato']: r['conteggio'] for r in righe_stati}

        # 2. Prodotto più venduto per unità totali
        top = (
            OrdineProdotto.objects
            .values('prodotto__id', 'prodotto__nome', 'prodotto__prezzo')
            .annotate(unita_vendute=Sum('quantita'))
            .order_by('-unita_vendute')
            .first()
        )

        # 3. Incasso ordini completati oggi
        oggi = timezone.now().date()
        incasso_oggi = (
            Ordine.objects
            .filter(stato='completato', data_ordine__date=oggi)
            .aggregate(totale=Sum('totale'))
        )['totale'] or 0

        return Response({
            'ordini_per_stato': {
                'in_attesa':        stato_map.get('in_attesa', 0),
                'in_preparazione':  stato_map.get('in_preparazione', 0),
                'completato':       stato_map.get('completato', 0),
                'annullato':        stato_map.get('annullato', 0),
            },
            'prodotto_piu_venduto': {
                'id':            top['prodotto__id'],
                'nome':          top['prodotto__nome'],
                'prezzo':        top['prodotto__prezzo'],
                'unita_vendute': top['unita_vendute'],
            } if top else None,
            'incasso_oggi': round(incasso_oggi, 2),
        })