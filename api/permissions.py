from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS  #Importo classi e costanti per i permessi


class IsAdminOrReadOnly(BasePermission):  #Definisco permesso personalizzato admin o sola lettura
    """Lettura pubblica (GET, HEAD, OPTIONS). Scrittura solo per is_staff=True."""  #Descrizione comportamento permesso

    def has_permission(self, request, view):  #Definisco controllo permessi a livello di view
        if request.method in SAFE_METHODS:  #Se è una richiesta di sola lettura
            return True  #Consento accesso
        return request.user and request.user.is_staff  #Altrimenti consento solo se admin


class IsOwnerOrAdmin(BasePermission):  #Definisco permesso per proprietario o admin
    """Accesso all'oggetto solo al proprietario o agli admin."""  #Descrizione permesso

    def has_object_permission(self, request, view, obj):  #Controllo accesso al singolo oggetto
        if request.user.is_staff:  #Se l'utente è admin
            return True  #Consento sempre accesso
        return obj.utente == request.user  #Altrimenti controllo proprietà dell'oggetto


IsAdminUser = IsAdminUser  #Rinomino o rialloco IsAdminUser (ridondante, non necessario ma mantenuto)