# netology_pd73_webpy_aiohttp_hw

## Сборка образа для контейнера с Flask и Gunicorn
Из директории с файлом `Dockerfile` выполнить:
```bash
sudo docker build -t netology_pd73_webpy_aiohttp_hw .
```

## Подготовка файла с переменными окружения
В директории с файлом `docker-compose.yml` создать файл `.env` со следующими переменными окружения:
```
PROJECT_NAME=netology_pd73_webpy_aiohttp_hw
DB_PORT=5432
DB_USER=${PROJECT_NAME}
DB_PWD='...'
DB_NAME=${PROJECT_NAME}

HTTP_SRV_ADDR_PORT='127.0.0.1:80'
```
`DB_PWD='...'` вместо `...` подставить пароль, который будет использоваться для БД

`HTTP_SRV_ADDR_PORT='127.0.0.1:80'` адрес и порт, по которым будет доступно приложение на хосте

## Запуск контейнеров для приложения
```bash
sudo docker compose up -d
```