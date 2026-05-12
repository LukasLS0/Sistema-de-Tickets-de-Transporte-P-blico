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


# unicipioSerializer — todos os campos (fields = '__all__').
# 9. EmpresaTransporteSerializer — inclua o campo calculado municipio_nome
# (source='municipio.nome', read_only=True).
# 10. UsuarioSerializer — todos os campos; defina saldo como read_only=True (alterações
# de saldo só ocorrem por validações ou cargas).
# 11. TipoTicketSerializer — inclua o campo nome_display (get_nome_display,
# read_only=True).
# 12. TicketSerializer — inclua os campos calculados usuario_nome
# (source='usuario.nome'), tipo_nome (source='tipo.nome_display'), status_display
# (get_status_display); valor_pago e data_validade devem ser read_only.
# 13. TransporteSerializer — inclua tipo_display (get_tipo_display) e empresa_nome
# (source='empresa.nome_fantasia'); ambos read_only.
# 14. ValidadorSerializer — inclua tipo_display e transporte_identificacao
# (source='transporte.identificacao', read_only=True, allow_null=True).
# 15. ValidacaoSerializer — este é o mais complexo. Implemente com: a) usuario_nome
# (source='ticket.usuario.nome', read_only=True); b) tipo_ticket
# (source='ticket.tipo.nome_display', read_only=True); c) transporte_nome
# (source='transporte.nome', read_only=True); d) SerializerMethodField mensagem que
# retorne 'Integração tarifária' quando dentro_janela_integracao=True ou 'Nova passagem'
# caso contrário; e) Sobrescreva create() para verificar a janela de integração: se já existir
# uma Validacao do mesmo ticket.usuario nas últimas N minutos (N =
# ticket.tipo.janela_integracao_minutos), defina dentro_janela_integracao=True e
# valor_debitado=0; caso contrário, debite o valor do tipo de ticket do saldo do usuário.
