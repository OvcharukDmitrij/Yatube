import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Comment, Follow

GROUP_TITLE = 'Тестовый заголовок'
GROUP_SLUG = 'test_slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый текст'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
COMMENT_TEXT = 'Тестовый комментарий'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.other_user = User.objects.create_user(username='other_auth')
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text=COMMENT_TEXT,
            author=cls.user,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """Проверяем правильность применения соответствующих шаблонов """
        templates_pages_names = {
            reverse('posts:posts_index'): 'posts/index.html',
            reverse('posts:posts_group',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{PostPagesTest.post.id}'}):
                    'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTest.post.id}'}):
                    'posts/create_post.html'
        }
        for name, template in templates_pages_names.items():
            with self.subTest(name=name):
                response = PostPagesTest.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = PostPagesTest.authorized_client.get(
            reverse('posts:posts_index')
        )
        first_object = response.context['page_obj'][-1]
        post_id_0 = first_object.id
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_id_0, PostPagesTest.post.id)
        self.assertEqual(post_text_0, PostPagesTest.post.text)
        self.assertEqual(post_author_0, PostPagesTest.post.author)
        self.assertEqual(post_group_0, PostPagesTest.post.group)
        self.assertEqual(post_image_0, PostPagesTest.post.image)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = PostPagesTest.authorized_client.get(
            reverse('posts:posts_group', kwargs={'slug': 'test_slug'})
        )
        self.assertEqual(response.context.get('group').title,
                         PostPagesTest.group.title)
        self.assertEqual(response.context.get('group').slug,
                         PostPagesTest.group.slug)
        self.assertEqual(response.context.get('group').description,
                         PostPagesTest.group.description)
        self.assertEqual(response.context['page_obj'][0].image,
                         PostPagesTest.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = PostPagesTest.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(response.context.get('author'),
                         PostPagesTest.post.author)
        self.assertEqual(response.context['page_obj'][0].image,
                         PostPagesTest.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = PostPagesTest.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTest.post.id})
        )
        self.assertEqual(response.context.get('post').id,
                         PostPagesTest.post.id)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = PostPagesTest.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField)
        self.assertIsInstance(
            response.context.get('form').fields.get('image'),
            forms.fields.ImageField)

    def test_post_edit_and_post_create_show_correct_context(self):
        """Шаблон post_edit и post_create сформированы
         с правильным контекстом"""
        responses = {
            'post_edit': PostPagesTest.authorized_client.get(reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{PostPagesTest.post.id}'})
            ),
            'post_create': PostPagesTest.authorized_client.get(
                reverse('posts:post_create')
            )
        }
        for process, response in responses.items():
            with self.subTest(response=response):
                self.assertIsInstance(
                    response.context.get('form').fields.get('text'),
                    forms.fields.CharField
                )
                self.assertIsInstance(
                    response.context.get('form').fields.get('image'),
                    forms.fields.ImageField
                )

    def test_post_on_the_page(self):
        """Проверка наличия созданного поста на страницах
        index, group, profile"""
        response_page = {
            'posts_index': PostPagesTest.authorized_client.get(
                reverse('posts:posts_index')
            ),
            'posts_group': PostPagesTest.authorized_client.get(
                reverse('posts:posts_group', kwargs={'slug': 'test_slug'})
            ),
            'posts_profile': PostPagesTest.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'auth'})
            ),
        }
        for page, response in response_page.items():
            with self.subTest(response=response):
                latest_object = response.context['page_obj'][0]
                post_text_latest = latest_object.text
                self.assertEqual(PostPagesTest.post.text, post_text_latest)

    def test_comment_on_the_page(self):
        response = PostPagesTest.authorized_client.get(
            reverse('posts:posts_index')
        )
        latest_object = response.context['page_obj'][0]
        latest_comment = latest_object.comment
        self.assertEqual(PostPagesTest.post.comment, latest_comment)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_cache(self):
        """Проверка кеширования главной страницы"""
        url = reverse('posts:posts_index')

        response_before = CacheTest.authorized_client.get(url)

        CacheTest.post.delete()

        response_after = CacheTest.authorized_client.get(url)

        cache.clear()

        response_cache_clear = CacheTest.authorized_client.get(url)

        self.assertEqual(
            response_before.content,
            response_after.content
        )
        self.assertNotEqual(
            response_before.content,
            response_cache_clear.content
        )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.other_user = User.objects.create_user(username='other_auth')
        cls.authorized_other_client = Client()
        cls.authorized_other_client.force_login(cls.other_user)
        cls.authors = cls.user.follower.all()
        Post.objects.create(
            text=POST_TEXT,
            author=FollowTest.other_user
        )
        cls.follow = Follow.objects.create(
            user_id=FollowTest.user.id,
            author_id=FollowTest.other_user.id
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_follow(self):
        """Проверяем что записи автора, на которого подписан пользователь,
        появляются у него в ленте 'Избранное'"""
        url = reverse('posts:follow_index')

        response_follow = FollowTest.authorized_client.get(url)
        object_author = response_follow.context['page_obj'][0].author

        self.assertEqual(object_author, FollowTest.follow.author)

    def test_unfollow(self):
        """Проверяем что записи автора, на которого не подписан пользователь,
        не появляются у пользователя в 'Избранное'"""
        url = reverse('posts:follow_index')

        response_not_follow = FollowTest.authorized_other_client.get(url)

        object_not_follow = response_not_follow.context['page_obj'].object_list

        self.assertFalse(object_not_follow)

    def test_follow_auth(self):
        """Проверяем что пользователь не может подписаться на
        самого себя"""
        authors_before_follow = FollowTest.authors.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        authors_after_follow = FollowTest.authors.count()

        self.assertEqual(authors_before_follow, authors_after_follow)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = User.objects.create_user(username='other_auth')
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION
        )
        cls.TOTAL_NUMBERS_POSTS = 13  # Общее количество постов
        cls.FIRST_PAGE_POSTS = 10  # Количество постов на первой странице
        cls.SECOND_PAGE_POSTS = 3  # Количество постов на второй странице
        cls.posts_list = [
            Post(
                text=(str(i) + POST_TEXT),
                author=cls.client,
                group=cls.group,
            )
            for i in range(PaginatorViewsTest.TOTAL_NUMBERS_POSTS)
        ]
        Post.objects.bulk_create(PaginatorViewsTest.posts_list)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response_page_1 = {
            'posts_index': self.client.get(
                reverse('posts:posts_index')
            ),
            'posts_group': self.client.get(
                reverse('posts:posts_group', kwargs={'slug': 'test_slug'})
            ),
            'posts_profile': self.client.get(
                reverse('posts:profile', kwargs={'username': 'other_auth'})
            ),
        }

        response_page_2 = {
            'posts_index': self.client.get(
                reverse('posts:posts_index') + '?page=2'),
            'posts_group': self.client.get(
                reverse('posts:posts_group', kwargs={'slug': 'test_slug'})
                + '?page=2'),
            'posts_profile': self.client.get(
                reverse('posts:profile', kwargs={'username': 'other_auth'})
                + '?page=2'),
        }
        for page, response in response_page_1.items():
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']),
                                 PaginatorViewsTest.FIRST_PAGE_POSTS)

        for page, response in response_page_2.items():
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']),
                                 PaginatorViewsTest.SECOND_PAGE_POSTS)
