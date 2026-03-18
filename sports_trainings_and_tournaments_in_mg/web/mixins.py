from django.shortcuts import redirect


class NoPermissionRedirectMixin:
    def handle_no_permission(self):
        if self.request.user.profile.role == 'teacher':
            return redirect('student dashboard')
        else:
            return redirect('teacher dashboard')
