from base.api import views
from django.urls import path

from base.api.views import getRoutes, getRooms

urlpatterns = [
    path('', views.getRoutes),
    path('rooms/', views.getRooms),
    path('rooms/<str:pk>', views.getRoom),
    
]
