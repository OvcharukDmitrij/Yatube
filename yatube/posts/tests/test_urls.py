from django.core.cache import cache
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group, User

GROUP_TITLE = 'Тестовый заголовок'
GROUP_SLUG = 'test_slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый текст'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other_auth')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.other_authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.other_authorized_client.force_login(cls.other_user)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.group,
        )
        cls.url_open_to_all = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        cls.url_open_to_auth_user = {
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
        }

        cache.clear()

    def test_homepage(self):
        # Делаем запрос к главной странице и проверяем статус
        response = self.guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес публичной страницы использует соответствующий шаблон."""
        for address, template in PostURLTests.url_open_to_all.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
        """URL-адрес приватной страницы использует соответствующий шаблон."""
        for address, template in PostURLTests.url_open_to_auth_user.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_available_to_all(self):
        """Проверяем доступность публичных страниц
         для неавторизованного пользователя"""
        for address in PostURLTests.url_open_to_all.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_available_to_authorized_user(self):
        """Проверяем доступность приватных страниц
         для авторизованного пользователя"""
        for address in PostURLTests.url_open_to_auth_user.keys():
            with self.subTest(address=address):
                response = PostURLTests.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect(self):
        """Проверяем редирект приватных страниц"""
        for address in PostURLTests.url_open_to_auth_user.keys():
            with self.subTest(address=address):
                response = PostURLTests.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_redirect_other_user(self):
        """Проверяем редирект приватных страниц из под другого авторизованного
        пользователя"""
        response = PostURLTests.other_authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_page_404(self):
        """Проверяем несуществующую страницу"""
        response = PostURLTests.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment(self):
        """Проверяем возможность комментировать только
        авторизованными пользователеми"""
        response = PostURLTests.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_follow(self):
        """Проверяем возможность подписываться только
        авторизованными пользователеми"""
        response = PostURLTests.guest_client.get(
            f'/profile/{PostURLTests.post.author.username}/follow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        """Проверяем возможность отписаться от автора только
        авторизованными пользователями"""
        response = PostURLTests.guest_client.get(
            f'/profile/{PostURLTests.post.author.username}/unfollow/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
