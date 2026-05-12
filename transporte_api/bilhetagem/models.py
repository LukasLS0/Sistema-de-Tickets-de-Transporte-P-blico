from email.policy import default

from django.db import models

# Create your models here.

class Municipio(models.Model):
    nome = models.CharField(max_length=120)
    uf = models.CharField(max_length=2) #SP, RJ
    endereco_sede =  models.CharField(max_length=200, blank=True) # endereco da prefeitura
    ativo = models.BooleanField(default=True)

class EmpresaTransporte(models.Model):
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=150, blank=True)
    cnpj = models.CharField(max_length=18, unique=True) # como colocar o formato: 00.000.000/0000-00
    endereco = models.CharField(max_length=200, blank=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT, related_name='empresas')

class Usuario(models.Model):
    nome = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, unique=True) # formato: 000.000.000-00
    endereco = models.CharField(max_length=200, blank=True)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)

class TipoTicket(models.Model):
    CHOICES_TICKETS = (
        ('avulso', 'Avulso'),
        ('diario', 'Diário'),
        ('semanal', 'Semanal'),
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
    )
    nome = models.CharField(choices=CHOICES_TICKETS)
    descricao = models.TextField(blank=True)
    valor = models.DecimalField(max_digits=8, decimal_places=2) # preco do ticket
    duracao_dias = models.PositiveSmallIntegerField(default=60)  # Janela de intregração tarifária minutos
    ativo = models.BooleanField(default=True)

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('consumido', 'Consumido'),
        ('cancelado', 'Cancelado'),
        ('ativo', 'Ativo'),
        ('expirado', 'Expirado'),
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='tickets')
    tipo = models.ForeignKey(TipoTicket, on_delete=models.PROTECT, related_name='tickets')
    data_compra = models.DateTimeField(auto_now_add=True)
    valor_pago = models.DecimalField(max_digits=8, decimal_places=2)
    data_validade = models.DateTimeField() # calculada a partidar de data de compra + duracao dias. como fazer isso?
    status = models.CharField(choices=STATUS_CHOICES)

class Transporte(models.Model):
    TIPO_CHOICES = (
        ('onibus', 'Ônibus'),
        ('parada', 'Parada'),
        ('trem', 'Trem'),
    )
    identificacao = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(choices=TIPO_CHOICES)
    nome = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    empresa = models.ForeignKey(EmpresaTransporte, on_delete=models.PROTECT, related_name='transportes')
    ativo = models.BooleanField(default=True)

class Validador(models.Model):
    TIPO_CHOICES = (
        ('cartao', 'Cartão'),
        ('celular', 'Celular')
    )
    codigo = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(choices=TIPO_CHOICES)
    transporte = models.ForeignKey(Transporte, on_delete=models.PROTECT, related_name='validadores', null=True, blank=True)  # nulo quando for celular do usuario
    data_instalacao = models.DateField()
    ativo = models.BooleanField(default=True)

class Validacao(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name='validacoes')
    validador = models.ForeignKey(Validador, on_delete=models.PROTECT, related_name='validacoes')
    Transporte = models.ForeignKey(Transporte, on_delete=models.PROTECT, related_name='validacoes')
    data_hora = models.DateTimeField(auto_now_add=True)
    dentro_janela_integracao = models.BooleanField(default=False) # true se ocorrer dentro da janela de 1h de validação anterior do mesmo usuário
    valor_debitado = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    