from rest_framework.permissions import BasePermission, IsAdminUser, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Lettura pubblica (GET, HEAD, OPTIONS). Scrittura solo per is_staff=True."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(BasePermission):
    """Accesso all'oggetto solo al proprietario o agli admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.utente == request.user


# ✅ FIX: ri-esporto IsAdminUser da DRF così la view lo importa da un unico punto
# (evita di fare il controllo is_staff manualmente nella view)
IsAdminUser = IsAdminUser