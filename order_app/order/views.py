from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.messages import views
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterView
from .models import Order, OrderItem
from order_app.item.models import Item
from .serializers import OrderSerializer
from .forms import OrderCreateForm, OrderUpdateForm
from .filters import OrderFilter
from django.core.exceptions import ValidationError


class OrdersAPIView(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status']
    search_fields = ['table_number', 'status']


class OrdersListView(FilterView):
    queryset = Order.objects.all()
    template_name = 'order/orders.html'
    filterset_class = OrderFilter
    context_object_name = 'orders'


class OrderCreateView(views.SuccessMessageMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'order/order_create.html'
    success_message = 'Order has been created'
    success_url = reverse_lazy('orders')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        return context

    def form_valid(self, form):
        try:
            response = super().form_valid(form) 
            order = self.object
            items_added = False


            for key, quantity in self.request.POST.items():
                if key.startswith('item_') and quantity.isdigit():
                    item_id = key.split('_')[1]
                    try:
                        item = Item.objects.get(id=item_id)
                        if int(quantity) > 0:
                            OrderItem.objects.create(order=order, item=item, quantity=int(quantity))
                            items_added = True
                    except Item.DoesNotExist:
                        self.object.delete()
                        messages.ERROR(self.request, "There is no such item.")
                        return self.form_invalid(form)
            if not items_added:
                order.delete()
                raise ValidationError("You can't create an order without any item")
            order.calculate_total_price()
            return response
                
        except ValueError:
                    self.object.delete()
                    messages.ERROR(self.request, "Check quantity")
                    return self.form_invalid(form)


class OrderDetailView(DetailView):
    model = Order
    template_name='order/order_detail.html'


class OrderUpdateView(views.SuccessMessageMixin, UpdateView):
    model=Order
    form_class=OrderUpdateForm
    template_name='order/order_update.html'
    success_message='Order has been changed'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = Item.objects.all()
        context['form'] = OrderUpdateForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('order_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        order = self.object
        added_order_items = OrderItem.objects.filter(order=order)
        for order_item in added_order_items:
            quantity =  self.request.POST.get(f'item_{order_item.item.id}')
            if quantity and int(quantity) > 0:
                order_item.quantity += int(quantity)
                order_item.save()
        order.calculate_total_price()
        return response


class OrderDeleteView(views.SuccessMessageMixin, DeleteView):
    model=Order
    template_name='order/order_delete.html'
    success_message='Order was deleted'
    success_url= reverse_lazy('orders')
