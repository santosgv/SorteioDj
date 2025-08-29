import uuid
from .models import ScratchCard, Purchase,RaffleNumber
import random

def allocate_numbers_for_purchase(purchase):
    # Filtra números disponíveis para o sorteio específico
    available_numbers = list(
        RaffleNumber.objects.filter(
            raffle=purchase.raffle, 
            status=RaffleNumber.Status.AVAILABLE
        ).values_list("number", flat=True)
    )

    if len(available_numbers) < purchase.quantity:
        raise ValueError("Não há números suficientes disponíveis")

    chosen_numbers = random.sample(available_numbers, purchase.quantity)

    # Atualiza os números escolhidos para vendidos
    RaffleNumber.objects.filter(
        raffle=purchase.raffle,
        number__in=chosen_numbers
    ).update(
        status=RaffleNumber.Status.SOLD,
        owner=purchase.user,
        purchase=purchase,
        reserved_until=None  # Remove a reserva se houver
    )
    
    # Atualiza a compra com os números escolhidos
    purchase.chosen_numbers = chosen_numbers
    purchase.save(update_fields=["chosen_numbers"])

    return chosen_numbers

def create_scratchcards_for_purchase(purchase: Purchase):
    """
    Cria raspadinhas de acordo com a quantidade comprada.
    """
    scratchcards = []
    for _ in range(purchase.quantity):
        code = str(uuid.uuid4())[:8].upper()  # código único
        scratchcards.append(ScratchCard(purchase=purchase, code=code))
    ScratchCard.objects.bulk_create(scratchcards)
    return scratchcards