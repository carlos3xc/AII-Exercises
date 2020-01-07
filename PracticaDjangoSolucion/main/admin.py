from main.models import Usuario, Categoria, Pelicula, Puntuacion, Ocupacion
from django.contrib import admin

admin.site.register(Ocupacion)
admin.site.register(Usuario)
admin.site.register(Categoria)
admin.site.register(Pelicula)
admin.site.register(Puntuacion)