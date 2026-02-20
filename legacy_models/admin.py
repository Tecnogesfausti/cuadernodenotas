from django.contrib import admin

from .models import (
    Alumno,
    AlumnoEvaluableUsuario,
    AlumnoEvaluableUsuarioAsignaturas,
    Anotacion,
    Asignatura,
    AsuntoEvaluadoUsuario,
    ConceptoEvaluado,
    ConceptoMensajeEnviado,
    CorreoUsuario,
    Docente,
    FotoAlumno,
    GMailAlumnoUsuario,
    Grupo,
    Importacion,
    Mensaje,
    Version,
)


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def get_readonly_fields(self, request, obj=None):
        concrete = [f.name for f in self.model._meta.fields]
        many_to_many = [f.name for f in self.model._meta.many_to_many]
        return concrete + many_to_many


class ReadOnlyInlineMixin:
    can_delete = False
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        concrete = [f.name for f in self.model._meta.fields]
        many_to_many = [f.name for f in self.model._meta.many_to_many]
        return concrete + many_to_many


class LatestImportacionQuerysetMixin:
    importacion_lookup = None

    def get_latest_importacion_id(self):
        return Importacion.objects.order_by("-id").values_list("id", flat=True).first()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_importacion_id = self.get_latest_importacion_id()
        if latest_importacion_id is None:
            return qs.none()
        if self.importacion_lookup:
            return qs.filter(**{self.importacion_lookup: latest_importacion_id})
        return qs


class AlumnoInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = Alumno
    fk_name = "importacion"
    show_change_link = True
    fields = ("nombre", "codhistorial", "documento", "grupo")


class ConceptoEvaluadoInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = ConceptoEvaluado
    fk_name = "importacion"
    show_change_link = True
    fields = ("descripcion", "asignatura", "trimestre", "peso_nota")


class AlumnoEvaluableUsuarioAsignaturasInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = AlumnoEvaluableUsuarioAsignaturas
    fk_name = "alumno_evaluable"
    autocomplete_fields = ("asignatura",)


class AsuntoEvaluadoUsuarioInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = AsuntoEvaluadoUsuario
    fk_name = "alumno_evaluable"
    show_change_link = True
    fields = ("concepto_evaluado", "nota", "fecha", "gruponumero")
    autocomplete_fields = ("concepto_evaluado",)


class GMailAlumnoUsuarioInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = GMailAlumnoUsuario
    fk_name = "alumno_evaluable"
    show_change_link = True
    fields = ("gmail",)


class FotoAlumnoInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = FotoAlumno
    fk_name = "alumno_evaluable"
    show_change_link = True
    fields = ("foto",)


class CorreoUsuarioInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = CorreoUsuario
    fk_name = "gmail_alumno"
    show_change_link = True
    fields = ("asunto", "correo_id", "fecha", "adjuntos", "invalido")


class CorreoUsuarioPorAsuntoInline(ReadOnlyInlineMixin, admin.TabularInline):
    model = CorreoUsuario
    fk_name = "asunto_evaluado"
    show_change_link = True
    fields = ("gmail_alumno", "asunto", "fecha", "invalido")
    autocomplete_fields = ("gmail_alumno",)


@admin.register(Importacion)
class ImportacionAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "id"
    list_display = ("id", "curso", "codigo", "denominacion", "version", "ocultar")
    list_filter = ("ocultar", "curso")
    search_fields = ("curso", "codigo", "denominacion")
    inlines = (AlumnoInline, ConceptoEvaluadoInline)


@admin.register(Grupo)
class GrupoAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "grupo")
    search_fields = ("grupo",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_importacion_id = Importacion.objects.order_by("-id").values_list("id", flat=True).first()
        if latest_importacion_id is None:
            return qs.none()
        return qs.filter(alumno__importacion_id=latest_importacion_id).distinct()


@admin.register(Alumno)
class AlumnoAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "importacion_id"
    list_display = ("id", "nombre", "codhistorial", "documento", "grupo", "importacion")
    list_filter = ("importacion", "grupo")
    search_fields = ("nombre", "codhistorial", "documento", "telefono")
    autocomplete_fields = ("importacion", "grupo")


@admin.register(AlumnoEvaluableUsuario)
class AlumnoEvaluableUsuarioAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "alumno__importacion_id"
    list_display = ("alumno", "usuario", "notamedia", "n_correos_gmail", "n_correos_sin_asunto")
    list_filter = ("usuario",)
    search_fields = ("alumno__nombre", "alumno__codhistorial")
    autocomplete_fields = ("alumno", "usuario")
    inlines = (
        AlumnoEvaluableUsuarioAsignaturasInline,
        GMailAlumnoUsuarioInline,
        AsuntoEvaluadoUsuarioInline,
        FotoAlumnoInline,
    )


@admin.register(Asignatura)
class AsignaturaAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "nombre", "usuario")
    list_filter = ("usuario",)
    search_fields = ("nombre",)
    autocomplete_fields = ("usuario",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        latest_importacion_id = Importacion.objects.order_by("-id").values_list("id", flat=True).first()
        if latest_importacion_id is None:
            return qs.none()
        return qs.filter(conceptoevaluado__importacion_id=latest_importacion_id).distinct()


@admin.register(AlumnoEvaluableUsuarioAsignaturas)
class AlumnoEvaluableUsuarioAsignaturasAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "alumno_evaluable__alumno__importacion_id"
    list_display = ("id", "alumno_evaluable", "asignatura")
    list_filter = ("asignatura",)
    search_fields = ("alumno_evaluable__alumno__nombre", "asignatura__nombre")
    autocomplete_fields = ("alumno_evaluable", "asignatura")


@admin.register(ConceptoEvaluado)
class ConceptoEvaluadoAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "importacion_id"
    list_display = ("id", "descripcion", "asignatura", "trimestre", "peso_nota", "importacion")
    list_filter = ("trimestre", "asignatura", "importacion")
    search_fields = ("descripcion", "asignatura__nombre")
    autocomplete_fields = ("importacion", "asignatura", "usuario")


@admin.register(AsuntoEvaluadoUsuario)
class AsuntoEvaluadoUsuarioAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "concepto_evaluado__importacion_id"
    list_display = ("id", "alumno_evaluable", "concepto_evaluado", "nota", "fecha", "gruponumero")
    list_filter = ("fecha", "concepto_evaluado__asignatura")
    search_fields = ("alumno_evaluable__alumno__nombre", "concepto_evaluado__descripcion", "anotaciones")
    autocomplete_fields = ("alumno_evaluable", "concepto_evaluado")
    inlines = (CorreoUsuarioPorAsuntoInline,)


@admin.register(GMailAlumnoUsuario)
class GMailAlumnoUsuarioAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "alumno_evaluable__alumno__importacion_id"
    list_display = ("id", "gmail", "alumno_evaluable")
    search_fields = ("gmail", "alumno_evaluable__alumno__nombre")
    autocomplete_fields = ("alumno_evaluable",)
    inlines = (CorreoUsuarioInline,)


@admin.register(CorreoUsuario)
class CorreoUsuarioAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "gmail_alumno__alumno_evaluable__alumno__importacion_id"
    list_display = ("id", "asunto", "correo_id", "fecha", "adjuntos", "invalido", "gmail_alumno")
    list_filter = ("invalido", "fecha")
    search_fields = ("asunto", "correo_id", "destinatario", "gmail_alumno__gmail")
    autocomplete_fields = ("asunto_evaluado", "gmail_alumno")


@admin.register(FotoAlumno)
class FotoAlumnoAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "alumno_evaluable__alumno__importacion_id"
    list_display = ("id", "alumno_evaluable", "foto")
    search_fields = ("alumno_evaluable__alumno__nombre",)
    autocomplete_fields = ("alumno_evaluable",)


@admin.register(Docente)
class DocenteAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "documento", "nombre", "telefono1", "telefono2")
    search_fields = ("documento", "nombre")


@admin.register(Mensaje)
class MensajeAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "texto")
    search_fields = ("texto",)


@admin.register(ConceptoMensajeEnviado)
class ConceptoMensajeEnviadoAdmin(LatestImportacionQuerysetMixin, ReadOnlyAdminMixin, admin.ModelAdmin):
    importacion_lookup = "importacion_id"
    list_display = ("id", "importacion", "mensaje_predefinido", "mensajepersonalizado", "fechaenvio", "prioridad")
    list_filter = ("prioridad", "importacion")
    search_fields = ("mensajepersonalizado",)
    autocomplete_fields = ("importacion", "mensaje_predefinido")


@admin.register(Anotacion)
class AnotacionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "descripcion", "fecha")
    list_filter = ("fecha",)
    search_fields = ("descripcion",)


@admin.register(Version)
class VersionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("id", "revisioncodigo", "revisiondatos", "fecha")
    list_filter = ("fecha",)
