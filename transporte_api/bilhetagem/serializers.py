from models import *
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta



class MunicipioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = '__all__'

class EmpresaTransporteSerializer(serializers.ModelSerializer):
    municipio_nome = serializers.CharField(source='municipio.nome', read_only=True)

    class Meta:
        model = EmpresaTransporte
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'
        read_only_fields = ['saldo']

class TipoTicketSerializer(serializers.ModelSerializer):
    nome_display = serializers.CharField(source='get_nome_display', read_only=True)

    class Meta:
        model = TipoTicket
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    tipo_nome = serializers.CharField(source='tipo.nome_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['valor_pago', 'data_validade']

    def save(self, **kwargs):
        if not self.instance:  # Apenas na criação
            tipo_ticket = self.validated_data['tipo']
            self.validated_data['data_validade'] = timezone.now() + timedelta(days=tipo_ticket.duracao_dias)
            self.validated_data['valor_pago'] = tipo_ticket.valor
        return super().save(**kwargs)

class TransporteSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    empresa_nome = serializers.CharField(source='empresa.nome_fantasia', read_only=True)

    class Meta:
        model = Transporte
        fields = '__all__'

class ValidadorSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='transporte.get_tipo_display', read_only=True)
    transporte_identificacao = serializers.CharField(source='transporte.identificacao', read_only=True, allow_null=True)

    class Meta:
        model = Validador
        fields = '__all__'

class ValidacaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='ticket.usuario.nome', read_only=True)
    tipo_ticket = serializers.CharField(source='ticket.tipo.nome_display', read_only=True)
    transporte_nome = serializers.CharField(source='transporte.nome', read_only=True)
    mensagem = serializers.SerializerMethodField()

    class Meta:
        model = Validacao
        fields = '__all__'
    
    def get_mensagem(self, obj):
        if hasattr(obj, 'dentro_janela_integracao') and obj.dentro_janela_integracao:
            return 'Integração tarifária'
        return 'Nova passagem'
    
    def create(self, validated_data):
        # Lógica para verificar janela de integração e debitar valor
        ticket = validated_data['ticket']
        usuario = ticket.usuario
        tipo_ticket = ticket.tipo

        # Verificar se o ticket está ativo
        if ticket.status != 'ativo':
            raise serializers.ValidationError('Ticket não está ativo.')

        # Verificar validações anteriores do mesmo usuário dentro da janela de integração
        janela_integracao = tipo_ticket.duracao_dias * 24 * 60  # Convertendo dias para minutos
        tempo_limite = timezone.now() - timedelta(minutes=janela_integracao)

        validacoes_recentes = Validacao.objects.filter(
            ticket__usuario=usuario,
            data_hora__gte=tempo_limite
        )

        dentro_janela_integracao = validacoes_recentes.exists()

        if dentro_janela_integracao:
            valor_debitado = 0
        else:
            valor_debitado = tipo_ticket.valor
            if usuario.saldo < valor_debitado:
                raise serializers.ValidationError('Saldo insuficiente.')
            usuario.saldo -= valor_debitado
            usuario.save()

            # Atualizar status do ticket avulso para consumido após uso
            if tipo_ticket.nome == 'avulso':
                ticket.status = 'consumido'
                ticket.save()

        validacao = Validacao.objects.create(
            **validated_data,
            dentro_janela_integracao=dentro_janela_integracao,
            valor_debitado=valor_debitado
        )
        return validacao







