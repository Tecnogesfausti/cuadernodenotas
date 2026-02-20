from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import (
    AlumnoEvaluableUsuario,
    AlumnoEvaluableUsuarioAsignaturas,
    Asignatura,
    AsuntoEvaluadoUsuario,
    ConceptoEvaluado,
    Grupo,
    Importacion,
)


def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _latest_importacion():
    return Importacion.objects.order_by("-id").first()


@login_required
def menu_evaluaciones(request):
    latest_importacion = _latest_importacion()
    grupo_id = _to_int(request.GET.get("grupo_id"))
    trimestre = _to_int(request.GET.get("trimestre"), 1)

    grupos = Grupo.objects.none()
    asignaturas = Asignatura.objects.none()
    grupo_sel = None

    if latest_importacion:
        grupos = Grupo.objects.filter(alumno__importacion_id=latest_importacion.id).distinct().order_by("grupo")
        if grupo_id:
            grupo_sel = grupos.filter(pk=grupo_id).first()
            if grupo_sel:
                asignatura_ids_qs = (
                    AlumnoEvaluableUsuarioAsignaturas.objects.filter(
                        alumno_evaluable__alumno__importacion_id=latest_importacion.id,
                        alumno_evaluable__alumno__grupo_id=grupo_sel.id,
                    )
                    .values_list("asignatura_id", flat=True)
                    .distinct()
                )
                asignaturas = (
                    Asignatura.objects.filter(
                        id__in=asignatura_ids_qs,
                        conceptoevaluado__importacion_id=latest_importacion.id,
                        conceptoevaluado__trimestre=trimestre,
                    )
                    .distinct()
                    .order_by("nombre")
                )

    return render(
        request,
        "legacy_models/menu_evaluaciones.html",
        {
            "latest_importacion": latest_importacion,
            "grupos": grupos,
            "grupo_id": grupo_id,
            "grupo_sel": grupo_sel,
            "trimestre": trimestre,
            "asignaturas": asignaturas,
        },
    )


@login_required
def visita_asignatura(request, asignatura_id, trimestre, orden=0):
    latest_importacion = _latest_importacion()
    grupo_id = _to_int(request.GET.get("grupo_id"))
    grupo_sel = None
    if latest_importacion is None:
        return render(
            request,
            "legacy_models/visita_asignatura.html",
            {
                "asignatura": None,
                "trimestre": trimestre,
                "orden": orden,
                "conceptos": [],
                "filas": [],
                "latest_importacion": None,
                "grupo_id": None,
                "grupo_sel": None,
            },
        )

    asignatura = get_object_or_404(Asignatura, pk=asignatura_id)
    if grupo_id:
        grupo_sel = Grupo.objects.filter(pk=grupo_id).first()
        if not grupo_sel:
            grupo_id = None

    conceptos = list(
        ConceptoEvaluado.objects.filter(
            importacion_id=latest_importacion.id,
            asignatura_id=asignatura.id,
            trimestre=trimestre,
        ).order_by("id")
    )

    alumnos_qs = AlumnoEvaluableUsuario.objects.filter(alumno__importacion_id=latest_importacion.id).select_related(
        "alumno", "alumno__grupo"
    )
    if grupo_id:
        alumnos_qs = alumnos_qs.filter(alumno__grupo_id=grupo_id)
    if orden == 1:
        alumnos_qs = alumnos_qs.order_by("alumno__nombre")
    else:
        alumnos_qs = alumnos_qs.order_by("alumno__grupo__grupo", "alumno__nombre")
    alumnos = list(alumnos_qs)

    asuntos = AsuntoEvaluadoUsuario.objects.filter(
        alumno_evaluable__in=alumnos,
        concepto_evaluado__in=conceptos,
    ).select_related("alumno_evaluable", "concepto_evaluado")

    asuntos_map = {(a.alumno_evaluable_id, a.concepto_evaluado_id): a for a in asuntos}
    filas = []
    for alumno in alumnos:
        celdas = [asuntos_map.get((alumno.alumno_id, concepto.id)) for concepto in conceptos]
        filas.append({"alumno": alumno, "celdas": celdas})

    return render(
        request,
        "legacy_models/visita_asignatura.html",
        {
            "asignatura": asignatura,
            "trimestre": trimestre,
            "orden": orden,
            "conceptos": conceptos,
            "filas": filas,
            "latest_importacion": latest_importacion,
            "grupo_id": grupo_id,
            "grupo_sel": grupo_sel,
        },
    )
