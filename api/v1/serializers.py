from rest_framework import serializers
from api.models import *

class RaffleNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaffleNumber
        fields = ["id", "number", "status"]

class RaffleSerializer(serializers.ModelSerializer):
    available = serializers.SerializerMethodField()

    class Meta:
        model = Raffle
        fields = ["id", "title", "description", "total_numbers", "price_per_number",
                  "status", "starts_at", "ends_at", "available"]

    def get_available(self, obj):
        return obj.numbers.filter(status=RaffleNumber.Status.AVAILABLE).count()

class PurchaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ["idempotency_key", "raffle", "quantity", "chosen_numbers", "payment_provider"]
        extra_kwargs = {
            "idempotency_key": {"required": False},
            "chosen_numbers": {"required": False},
        }

    def validate(self, data):
        raffle = data["raffle"]
        if raffle.status != Raffle.Status.SELLING:
            raise serializers.ValidationError("Sorteio não está em venda.")
        chosen = data.get("chosen_numbers") or []
        qty = data["quantity"]
        if chosen and len(chosen) != qty:
            raise serializers.ValidationError("Quantidade ≠ quantidade de números escolhidos.")
        return data

    def create(self, validated):
        user = self.context["request"].user
        raffle = validated["raffle"]
        qty = validated["quantity"]
        chosen = validated.get("chosen_numbers") or []
        unit = raffle.price_per_number
        total = unit * qty
        return Purchase.objects.create(
            user=user,
            raffle=raffle,
            quantity=qty,
            chosen_numbers=chosen,
            unit_price=unit,
            total_price=total,
            payment_provider=validated.get("payment_provider") or "",
        )

class PurchaseSerializer(serializers.ModelSerializer):
    numbers = RaffleNumberSerializer(many=True, read_only=True)

    class Meta:
        model = Purchase
        fields = ["id", "idempotency_key", "status", "payment_ref", "total_price",
                  "unit_price", "quantity", "raffle", "numbers", "paid_at", "created_at"]

class ScratchCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScratchCard
        fields = ["id", "status", "prize_amount", "revealed_at", "claimed_at"]

class AffiliateLinkSerializer(serializers.ModelSerializer):
    current_percent = serializers.SerializerMethodField()

    class Meta:
        model = AffiliateLink
        fields = ["id", "code", "active", "percentage_override", "current_percent"]

    def get_current_percent(self, obj):
        return obj.current_percent()

class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = ["id", "purchase", "amount", "percentage", "status", "created_at"]

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WithdrawalRequest
        fields = ["id", "amount", "status", "pix_key", "created_at", "processed_at", "admin_note"]
        read_only_fields = ["status", "processed_at", "admin_note"]
