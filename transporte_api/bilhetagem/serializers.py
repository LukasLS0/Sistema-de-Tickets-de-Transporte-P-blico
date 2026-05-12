from models import *
from rest_framework import serializers


# Regras de Negócio das Validações
# • Uma validação dentro da janela de integração (60 min por padrão) NÃO debita valor —
# apenas registra o uso (dentro_janela_integracao=True, valor_debitado=0).
# • Fora da janela de integração, deve-se debitar o saldo do usuário e marcar a validação
# como nova passagem.
# • Um ticket com status diferente de 'ativo' não pode ser validado — a API deve retornar
# HTTP 400.
# • Tickets do tipo 'avulso' permitem apenas uma janela de integração e depois passam ao
# status 'consumido'.
# • Tickets do tipo 'mensal' ou 'anual' permitem validações ilimitadas durante a validade.

#5. Sobrescreva o método save() do modelo Ticket para calcular automaticamente data_validade = data_compra + timedelta(days=tipo.duracao_dias) na criação.
