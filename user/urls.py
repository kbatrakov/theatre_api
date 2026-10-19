from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from user.views import CreateUserView, CreateTokenView, ManageUserView

app_name = "user"

urlpatterns = [
    path("register/", CreateUserView.as_view(), name="create"),
    path("login/", CreateTokenView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", ManageUserView.as_view(), name="manage"),
]
