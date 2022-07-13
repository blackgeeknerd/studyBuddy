
from django.contrib import admin
from django.urls import path, include
# 

base_url = 'base.urls'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(base_url)) ,
    path('api/', include('base.api.urls'))
]
