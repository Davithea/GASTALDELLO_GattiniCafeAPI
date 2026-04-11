from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated #Importo le classi base per i permessi, i metodi sicuri e il permesso di autenticazione

class IsAdminOrReadOnly(BasePermission): #Definisco un permesso personalizzato che estende BasePermission
    """Lettura pubblica senza auth, scrittura solo admin."""
    def has_permission(self, request, view): #Metodo chiamato da Django REST Framework per verificare il permesso
        if request.method in SAFE_METHODS: #Controllo se il metodo della richiesta è tra quelli sicuri (GET, HEAD, OPTIONS)
            return True #Se è una lettura la permetto a tutti senza autenticazione
        return request.user and request.user.is_authenticated and request.user.is_staff #Per la scrittura verifico che l'utente esista, sia autenticato e sia admin

class IsOwnerOrAdmin(BasePermission): #Definisco un permesso personalizzato per controllare la proprietà degli oggetti
    """Accesso solo al proprietario dell'ordine o all'admin."""
    def has_object_permission(self, request, view, obj): #Metodo chiamato per verificare il permesso su un oggetto specifico
        return obj.utente == request.user or request.user.is_staff #Permetto l'accesso solo se l'utente è il proprietario dell'ordine oppure è admin