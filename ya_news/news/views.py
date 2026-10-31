"""Модуль views для приложения news: представления новостей и комментариев."""

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from .forms import CommentForm
from .models import Comment, News


class NewsList(generic.ListView):
    """Список новостей на главной странице."""

    model = News
    template_name = 'news/home.html'
    context_object_name = 'news_feed'

    def get_queryset(self):
        """Возвращает ограниченное количество последних новостей."""
        return self.model.objects.prefetch_related(
            'comment_set'
        )[:settings.NEWS_COUNT_ON_HOME_PAGE]


class NewsDetail(generic.DetailView):
    """Детальная страница новости с комментариями."""

    model = News
    template_name = 'news/detail.html'

    def get_object(self, queryset=None):
        """Получает объект новости с предзагрузкой комментариев и авторов."""
        obj = get_object_or_404(
            self.model.objects.prefetch_related('comment_set__author'),
            pk=self.kwargs['pk']
        )
        return obj

    def get_context_data(self, **kwargs):
        """Добавляет форму для комментария, если пользователь авторизован."""
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['form'] = CommentForm()
        return context


class NewsComment(
    LoginRequiredMixin,
    generic.detail.SingleObjectMixin,
    generic.FormView
):
    """Обработка формы добавления комментария к новости."""

    model = News
    form_class = CommentForm
    template_name = 'news/detail.html'

    def post(self, request, *args, **kwargs):
        """Обрабатывает POST‑запрос для комментария."""
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Сохраняет комментарий, устанавливая автора и привязку к новости."""
        comment = form.save(commit=False)
        comment.news = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Возвращает URL страницы новости с якорем #comments."""
        post = self.get_object()
        return (
            reverse('news:detail', kwargs={'pk': post.pk})
            + '#comments'
        )


class NewsDetailView(generic.View):
    """Объединяет отображение новости и обработку формы комментария."""

    def get(self, request, *args, **kwargs):
        """Отображает страницу новости через NewsDetail."""
        view = NewsDetail.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Обрабатывает добавление комментария через NewsComment."""
        view = NewsComment.as_view()
        return view(request, *args, **kwargs)


class CommentBase(LoginRequiredMixin):
    """Базовый класс для редактирования и удаления комментариев."""

    model = Comment

    def dispatch(self, request, *args, **kwargs):
        """
        Проверяет авторизацию и права доступа перед обработкой запроса.

        1. Сначала выполняется стандартная обработка LoginRequiredMixin.
           Если пользователь не авторизован — сразу редирект (302).
        2. Если авторизован, проверяется, является ли он автором комментария.
           Если нет — возвращается 403.
        3. Иначе запрос передаётся дальше (UpdateView/DeleteView).
        """
        response = super().dispatch(request, *args, **kwargs)

        if response.status_code == 302:
            return response

        self.object = self.get_object()
        if self.object.author != request.user:
            return HttpResponseForbidden()

        return response

    def get_success_url(self):
        """URL детальной страницы новости с якорем на комментарии."""
        comment = self.get_object()
        base_url = reverse('news:detail', kwargs={'pk': comment.news.pk})
        return f'{base_url}#comments'


class CommentUpdate(CommentBase, generic.UpdateView):
    """Представление для редактирования комментария."""

    template_name = 'news/edit.html'
    form_class = CommentForm


class CommentDelete(CommentBase, generic.DeleteView):
    """Представление для удаления комментария."""

    template_name = 'news/delete.html'
