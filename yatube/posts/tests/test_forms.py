import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, User

GROUP_TITLE = 'Тестовый заголовок'
GROUP_SLUG = 'test_slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый текст'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.group
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.client = User.objects.get(username='auth')
        cls.authorized_client.force_login(cls.user)
        cls.form = PostForm()

        cache.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': POST_TEXT,
            'group': PostCreateFormsTest.group.id,
            'image': uploaded
        }
        response = PostCreateFormsTest.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEquals(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())

    def test_edit_post(self):
        """Валидная форма меняет запись в существующем Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый текст',
        }
        response = PostCreateFormsTest.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostCreateFormsTest.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertEquals(Post.objects.count(), post_count)
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostCreateFormsTest.post.id}'})
        )
        self.assertEqual(
            response.context.get('post').text, form_data['text']
        )
