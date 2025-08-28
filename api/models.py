from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL


class SiteConfig(models.Model):
    """Config global gerenciada pelo admin (um único registro)."""
    commission_default_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)  # 5%
    min_withdraw_amount = models.DecimalField(max_digits=12, decimal_places=2, default=50)
    # probabilidades e prêmios das raspadinhas (exemplo)
    # [{"prob": 0.80, "amount": "0.00"}, {"prob": 0.15, "amount": "5.00"}, {"prob": 0.05, "amount": "20.00"}]
    scratchcard_table = models.JSONField(default=list, blank=True)

    def __str__(self):
        return "Config do Site"

    class Meta:
        verbose_name = "Config do Site"
        verbose_name_plural = "Config do Site"


class Raffle(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SELLING = "selling", "Vendendo"
        CLOSED = "closed", "Encerrada (aguardando sorteio)"
        DRAWN = "drawn", "Sorteada"

    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    total_numbers = models.PositiveIntegerField()
    price_per_number = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to="raffles/", null=True, blank=True)
    rules = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="raffles_created")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Sorteio"
        verbose_name_plural = "Sorteios"


class RaffleNumber(models.Model):
    """Número individual do sorteio (estoque)."""
    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponível"
        RESERVED = "reserved", "Reservado"
        SOLD = "sold", "Vendido"
        WINNER = "winner", "Vencedor"

    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="numbers")
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    # quem ficou com ele quando vendido
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="raffle_numbers")
    # controle de reserva para evitar over-selling
    reserved_until = models.DateTimeField(null=True, blank=True)
    purchase = models.ForeignKey("Purchase", null=True, blank=True, on_delete=models.SET_NULL, related_name="numbers")

    class Meta:
        unique_together = ("raffle", "number")
        indexes = [
            models.Index(fields=["raffle", "status"]),
            models.Index(fields=["raffle", "number"]),
        ]

    def __str__(self):
        return f"{self.raffle_id} - #{self.number} ({self.status})"

    class Meta:
        verbose_name = "Número de rifa"
        verbose_name_plural = "Números de rifas"


class Purchase(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        CANCELED = "canceled", "Cancelado"

    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="purchases")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    payment_provider = models.CharField(max_length=30, blank=True)   # ex: "pix", "stripe"
    payment_ref = models.CharField(max_length=140, blank=True)       # txid/charge_id
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Purchase {self.pk} - {self.user} - {self.raffle}"

    class Meta:
        verbose_name = "Comprar"
        verbose_name_plural = "Comprar"


class ScratchCard(models.Model):
    """Raspadinha bônus vinculada a uma compra. Resultado revelado quando 'scratch'."""
    class Status(models.TextChoices):
        UNUSED = "unused", "Não revelada"
        WON = "won", "Premiada"
        LOST = "lost", "Sem prêmio"
        CLAIMED = "claimed", "Prêmio resgatado"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scratchcards")
    raffle = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="scratchcards")
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="scratchcards")
    code = models.CharField(max_length=50, default="", blank=True)  # opcional
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNUSED)
    prize_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revealed_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Raspadinha"
        verbose_name_plural = "Raspadinhas"


class AffiliateLink(models.Model):
    """Link de afiliado."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="affiliate_links")
    code = models.SlugField(unique=True)  # ex: 'vitor10'
    percentage_override = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # se None, usa SiteConfig
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def current_percent(self):
        cfg = SiteConfig.objects.first()
        base = cfg.commission_default_percent if cfg else 0
        return self.percentage_override if self.percentage_override is not None else base

    def __str__(self):
        return f"{self.code} ({self.owner})"

    class Meta:
        verbose_name = "Link de Afiliado"
        verbose_name_plural = "Links de Afiliados"


class Referral(models.Model):
    """Quem entrou via link de afiliado."""
    affiliate_link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name="referrals")
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral")  # 1 usuário -> 1 origem
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Indicação"
        verbose_name_plural = "Indicações"


class Commission(models.Model):
    """Comissão por compra do indicado."""
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovada"
        PAID = "paid", "Paga"
        REJECTED = "rejected", "Recusada"

    affiliate_link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name="commissions")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="generated_commissions")
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="commissions")
    base_amount = models.DecimalField(max_digits=12, decimal_places=2)    # total da compra
    percentage = models.DecimalField(max_digits=5, decimal_places=2)      # % no momento
    amount = models.DecimalField(max_digits=12, decimal_places=2)         # base * %
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_commissions")
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comissão"
        verbose_name_plural = "Comissões"


class WithdrawalRequest(models.Model):
    """Pedido de saque do afiliado."""
    class Status(models.TextChoices):
        REQUESTED = "requested", "Solicitado"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Recusado"
        PAID = "paid", "Pago"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    admin_note = models.TextField(blank=True)
    pix_key = models.CharField(max_length=120, blank=True)  # opcional
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="processed_withdrawals")

    class Meta:
        verbose_name = "Pedido de Saque"
        verbose_name_plural = "Pedidos de Saque"
