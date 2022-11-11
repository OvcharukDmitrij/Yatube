from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreateModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        "заголовок",
        max_length=200,
        help_text="напишите название группы"
    )
    slug = models.SlugField(
        "слаг",
        unique=True,
        help_text="придумайте короткое уникальное имя группы"
    )
    description = models.TextField(
        "описание",
        help_text="напишите краткое описание группы"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Группы"
        verbose_name_plural = "Группы"
        ordering = ['title']


class Post(CreateModel):
    text = models.TextField(
        "Текст поста",
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name="Автор"
    )
    group = models.ForeignKey(
        Group,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name="Группа",
        help_text='Группа, к которой будет относиться пост'
    )
    comment = models.ForeignKey(
        'Comment',
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-created']
        verbose_name = "Посты"
        verbose_name_plural = "Посты"


class Comment(CreateModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Комментируемый пост",
        help_text="Выберите комментируемый пост"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор комментария"
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Комментарии"
        verbose_name_plural = "Комментарии"
        ordering = ['text']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
