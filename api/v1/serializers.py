from rest_framework import serializers
from api.models import (
    User, SiteConfig, Sorteio, SorteioNumero,
    Comprar, Raspadinha
)


# --------------------------
# User Serializer
# --------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "cpf", "data_nascimento",
            "telefone", "cep", "endereco", "cidade", "uf",
            "data_cadastro"
        ]
        read_only_fields = ["id", "data_cadastro"]


# --------------------------
# Configuração do Site
# --------------------------
class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = "__all__"


# --------------------------
# Sorteio + Números
# --------------------------
class SorteioNumeroSerializer(serializers.ModelSerializer):
    proprietario = UserSerializer(read_only=True)

    class Meta:
        model = SorteioNumero
        fields = [
            "id", "sorteio", "numero", "status",
            "proprietario", "reservado_até", "comprar"
        ]
        read_only_fields = ["id", "status", "proprietario"]


class SorteioSerializer(serializers.ModelSerializer):
    criado_por = UserSerializer(read_only=True)
    numeros = SorteioNumeroSerializer(many=True, read_only=True)

    class Meta:
        model = Sorteio
        fields = [
            "id", "titulo", "descricao", "numeros_totais",
            "preco_por_numero", "status", "comeca_as", "termina_em",
            "image", "regras", "criado_por", "criado_em", "numeros"
        ]
        read_only_fields = ["id", "criado_em", "status", "criado_por"]


# --------------------------
# Compra (Comprar)
# --------------------------
class ComprarSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    sorteio = SorteioSerializer(read_only=True)

    class Meta:
        model = Comprar
        fields = [
            "id", "chave_idempotencia", "user", "sorteio",
            "quantidade", "preco_unitario", "total_preco",
            "status", "provedor_de_pagamento", "pagamento_ref",
            "criado_em", "pago_em", "números_escolhidos"
        ]
        read_only_fields = ["id", "chave_idempotencia", "criado_em", "pago_em"]


# --------------------------
# Raspadinha
# --------------------------
class RaspadinhaSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    sorteio = SorteioSerializer(read_only=True)
    comprar = ComprarSerializer(read_only=True)

    class Meta:
        model = Raspadinha
        fields = [
            "id", "user", "sorteio", "comprar",
            "codigo", "status", "valor_premio",
            "revrevelado_emealed_at", "reivindicado_em", "criado_em"
        ]
        read_only_fields = ["id", "criado_em", "valor_premio"]
