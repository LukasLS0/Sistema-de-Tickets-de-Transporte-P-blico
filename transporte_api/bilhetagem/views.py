from django.shortcuts import render
from models import *
from serializers import *
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

#Crie os ViewSets no arquivo bilhetagem/views.py e registre as rotas em transporte_api/urls.py:
#16. MunicipioViewSet — ModelViewSet; busca por nome (SearchFilter).

class MunicipioViewSet(viewsets.ModelViewSet):
    queryset = Municipio.objects.all()
    serializer_class = MunicipioSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome']

#17. EmpresaTransporteViewSet — ModelViewSet com filtros por municipio
#(filterset_fields) e busca por razao_social, nome_fantasia e cnpj.

class EmpresaTransporteViewSet(viewsets.ModelViewSet):
    queryset = EmpresaTransporte.objects.all()
    serializer_class = EmpresaTransporteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj']
    filterset_fields = ['municipio']


#18. UsuarioViewSet — ModelViewSet com busca por nome, email e cpf; ordenação por
#data_cadastro.

#GET /transporte_api/usuarios/1/extrato/HTTP 200 OK{ "usuario": "Maria da Silva", "cpf":
#"123.456.789-00", "saldo_atual": 42.50, "tickets_comprados": 8, "tickets_ativos": 1,
#"tickets_expirados": 6, "validacoes_realizadas": 47, "validacoes_30d": 12,
#"valor_total_gasto": 285.00, "valor_economizado_integracao": 38.00}


# Endpoint: Recarga de Saldo
#Implemente via @action no UsuarioViewSet:
#POST /transporte_api/usuarios/{id}/recarregar/
#Corpo da requisição (JSON):
#{ "valor": 50.00}
#• Validar valor > 0 — caso contrário, HTTP 400.
#• Incrementar o saldo do usuário.
#• Retornar o saldo atualizado.


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('data_cadastro')
    serializer_class = UsuarioSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome', 'email', 'cpf']

    @action(detail=True, methods=['get'])
    def extrato(self, request, pk=None):
        usuario = self.get_object()
        extrato_data = {
            "usuario": usuario.nome,
            "cpf": usuario.cpf,
            "saldo_atual": usuario.saldo,
            "tickets_comprados": usuario.tickets.count(),
            "tickets_ativos": usuario.tickets.filter(status='ativo').count(),
            "tickets_expirados": usuario.tickets.filter(status='expirado').count(),
            "validacoes_realizadas": Validacao.objects.filter(ticket__usuario=usuario).count(),
            "validacoes_30d": Validacao.objects.filter(ticket__usuario=usuario, data_hora__gte=timezone.now()-timedelta(days=30)).count(),
            "valor_total_gasto": sum(t.valor_pago for t in usuario.tickets.all()),
            "valor_economizado_integracao": sum(t.valor_pago for t in usuario.tickets.filter(status='integracao')),
        }
        return Response(extrato_data)

    @action(detail=True, methods=['post'])
    def recarregar(self, request, pk=None):
        usuario = self.get_object()
        valor = request.data.get('valor')

        if valor is None or float(valor) <= 0:
            return Response({'mensagem': 'Valor deve ser maior que zero.'}, status=400)

        usuario.saldo += float(valor)
        usuario.save()

        return Response({'saldo_atual': usuario.saldo})

#19. TipoTicketViewSet — ModelViewSet com filtros por nome e ativo.

class TipoTicketViewSet(viewsets.ModelViewSet):
    queryset = TipoTicket.objects.all()
    serializer_class = TipoTicketSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nome']
    filterset_fields = ['ativo']

#20. TicketViewSet — ModelViewSet com filtros por usuario, tipo e status; ordenação por
#data_compra. Otimize com select_related('usuario', 'tipo').

#5.1 — Endpoint: Validar Ticket
#Implemente via @action no TicketViewSet:
#POST /transporte_api/tickets/{id}/validar/
#Corpo da requisição (JSON):
#{ "validador_id": 3, "transporte_id": 12}
#Comportamento esperado:
#• Se o ticket não estiver com status='ativo' → HTTP 400 com mensagem 'Ticket inválido ou
#expirado'.
#• Se houver validação do mesmo usuário nos últimos N minutos (janela do tipo) → registrar
#com dentro_janela_integracao=True, valor_debitado=0.
#• Caso contrário → debitar o valor do tipo de ticket do saldo do usuário, criar a Validacao.
#• Para tickets do tipo 'avulso' fora da janela de integração → após a validação, alterar
#status do ticket para 'consumido'.
#• Retornar a Validacao criada (HTTP 201) com o campo mensagem do serializer


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('usuario', 'tipo').all().order_by('data_compra')
    serializer_class = TicketSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['usuario__nome', 'tipo__nome']
    filterset_fields = ['usuario', 'tipo', 'status']

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        ticket = self.get_object()
        validador_id = request.data.get('validador_id')
        transporte_id = request.data.get('transporte_id')

        if ticket.status != 'ativo':
            return Response({'mensagem': 'Ticket inválido ou expirado.'}, status=400)

        # Lógica de validação será implementada no ValidacaoViewSet
        validacao_data = {
            'ticket': ticket.id,
            'validador': validador_id,
            'transporte': transporte_id
        }
        validacao_serializer = ValidacaoSerializer(data=validacao_data)
        validacao_serializer.is_valid(raise_exception=True)
        validacao = validacao_serializer.save()

        return Response(ValidacaoSerializer(validacao).data, status=201)


#21. TransporteViewSet — ModelViewSet com filtros por tipo, empresa e ativo; busca por
#identificacao e nome.

#5.2 — Endpoint: Relatório por Transporte
#Implemente via @action no TransporteViewSet:
#GET /transporte_api/transportes/{id}/relatorio/?inicio=2026-05-01&fim=2026-05-31
#A resposta deve incluir:
#• Dados do transporte (identificação, tipo, nome, empresa).
#• Período consultado.
#• Total de validações no período.
#• Total de usuários únicos atendidos.
#• Distribuição por tipo de ticket (avulso, diário, semanal, mensal, anual).
#• Receita atribuída ao transporte (soma de valor_debitado das validações iniciadas naquele transporte)


#5.3 — Endpoint: Painel da Empresa
#Implemente via @action no EmpresaTransporteViewSet:
#GET /transporte_api/empresas/{id}/painel/
#Retorna o painel operacional da empresa, com:
#• Total de transportes ativos por tipo (parada, ônibus, trem).
#• Total de validadores ativos por tipo (cartão, celular).
#• Top 5 transportes com mais validações nos últimos 30 dias (lista ordenada decrescente).
#• Total de validações nos últimos 30 dias agregado por dia (para construir um gráfico).

class TransporteViewSet(viewsets.ModelViewSet):
    queryset = Transporte.objects.all()
    serializer_class = TransporteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['identificacao', 'empresa__nome_fantasia']
    filterset_fields = ['tipo', 'empresa', 'ativo']

    @action(detail=True, methods=['get'])
    def relatorio(self, request, pk=None):
        transporte = self.get_object()
        inicio = request.query_params.get('inicio')
        fim = request.query_params.get('fim')
        
        validacoes = Validacao.objects.filter(transporte=transporte, data_hora__range=[inicio, fim])
        total_validacoes = validacoes.count()
        usuarios_unicos = validacoes.values('ticket__usuario').distinct().count()
        distribuicao_tipo = validacoes.values('ticket__tipo__nome').annotate(count=Count('id'))
        receita = validacoes.aggregate(total_receita=Sum('valor_debitado'))['total_receita'] or 0

        relatorio_data = {
            'transporte': TransporteSerializer(transporte).data,
            'periodo': {'inicio': inicio, 'fim': fim},
            'total_validacoes': total_validacoes,
            'usuarios_unicos': usuarios_unicos,
            'distribuicao_tipo': list(distribuicao_tipo),
            'receita': receita
        }
        return Response(relatorio_data)
    
    @action(detail=True, methods=['get'])
    def painel(self, request, pk=None):
        empresa = self.get_object()
        transportes_ativos = Transporte.objects.filter(empresa=empresa, ativo=True).values('tipo').annotate(count=Count('id'))
        validadores_ativos = Validador.objects.filter(transporte__empresa=empresa, ativo=True).values('tipo').annotate(count=Count('id'))
        top_transportes = Validacao.objects.filter(transporte__empresa=empresa, data_hora__gte=timezone.now()-timedelta(days=30)).values('transporte__nome').annotate(count=Count('id')).order_by('-count')[:5]
        validacoes_diarias = Validacao.objects.filter(transporte__empresa=empresa, data_hora__gte=timezone.now()-timedelta(days=30)).extra({'dia': "date(data_hora)"}).values('dia').annotate(count=Count('id')).order_by('dia')

        painel_data = {
            'transportes_ativos': list(transportes_ativos),
            'validadores_ativos': list(validadores_ativos),
            'top_transportes': list(top_transportes),
            'validacoes_diarias': list(validacoes_diarias)
        }
        return Response(painel_data)



#22. ValidadorViewSet — ModelViewSet com filtros por tipo, transporte e ativo.

class ValidadorViewSet(viewsets.ModelViewSet):
    queryset = Validador.objects.all()
    serializer_class = ValidadorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['transporte__identificacao']
    filterset_fields = ['transporte', 'ativo']

#23. ValidacaoViewSet — ModelViewSet com filtros por ticket, validador, transporte e
#dentro_janela_integracao; ordenação por data_hora. Otimize com
#select_related('ticket__usuario', 'ticket__tipo', 'validador', 'transporte').
#

class ValidacaoViewSet(viewsets.ModelViewSet):
    queryset = Validacao.objects.select_related('ticket__usuario', 'ticket__tipo', 'validador', 'transporte').all().order_by('data_hora')
    serializer_class = ValidacaoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['ticket__usuario__nome', 'ticket__tipo__nome', 'validador__transporte__identificacao']
    filterset_fields = ['ticket', 'validador', 'transporte', 'dentro_janela_integracao']




