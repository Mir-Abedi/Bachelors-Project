from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('webpages/', views.WebPageListView.as_view(), name='webpages'),
    path('add_webpage/', views.add_webpage, name='add_webpage'),
    path('webpage/<int:pk>/', views.WebPageDetailView.as_view(), name='webpage_detail'),
    path('author/<int:author_id>/update-email/', views.update_author_email, name='update_author_email'),
    path('author/<int:author_id>/', views.AuthorDetailView.as_view(), name='author_detail'),
]
