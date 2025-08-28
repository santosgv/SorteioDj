from rest_framework import viewsets, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from api.models import *
from api.v1.serializers import *
#from .services import reveal_scratchcard  # onde você colocou o helper

class IsAdmin(permissions.IsAdminUser):
    pass


class RaffleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Raffle.objects.all().select_related("created_by")
    serializer_class = RaffleSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=["get"])
    def numbers(self, request, pk=None):
        raffle = self.get_object()
        qs = raffle.numbers.filter(status=RaffleNumber.Status.AVAILABLE).only("id", "number", "status")
        return Response(RaffleNumberSerializer(qs, many=True).data)


class PurchaseViewSet(mixins.CreateModelMixin,
                      mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user).select_related("raffle")

    def get_serializer_class(self):
        return PurchaseCreateSerializer if self.action == "create" else PurchaseSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def mark_paid(self, request, pk=None):
        """Endpoint para webhooks/admin marcar como paga."""
        purchase = self.get_object()
        if purchase.status == Purchase.Status.PAID:
            return Response({"detail": "Já pago."})
        purchase.status = Purchase.Status.PAID
        purchase.payment_ref = request.data.get("payment_ref", "")
        purchase.save(update_fields=["status", "payment_ref"])
        return Response(PurchaseSerializer(purchase).data)


class ScratchCardViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScratchCardSerializer

    def get_queryset(self):
        return ScratchCard.objects.filter(user=self.request.user, raffle__status__in=[Raffle.Status.SELLING, Raffle.Status.CLOSED, Raffle.Status.DRAWN])

    @action(detail=True, methods=["post"])
    def reveal(self, request, pk=None):
        card = self.get_object()
        card = reveal_scratchcard(card)
        return Response(ScratchCardSerializer(card).data)

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        card = self.get_object()
        if card.status != ScratchCard.Status.WON or card.claimed_at:
            return Response({"detail": "Nada a resgatar."}, status=400)
        card.claimed_at = timezone.now()
        card.status = ScratchCard.Status.CLAIMED
        card.save(update_fields=["claimed_at", "status"])
        return Response(ScratchCardSerializer(card).data)


class AffiliateLinkViewSet(mixins.CreateModelMixin,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AffiliateLink.objects.filter(owner=self.request.user)

    serializer_class = AffiliateLinkSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CommissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommissionSerializer

    def get_queryset(self):
        return Commission.objects.filter(affiliate_link__owner=self.request.user).order_by("-created_at")


class WithdrawalViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WithdrawalSerializer

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        cfg = SiteConfig.objects.first()
        min_value = cfg.min_withdraw_amount if cfg else 0
        if serializer.validated_data["amount"] < min_value:
            raise serializers.ValidationError(f"Valor mínimo de saque é {min_value}.")
        serializer.save(user=self.request.user)


# Admin endpoints para aprovar comissões e saques
class AdminCommissionViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdmin]
    queryset = Commission.objects.all()
    serializer_class = CommissionSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        c = self.get_object()
        c.status = Commission.Status.APPROVED
        c.approved_by = request.user
        c.approved_at = timezone.now()
        c.save(update_fields=["status", "approved_by", "approved_at"])
        return Response(CommissionSerializer(c).data)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        c = self.get_object()
        c.status = Commission.Status.PAID
        c.paid_at = timezone.now()
        c.save(update_fields=["status", "paid_at"])
        return Response(CommissionSerializer(c).data)


class AdminWithdrawalViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdmin]
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalSerializer

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        w = self.get_object()
        w.status = WithdrawalRequest.Status.APPROVED
        w.processed_by = request.user
        w.processed_at = timezone.now()
        w.save(update_fields=["status", "processed_by", "processed_at"])
        return Response(WithdrawalSerializer(w).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        w = self.get_object()
        w.status = WithdrawalRequest.Status.REJECTED
        w.admin_note = request.data.get("note", "")
        w.processed_by = request.user
        w.processed_at = timezone.now()
        w.save(update_fields=["status", "admin_note", "processed_by", "processed_at"])
        return Response(WithdrawalSerializer(w).data)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        w = self.get_object()
        w.status = WithdrawalRequest.Status.PAID
        w.processed_by = request.user
        w.processed_at = timezone.now()
        w.save(update_fields=["status", "processed_by", "processed_at"])
        return Response(WithdrawalSerializer(w).data)
