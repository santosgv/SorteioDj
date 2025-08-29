from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comprar, SorteioNumero, Raspadinha,SiteConfig
from django.utils.crypto import get_random_string
import random

def sortear_premio(tabela):
    if not tabela or not isinstance(tabela, list):
        return 0

    # Filtra apenas os itens válidos
    premios = []
    chances = []
    for item in tabela:
        try:
            premios.append(item["premio"])
            chances.append(item["chance"])
        except KeyError:
            continue  # ignora se não tiver a chave correta

    # Se não tiver valores válidos, retorna 0
    if not premios or not chances:
        return 0

    # Sorteio ponderado
    return random.choices(premios, weights=chances, k=1)[0]


@receiver(post_save, sender=Comprar)
def criar_numeros_e_raspadinhas(sender, instance: Comprar, created, **kwargs):
    """
    Quando um usuário realiza uma compra, criamos automaticamente:
    - x números para o sorteio
    - x raspadinhas para o usuário
    """
    if created:
        quantidade = instance.quantidade
        sorteio = instance.sorteio
        user = instance.user

        # Criar números do sorteio
        for i in range(quantidade):
            numero = SorteioNumero.objects.create(
                sorteio=sorteio,
                proprietario=user,
                numero=SorteioNumero.objects.filter(sorteio=sorteio).count() + 1,
                comprar=instance
            )

            # Configuração global de raspadinhas
            config = SiteConfig.objects.first()
            tabela = config.tabela_raspadinha if config and config.tabela_raspadinha else []

            premio = sortear_premio(tabela)

            # Criar raspadinha vinculada
            Raspadinha.objects.create(
                comprar=instance,
                sorteio=sorteio,
                user=user,
                valor_premio=premio,
                codigo=get_random_string(12).upper(),  
            )
