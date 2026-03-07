from django.http import JsonResponse
from .models import Departamento, Municipio


def departamentos_list(request):
    """Retorna todos los departamentos ordenados alfabeticamente."""
    datos = Departamento.objects.all().values('id_departamento', 'departamento')
    return JsonResponse(list(datos), safe=False)


def municipios_by_departamento(request, id_departamento):
    """Retorna los municipios activos de un departamento."""
    datos = (
        Municipio.objects
        .filter(departamento_id=id_departamento, estado=True)
        .values('id_municipio', 'municipio')
        .order_by('municipio')
    )
    return JsonResponse(list(datos), safe=False)
