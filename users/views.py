import uuid
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView

from common.views import TitleMixin
from users.forms import UserLoginForm, UserProfileForm, UserRegisterForm
from users.models import EmailVerification, User


class UserLoginView(TitleMixin, LoginView):
    template_name = 'users/login.html'
    form_class = UserLoginForm
    # extra_context = {'title': 'Store - Авторизация'}
    title = 'Store - Авторизация'


class UserRegistrationView(TitleMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    # extra_context = {'title': 'Store - Регистрация'}
    title = 'Store - Регистрация'
    success_message = 'Вы успешно зарегистрированы!'


class UserProfileView(LoginRequiredMixin, TitleMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    title = 'Store - Личный кабинет'
    login_url = reverse_lazy('users:login')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:profile')


class EmailVerificationView(TitleMixin, TemplateView):
    title = 'Store - Подтверждение электронной почты'
    template_name = 'users/email_verification.html'
    is_success = True

    def get(self, request, *args, **kwargs):
        code = kwargs.get('code')
        user = User.objects.get(email=kwargs.get('email'))
        email_verifications = EmailVerification.objects.filter(user=user, code=code).first()

        if not email_verifications:
            return HttpResponseRedirect(reverse('index'))

        if email_verifications.is_expired():
            self.is_success = False
            email_verifications.code = uuid.uuid4()
            email_verifications.expiration = now() + timedelta(hours=24)
            email_verifications.save()
            email_verifications.send_verification_email(is_expired=True)
            return super(EmailVerificationView, self).get(request, *args, **kwargs)

        if email_verifications:
            user.is_verified_email = True
            user.save()
            return super(EmailVerificationView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('index'))

    def get_context_data(self, **kwargs):
        context = super(EmailVerificationView, self).get_context_data()
        if self.is_success:
            context['message'] = 'Почта успешно подтверждена'
        else:
            context['message'] = 'Ссылка для подтверждения почты устарела. Новая ссылка отправлена снова.'
        return context
