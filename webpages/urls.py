from django.urls import path
from webpages import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('webpages/', views.WebPageListView.as_view(), name='webpages'),
    path('add_webpage/', views.add_webpage, name='add_webpage'),
]
