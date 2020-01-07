#encoding:utf-8
from django import forms
   
class UsuarioBusquedaForm(forms.Form):
    idUsuario = forms.CharField(label="Id de Usuario", widget=forms.TextInput, required=True)
    
class PeliculaBusquedaYearForm(forms.Form):
    year = forms.IntegerField(label="Año de publicación", widget=forms.TextInput, required=True)