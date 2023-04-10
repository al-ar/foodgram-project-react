from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    email = models.EmailField(
        max_length=254,
        unique=True,
        blank=False,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        verbose_name='Уникальный юзернейм'
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Имя')
    last_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Фамилия')
    password = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Пароль')
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

    class Meta:
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'
        db_table = 'db_follow'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='user_author')
        ]
