from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cartpol/", include('cartpol_app.api.urls'))
]
