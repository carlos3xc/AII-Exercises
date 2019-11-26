from django.db import models

class Usuario(models.Model):
    id_usuario = models.IntegerField(primary_key=True)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=1, choices=[('F', 'Femenino'), ('M', 'Masculino')])
    #ocupacion =
    codigo_postal = models.CharField(max_length=5)

    def __str__(self):
        return self.id_usuario


class Pelicula(models.Model):
    id_pelicula = models.IntegerField(primary_key=True)
    titulo = models.CharField(max_length=100)
    fecha_estreno = models.DateField()
    imdb_url = models.URLField()
    #categorias=

    def __str__(self):
        return self.id_pelicula


class Categoria(models.Model):
    id_categoria = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.id_categoria

class Ocupacion(models.Model):
    id_ocupacion = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Puntuacion(models.Model):
    id_puntuacion = models.IntegerField(primary_key=True)
    puntuacion = models.IntegerField()

    def __str__(self):
        return self.id_puntuacion