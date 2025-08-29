from rest_framework import viewsets, permissions
from api.models import (
    User, SiteConfig, Sorteio, SorteioNumero,
    Comprar, Raspadinha
)
from .serializers import (
    UserSerializer, SiteConfigSerializer, SorteioSerializer,
    SorteioNumeroSerializer, ComprarSerializer, RaspadinhaSerializer
)


# --------------------------
# Usuários
# --------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


# --------------------------
# Configuração do Site
# --------------------------
class SiteConfigViewSet(viewsets.ModelViewSet):
    queryset = SiteConfig.objects.all()
    serializer_class = SiteConfigSerializer
    permission_classes = [permissions.IsAdminUser]


# --------------------------
# Sorteio + Números
# --------------------------
class SorteioViewSet(viewsets.ModelViewSet):
    queryset = Sorteio.objects.all()
    serializer_class = SorteioSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)


class SorteioNumeroViewSet(viewsets.ModelViewSet):
    queryset = SorteioNumero.objects.all()
    serializer_class = SorteioNumeroSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(proprietario=self.request.user)


# --------------------------
# Comprar
# --------------------------
class ComprarViewSet(viewsets.ModelViewSet):
    queryset = Comprar.objects.all()
    serializer_class = ComprarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# --------------------------
# Raspadinha
# --------------------------
class RaspadinhaViewSet(viewsets.ModelViewSet):
    queryset = Raspadinha.objects.all()
    serializer_class = RaspadinhaSerializer
    #permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
