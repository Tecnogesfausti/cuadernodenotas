# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.conf import settings
from django.db import models


class Alumno(models.Model):
    id = models.BigAutoField(primary_key=True)
    importacion = models.ForeignKey('Importacion', models.DO_NOTHING)
    codhistorial = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    documento = models.CharField(max_length=255)
    domicilio = models.CharField(max_length=255)
    localidad = models.CharField(max_length=50)
    provincia = models.CharField(max_length=50)
    codpostal = models.CharField(max_length=10)
    telefono = models.CharField(max_length=255)
    grupo = models.ForeignKey('Grupo', models.DO_NOTHING, db_column='codgrupo_id', blank=True, null=True)
    comentario = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'alumnos_alumno'
        verbose_name = 'Alumno'
        verbose_name_plural = 'Alumnos'


class Anotacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField(blank=True, null=True)
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = False
        db_table = 'alumnos_anotacion'
        verbose_name = 'Anotacion'
        verbose_name_plural = 'Anotaciones'


class ConceptoMensajeEnviado(models.Model):
    id = models.BigAutoField(primary_key=True)
    fechaenvio = models.DateTimeField()
    mensajepersonalizado = models.CharField(max_length=255, blank=True, null=True)
    prioridad = models.BigIntegerField(blank=True, null=True)
    importacion = models.ForeignKey('Importacion', models.DO_NOTHING)
    mensaje_predefinido = models.ForeignKey('Mensaje', models.DO_NOTHING, db_column='mensajepredefinido_id', blank=True, null=True)

    def __str__(self):
        return self.mensajepersonalizado or f'Mensaje {self.id}'

    class Meta:
        managed = False
        db_table = 'alumnos_conceptomensajeenviado'
        verbose_name = 'Concepto de mensaje enviado'
        verbose_name_plural = 'Conceptos de mensajes enviados'


class Grupo(models.Model):
    id = models.BigAutoField(primary_key=True)
    grupo = models.TextField()

    def __str__(self):
        return self.grupo

    class Meta:
        managed = False
        db_table = 'alumnos_grupo'
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'


class Importacion(models.Model):
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=10)
    denominacion = models.CharField(max_length=255)
    curso = models.CharField(max_length=10)
    fechaexportacion = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=10)
    idfaltas = models.FloatField()
    ocultar = models.BooleanField()

    def __str__(self):
        return f'{self.curso} ({self.id})'

    class Meta:
        managed = False
        db_table = 'alumnos_importacion'
        verbose_name = 'Importacion'
        verbose_name_plural = 'Importaciones'


class Mensaje(models.Model):
    id = models.BigAutoField(primary_key=True)
    texto = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.texto or f'Mensaje {self.id}'

    class Meta:
        managed = False
        db_table = 'alumnos_mensaje'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'


class Docente(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    telefono1 = models.CharField(max_length=255)
    telefono2 = models.CharField(max_length=255)
    domicilio = models.CharField(max_length=255)
    documento = models.CharField(max_length=255)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f'{self.documento} {self.nombre}'

    class Meta:
        managed = False
        db_table = 'docente_docente'
        verbose_name = 'Docente'
        verbose_name_plural = 'Docentes'


class AlumnoEvaluableUsuario(models.Model):
    alumno = models.OneToOneField(Alumno, models.DO_NOTHING, db_column='alumno_ptr_id', primary_key=True)
    notamedia = models.CharField(max_length=255, blank=True, null=True)
    n_correos_gmail = models.BigIntegerField(db_column='ncorreousuariosgmail', blank=True, null=True)
    n_correos_sin_asunto = models.BigIntegerField(db_column='ncorreousuariossinasunto', blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='uregistrado_id', blank=True, null=True)

    def __str__(self):
        return str(self.alumno)

    class Meta:
        managed = False
        db_table = 'evaluaciones_alumnoevaluableusuario'
        verbose_name = 'Alumno evaluable'
        verbose_name_plural = 'Alumnos evaluables'


class AlumnoEvaluableUsuarioAsignaturas(models.Model):
    id = models.BigAutoField(primary_key=True)
    alumno_evaluable = models.ForeignKey(AlumnoEvaluableUsuario, models.DO_NOTHING, db_column='alumnoevaluableusuario_id')
    asignatura = models.ForeignKey('Asignatura', models.DO_NOTHING)

    def __str__(self):
        return f'{self.alumno_evaluable} - {self.asignatura}'

    class Meta:
        managed = False
        db_table = 'evaluaciones_alumnoevaluableusuario_asignaturas'
        unique_together = (('alumno_evaluable', 'asignatura'),)
        verbose_name = 'Asignatura de alumno evaluable'
        verbose_name_plural = 'Asignaturas de alumnos evaluables'


class Asignatura(models.Model):
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='uregistrado_id', blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'evaluaciones_asignatura'
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'


class AsuntoEvaluadoUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    valoracion = models.CharField(max_length=255)
    nota = models.TextField()
    fecha = models.DateField(blank=True, null=True)
    anotaciones = models.CharField(max_length=255)
    gruponumero = models.BigIntegerField(blank=True, null=True)
    alumno_evaluable = models.ForeignKey(AlumnoEvaluableUsuario, models.DO_NOTHING, db_column='alumnoevaluableusuario_id')
    concepto_evaluado = models.ForeignKey('ConceptoEvaluado', models.DO_NOTHING, db_column='conceptoevaluado_id')

    def __str__(self):
        return f'Asunto {self.id}'

    class Meta:
        managed = False
        db_table = 'evaluaciones_asuntoevaluadousuario'
        verbose_name = 'Asunto evaluado'
        verbose_name_plural = 'Asuntos evaluados'


class ConceptoEvaluado(models.Model):
    id = models.BigAutoField(primary_key=True)
    importacion = models.ForeignKey(Importacion, models.DO_NOTHING)
    descripcion = models.CharField(max_length=255)
    peso_nota = models.BigIntegerField(db_column='pesonota')
    asignatura = models.ForeignKey(Asignatura, models.DO_NOTHING)
    trimestre = models.BigIntegerField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.DO_NOTHING, db_column='uregistrado_id', blank=True, null=True)
    modo = models.BigIntegerField()

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = False
        db_table = 'evaluaciones_conceptoevaluado'
        verbose_name = 'Concepto evaluado'
        verbose_name_plural = 'Conceptos evaluados'


class CorreoUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    correo_id = models.CharField(db_column='idcorreousuario', max_length=255)
    asunto = models.CharField(max_length=255)
    fecha = models.DateField(blank=True, null=True)
    adjuntos = models.BigIntegerField()
    anotaciones = models.CharField(max_length=255)
    invalido = models.BooleanField(blank=True, null=True)
    asunto_evaluado = models.ForeignKey(AsuntoEvaluadoUsuario, models.DO_NOTHING, db_column='asuntoevaluadousuario_id', blank=True, null=True)
    gmail_alumno = models.ForeignKey('GMailAlumnoUsuario', models.DO_NOTHING, db_column='gmailalumnousuario_id')
    destinatario = models.CharField(max_length=255)

    def __str__(self):
        return self.asunto

    class Meta:
        managed = False
        db_table = 'evaluaciones_correousuario'
        verbose_name = 'Correo de usuario'
        verbose_name_plural = 'Correos de usuario'


class FotoAlumno(models.Model):
    foto = models.CharField(max_length=100, blank=True, null=True)
    alumno_evaluable = models.ForeignKey(AlumnoEvaluableUsuario, models.DO_NOTHING, db_column='alumnoevaluableusuario_id')

    def __str__(self):
        return f'Foto {self.id}'

    class Meta:
        managed = False
        db_table = 'evaluaciones_fotoalumno'
        verbose_name = 'Foto de alumno'
        verbose_name_plural = 'Fotos de alumnos'


class GMailAlumnoUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    gmail = models.CharField(max_length=255)
    alumno_evaluable = models.ForeignKey(AlumnoEvaluableUsuario, models.DO_NOTHING, db_column='alumnoevaluableusuario_id')

    def __str__(self):
        return self.gmail

    class Meta:
        managed = False
        db_table = 'evaluaciones_gmailalumnousuario'
        verbose_name = 'Email de alumno'
        verbose_name_plural = 'Emails de alumnos'


class Version(models.Model):
    id = models.BigAutoField(primary_key=True)
    revisioncodigo = models.BigIntegerField()
    revisiondatos = models.BigIntegerField()
    fecha = models.DateTimeField(blank=True, null=True)
    novedades = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.revisioncodigo}.{self.revisiondatos}'

    class Meta:
        managed = False
        db_table = 'importaciones_version'
        verbose_name = 'Version'
        verbose_name_plural = 'Versiones'
