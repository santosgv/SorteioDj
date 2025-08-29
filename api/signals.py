from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Purchase
from django.utils import timezone
from .utils import allocate_numbers_for_purchase, create_scratchcards_for_purchase

@receiver(post_save, sender=Purchase)
def on_purchase_paid(sender, instance: Purchase, created, **kwargs):
    # evita rodar no momento da criação
    if created:
        return
    
    # só executa quando o status muda para pago
    if instance.status == Purchase.Status.PAID and instance.paid_at is None:
        instance.paid_at = timezone.now()
        instance.save(update_fields=["paid_at"])

        # Alocar números automaticamente
        allocate_numbers_for_purchase(instance)

        # Criar raspadinhas
        create_scratchcards_for_purchase(instance)