from django.core.cache import cache
from django.test import TestCase

from ..models import Group, Post, User

GROUP_TITLE = 'Тестовый заголовок'
GROUP_SLUG = 'test_slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый пост длинной не менее 15 символов'
NUMBER_CHARACTERS = 15  # Количество отображаемых символов


class PostModelTest(TestCase):
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
            author=cls.user,
            text=POST_TEXT,
        )

        cache.clear()

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        expected_object_name_group = group.title
        expected_object_name_post = post.text[:NUMBER_CHARACTERS]
        self.assertEqual(expected_object_name_group, str(group))
        self.assertEqual(expected_object_name_post, str(post))
