from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.urls import reverse_lazy
from .models import Note
from .forms import NoteForm


class Home(ListView):
    """Главная страница: список заметок (публичная)."""
    model = Note
    template_name = 'notes/list.html'
    context_object_name = 'notes'
    paginate_by = 10

    def get_queryset(self):
        return Note.objects.all().order_by('-pub_date')


class NotesList(ListView):
    """Страница списка заметок (notes/) — дублирует логику Home,
    если нужно отдельное имя URL.
    """
    model = Note
    template_name = 'notes/list.html'
    context_object_name = 'notes'
    paginate_by = 10

    def get_queryset(self):
        return Note.objects.all().order_by('-pub_date')


class NoteDetail(LoginRequiredMixin, DetailView):
    model = Note
    template_name = 'notes/detail.html'
    context_object_name = 'note'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.author != self.request.user:
            raise Http404("Заметка не найдена")
        return obj


class NoteCreate(LoginRequiredMixin, CreateView):
    """Создание заметки (только для авторизованных)."""
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'
    success_url = reverse_lazy('notes:success')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class NoteUpdate(LoginRequiredMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = 'notes/form.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.author != self.request.user:
            raise Http404("Заметка не найдена")
        return obj

    def get_success_url(self):
        return reverse_lazy('notes:detail', kwargs={'slug': self.object.slug})


class NoteDelete(LoginRequiredMixin, DeleteView):
    model = Note
    template_name = 'notes/delete.html'
    success_url = reverse_lazy('notes:list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.author != self.request.user:
            raise Http404("Заметка не найдена")
        return obj


class NoteSuccess(TemplateView):
    """Страница успеха после создания заметки."""
    template_name = 'notes/success.html'
