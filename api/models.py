from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
import uuid
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    data_cadastro = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cep = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "cpf"]

    def __str__(self):
        return f"{self.username} - {self.email}"

class SiteConfig(models.Model):
    """Config global gerenciada pelo admin (um único registro)."""
    comissão_padrão_porcentagem = models.DecimalField(max_digits=5, decimal_places=2, default=5)  # 5%
    valor_min_de_saque = models.DecimalField(max_digits=12, decimal_places=2, default=50)
    # probabilidades e prêmios das raspadinhas (exemplo)
    #[{"prob": 0.80, "amount": "0.00"}, {"prob": 0.15, "amount": "5.00"}, {"prob": 0.05, "amount": "20.00"}]
    tabela_raspadinha = models.JSONField(default=list, blank=True)

    def __str__(self):
        return "Config do Site"

    class Meta:
        verbose_name = "Config do Site"
        verbose_name_plural = "Config do Site"

class Sorteio(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SELLING = "selling", "Vendendo"
        CLOSED = "closed", "Encerrada (aguardando sorteio)"
        DRAWN = "drawn", "Sorteada"

    titulo = models.CharField(max_length=140)
    descricao = models.TextField(blank=True)
    numeros_totais = models.PositiveIntegerField()
    preco_por_numero = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    comeca_as = models.DateTimeField(null=True, blank=True)
    termina_em = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to="sorteios/", null=True, blank=True)
    regras = models.TextField(blank=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="raffles_created")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = "Sorteio"
        verbose_name_plural = "Sorteios"

class Comprar(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        CANCELED = "canceled", "Cancelado"

    chave_idempotencia = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="compras")
    sorteio = models.ForeignKey(Sorteio, on_delete=models.CASCADE, related_name="compras")
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    total_preco = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    provedor_de_pagamento = models.CharField(max_length=30, blank=True)   
    pagamento_ref = models.CharField(max_length=140, blank=True)       
    criado_em = models.DateTimeField(auto_now_add=True)
    pago_em = models.DateTimeField(null=True, blank=True)
    números_escolhidos = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Comprar {self.pk} - {self.user} - {self.sorteio}"

    class Meta:
        verbose_name = "Comprar"
        verbose_name_plural = "Comprar"

class SorteioNumero(models.Model):
    
    """Número individual do sorteio (estoque)."""
    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponível"
        RESERVED = "reserved", "Reservado"
        SOLD = "sold", "Vendido"
        WINNER = "winner", "Vencedor"

    sorteio = models.ForeignKey(Sorteio, on_delete=models.CASCADE, related_name="numeros")
    numero = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AVAILABLE)
    # quem ficou com ele quando vendido
    proprietario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="numeros_do_sorteio")
    # controle de reserva para evitar over-selling
    reservado_até = models.DateTimeField(null=True, blank=True)
    comprar = models.ForeignKey(Comprar, null=True, blank=True, on_delete=models.SET_NULL, related_name="numeros")

    class Meta:
        unique_together = ("sorteiro", "numero")
        indexes = [
            models.Index(fields=["sorteio", "status"]),
            models.Index(fields=["sorteio", "numero"]),
        ]

    def __str__(self):
        return f"{self.sorteio.titulo} - #{self.numero} ({self.status})"

    class Meta:
        verbose_name = "Número de rifa"
        verbose_name_plural = "Números de rifas"

class Raspadinha(models.Model):
    """Raspadinha bônus vinculada a uma compra. Resultado revelado quando 'scratch'."""
    class Status(models.TextChoices):
        UNUSED = "unused", "Não revelada"
        WON = "won", "Premiada"
        LOST = "lost", "Sem prêmio"
        CLAIMED = "claimed", "Prêmio resgatado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="raspadinhas")
    sorteio = models.ForeignKey(Sorteio, on_delete=models.CASCADE, related_name="raspadinhas")
    comprar = models.ForeignKey(Comprar, on_delete=models.CASCADE, related_name="raspadinhas")
    codigo = models.CharField(max_length=50, default="", blank=True)  
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNUSED)
    valor_premio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revrevelado_emealed_at = models.DateTimeField(null=True, blank=True)
    reivindicado_em = models.DateTimeField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Raspadinha"
        verbose_name_plural = "Raspadinhas"

