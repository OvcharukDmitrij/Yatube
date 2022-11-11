from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'username': 'Имя для сайта',
            'email': 'Электронная почта'
        }
        help_texts = {
            'first_name': 'Введите ваше имя',
            'last_name': 'Введите вашу фамилию',
            'username': 'Под этим именем вас будут видеть на сайте',
            'email': 'Укажите адрес эл. почты'
        }
