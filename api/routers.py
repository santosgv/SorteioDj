from rest_framework import routers
from api.views import *

router = routers.DefaultRouter()

router.register("raffles", RaffleViewSet, basename="raffles")
router.register("purchases", PurchaseViewSet, basename="purchases")
router.register("scratchcards", ScratchCardViewSet, basename="scratchcards")
router.register("affiliate/links", AffiliateLinkViewSet, basename="affiliate-links")
router.register("affiliate/commissions", CommissionViewSet, basename="affiliate-commissions")
router.register("admin/commissions", AdminCommissionViewSet, basename="admin-commissions")
router.register("admin/withdrawals", AdminWithdrawalViewSet, basename="admin-withdrawals")
router.register("withdrawals", WithdrawalViewSet, basename="withdrawals")