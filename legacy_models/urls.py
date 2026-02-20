from django.urls import path

from .views import menu_evaluaciones, visita_asignatura

app_name = "legacy_models"

urlpatterns = [
    path(
        "evaluaciones/",
        menu_evaluaciones,
        name="menu_evaluaciones",
    ),
    path(
        "evaluaciones/visitaasignatura/<int:asignatura_id>/<int:trimestre>/",
        visita_asignatura,
        name="visita_asignatura",
    ),
    path(
        "evaluaciones/visitaasignatura/<int:asignatura_id>/<int:trimestre>/<int:orden>/",
        visita_asignatura,
        name="visita_asignatura_orden",
    ),
]
