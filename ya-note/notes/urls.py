from django.urls import path

from notes import views

app_name = 'notes'

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('add/', views.NoteCreate.as_view(), name='add'),
    path('notes/', views.NotesList.as_view(), name='list'),
    path('done/', views.NoteSuccess.as_view(), name='success'),

    path('<slug:slug>/', views.NoteDetail.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.NoteUpdate.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.NoteDelete.as_view(), name='delete'),
]
