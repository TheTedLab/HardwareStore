from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from common.views import TitleMixin
from orders.forms import OrderForm
from orders.models import Order


class SuccessTemplateView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'orders/success.html'
    title = 'Store - Спасибо за заказ!'
    login_url = reverse_lazy('users:login')


class OrderListView(LoginRequiredMixin, TitleMixin, ListView):
    template_name = 'orders/orders.html'
    title = 'Store - Заказы'
    queryset = Order.objects.all()
    ordering = ('-created',)
    login_url = reverse_lazy('users:login')

    def get_queryset(self):
        queryset = super(OrderListView, self).get_queryset()
        return queryset.filter(initiator=self.request.user)


class OrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = 'orders/order.html'
    model = Order
    login_url = reverse_lazy('users:login')

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['title'] = f'Store - Заказ #{self.object.id}'
        return context

    def test_func(self):
        return self.request.user == self.get_object().initiator

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('orders:orders_list'))


class OrderCreateView(LoginRequiredMixin, TitleMixin, CreateView):
    template_name = 'orders/order-create.html'
    form_class = OrderForm
    success_url = reverse_lazy('orders:order_create')
    title = 'Store - Оформление заказа'
    login_url = reverse_lazy('users:login')

    def post(self, request, *args, **kwargs):
        super(OrderCreateView, self).post(request, *args, **kwargs)
        order = Order.objects.get(id=self.object.id)
        order.update_after_creation()
        success_url = '{}{}'.format(settings.DOMAIN_NAME, reverse('orders:order_success'))
        return HttpResponseRedirect(success_url)

    def form_valid(self, form):
        form.instance.initiator = self.request.user
        return super(OrderCreateView, self).form_valid(form)
