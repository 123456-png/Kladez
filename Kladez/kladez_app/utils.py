from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class UserOwnedMixin:
    """Миксин для проверки, что объект принадлежит пользователю"""

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied("У вас нет доступа к этому объекту")
        return super().dispatch(request, *args, **kwargs)