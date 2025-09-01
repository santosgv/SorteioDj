from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comprar, SorteioNumero,Sorteio, Raspadinha,SiteConfig
from django.db import transaction
from django.utils.crypto import get_random_string
import random


@receiver(post_save, sender=Sorteio)
def criar_numeros_automaticamente(sender, instance, created, **kwargs):
    if created:
        # Exemplo: cria números de 1 até quantidade_numeros
        quantidade = instance.numeros_totais  
        numeros = [
            SorteioNumero(sorteio=instance, numero=i)
            for i in range(1, quantidade + 1)
        ]
        SorteioNumero.objects.bulk_create(numeros)

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

    if created:
        quantidade = instance.quantidade
        sorteio = instance.sorteio
        user = instance.user

        with transaction.atomic():
            numeros_disponiveis = (
            SorteioNumero.objects
            .select_for_update(skip_locked=True)
            .filter(sorteio=sorteio, status=SorteioNumero.Status.AVAILABLE)
            .order_by("numero")[:quantidade]
        )



        if numeros_disponiveis.count() < quantidade:
            raise ValueError("Não há números suficientes disponíveis para esta compra.")

        for numero in numeros_disponiveis:
            numero.status = SorteioNumero.Status.SOLD
            numero.proprietario = user
            numero.comprar = instance
            #numero.save()

        # Configuração de raspadinha
        config = SiteConfig.objects.first()
        tabela = config.tabela_raspadinha if config and config.tabela_raspadinha else []

        for i in range(quantidade):
            premio = sortear_premio(tabela)
            print(f"Prêmio sorteado: {premio}")
            #Raspadinha.objects.create(
            #    comprar=instance,
            #    sorteio=sorteio,
            #    user=user,
            #    valor_premio=premio,
            #    codigo=get_random_string(12).upper(),
            #)