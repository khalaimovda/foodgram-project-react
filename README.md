# FoodGram
(Проект развернут на 51.250.17.88)
(Аккаунт администратора: username: admin, email: admin@admin.com, password: admin)

[![Django-app workflow](https://github.com/khalaimovda/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/khalaimovda/foodgram-project-react/actions/workflows/main.yml)

### Описание 

Проект FoodGram является финальным проектом в рамках курса ЯндексПрактикума "Backend-разработка на Python". Проект реализует социальную сеть для публикации рецептов различных блюд.

В функционал входят следующие возможности:
- Просмотр рецептов
- Добавление рецептов в избранное
- Подписка на различных авторов
- Формирования списка покупок на основании рецептов, добавленных в корзину

### Запуск проекта

Клонировать GitHub-репозиторийи : 
``` 
git clone https://github.com/khalaimovda/foodgram-project-react.git
``` 

Перейти в директорию infra:
``` 
cd foodgram-project-react/infra
``` 

Создать файл .env, описав в нем переменные окружения:
``` 
touch .env
``` 

Шаблон заполнения env-файла:
``` 
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_database_password
DB_HOST=db
DB_PORT=5432

SECRET_KEY = your_secret_key
``` 


Запустить создание docker-образов и контейнеров
``` 
docker-compose up -d
``` 

Создать суперпользователя (опционально)
``` 
sudo docker-compose exec backend python manage.py createsuperuser
``` 

Заполнить БД тестовыми данными (опционально)
``` 
sudo docker-compose exec backend python manage.py loaddata db.json
``` 

### Используемые технологии
- Python
- Django
- Gunicorn
- Docker
- Nginx

### Авторы 
- Дмитрий Халаимов
