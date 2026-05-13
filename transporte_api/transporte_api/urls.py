"""
URL configuration for transporte_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from bilhetagem import views
from drf_yasg.views import get_schema_view
from drf_yasg import openapi





router = routers.DefaultRouter()
router.register(r'municipios', views.MunicipioViewSet, basename='municipio')
router.register(r'empresas', views.EmpresaTransporteViewSet, basename='empresa')
router.register(r'usuarios', views.UsuarioViewSet, basename='usuario')
router.register(r'tipos-ticket', views.TipoTicketViewSet, basename='tipo-ticket')
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'transportes', views.TransporteViewSet, basename='transporte')
router.register(r'validadores', views.ValidadorViewSet, basename='validador')
router.register(r'validacoes', views.ValidacaoViewSet, basename='validacao')

#25. Configure o Swagger (drf-yasg) para exibir a documentação em /swagger/ e o ReDoc
#em /redoc

schema_view = get_schema_view(
    openapi.Info(
        title='Sistema Ticket API',
        default_version='v1',
        description='Documentação da API do sistema de tickets',
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
