from rest_framework import routers
from api.v1.viewsets import *


router = routers.DefaultRouter()

router.register("sorteios", SorteioViewSet, basename="sorteios")
router.register("compras", ComprarViewSet, basename="compras")
router.register("raspadinhas", RaspadinhaViewSet, basename="raspadinhas")
