# Бот под ключ для приема платежей и подписки на закрытый канал
## **Инструкция по установке и настройке** ##

## Арендуйте сервера

### Выбирать сервер VPS для бота и VPN нужно по следующим параметрам:
1. 2 ядра у процессора
2. 2 ГБ Оперативной памяти
3. 20 ГБ HDD/SSD
4. OS Ubuntu 22.04
5. Локацию лучше выбирайте не в РФ

**Могу предложить вот таки варианты:**

https://justhost.ru/ - 800р
https://aeza.net/ru - 10€

## Подключение к серверу

После аренды вам дадут IP сервера и пароль от него

Используйте любую программу для подключения через ssh, 
рекомендую MobaXterm (https://mobaxterm.mobatek.net/download.html)

Если у вас Linux или Mac тогда используйте WindTerm
(https://github.com/kingToolbox/WindTerm/releases/tag/2.6.0)
пролистайте в самый низ и скачайте программу под нужную вам платформу


**После установки(WindTerm):**

  1. Нажмите Сессия
  2. Новая сессия
  3. Выберете SSH
  4. В графу "Хозяин(H)" впишите IP адрес сервера
  5. Нажимайте внизу соединить
  6. В окне Авторизации переходите на вкладку Account
  7. В графу пользователь пишите root
  8. В графу пароль вписывайте пароль

**После установки(MobaXterm):**

  1. Нажмите Session
  2. Выберете SSH
  3. В графе Remote host введите ip адрес 
  4. Нажимайте ОК 
  5. В главном меню выбирайте ваш сервер и начнется подключение
  6. Вас попросят ввести logi, вводите root  
  7. Введите пароль(обычно приходит в письме вместе с ip адресом). 
     Не пугайтесь если не будите видеть что вводите, на самом деле все вводится 
     просто скрыто, такая система защиты от любопытных глаз.


## Установка бота на сервере

Копируйте и вставляйте в командную строку команды:

1. Обновляем все стандартные пакеты

        sudo apt update && sudo apt upgrade -y && sudo apt install curl

2. Устанавливаем Docker

        curl -fSL https://get.docker.com -o get-docker.sh && sudo sh ./get-docker.sh && sudo apt install docker-compose-plugin

3. переносим на сервер папку PrivateClubBot из архива
4. Переходим в папку

       cd PrivateClubBot

5. Откройте файл .env и заполните все поля 
    ````
   ADMINS_ID= ID администраторов в телеграме получить нужно здесь -> https://t.me/userinfobot
   #min.1 day.1 mon.1 year.1
   PERIOD=day.1,day.10,mon.1,mon.3,mon.6,mon.12 Периоды подписки 
   AMOUNT=2,10,349,749,1199,1599 Цены на периоды
   UTC_TIME=3 временной пояс, по умолчанию стоит московское время
   TG_TOKEN= Токен бота нужно получить у BotFather https://t.me/BotFather /newbot
   TG_STARS=off- Удалите off если хотите включить Telegram Stars
   YOOMONEY_TOKEN= Токен Юмани что бы его получить нужно 
            1) зарегистрировать https://yoomoney.ru/myservices/new приложение",
               в ссылках указывайте бота, галочку внизу НЕ СТАВИТЬ!
            2) получить токен выполнив скрипт на этой странице
               https://colab.research.google.com/drive/1QtFtyttF_kq67DUxLjhstE08CaUWQ_RG?usp=sharing
   LAVA_TOKEN_SECRET= Получить секретный токен вы можете здесь https://business.lava.ru/ зарегестрируйте проект
   LAVA_ID_PROJECT= В ссылках указывайте адрес бота, когда проект создан напишите в этот бот с
   YOOKASSA_SHOP_ID= Зарегестрируйте в ЮКассе и создайте там приложение
   YOOKASSA_SECRET_KEY= Берется там же где и shop id
   TINKOFF_TERMINAL= Зарегестрируйтесь и получите здесь https://www.tbank.ru/tinkoff-pay/
   TINKOFF_SECRET= После одобрения необходимо пройти тесты платжной системы, из бота и личного кабинета
   CRYPTOMUS_KEY=Зарегестрируйтесь и создайте приложение здесь https://app.cryptomus.com/dashboard/business/ Payment API key
   CRYPTOMUS_UUID=Появится после создания приложения Merchant ID
   CRYPTO_BOT_API=Перейдите в https://t.me/CryptoBot В главном меню выберете CryptoPay -> Создать приложение. После создания вам нужен API-токен
   ID_CHANNEL=-1002184927159 ID Вашего канала, добавьте бота в админы вашего канала
   LINK_CHANNEL=https://t.me/+DK1QP61GgFo5MTZi Ссылка с на вступление с подключенной функцией "Заявки на вступление" вы можете создать ее в управлении каналом
   NAME_CHANNEL=PrivateClub - Название вашего канала
   
    #DataBase
    POSTGRES_DB=PrivateСlubDB - Название базы данных, можете не менять
    POSTGRES_USER= Имя пользователя для достпука к БД (НЕ ИСПОЛЬЗУЙТЕ СПЕЦСИМВОЛЫ)
    POSTGRES_PASSWORD= Пароль для доступа к БД (НЕ ИСПОЛЬЗУЙТЕ СПЕЦСИМВОЛЫ)
    PGADMIN_DEFAULT_EMAIL= Email для входя в панель управления БД (НЕ ИСПОЛЬЗУЙТЕ СПЕЦСИМВОЛЫ)
    PGADMIN_DEFAULT_PASSWORD= Пароль для входа в панель управления БД (НЕ ИСПОЛЬЗУЙТЕ СПЕЦСИМВОЛЫ)

6. Перейдите в BotFather и выберите /mybots, вашего бота. 
7. Перейдите в Edit Bot - здесь вы можете задать картинки и описания для бота
8. Запускаем бота(если вы будете запускать не из папки с ботом то получите ошибку)

        sudo docker compose up -d

Если вы хотите остановить используйте 
        
       sudo docker compose down

9. Для того что перейти в админ панель бота вы должны зайти в бот и нажать 
кнопку в главном меню


## Редактирование текста

1. Перейти в папку с ботом

       cd PrivateClubBot

2. Остановить бота

       sudo docker compose down

3. Перейти в папку bot/locales/ru/LC_MESSAGES, откройте файл txt.ftl и измените текст

4. Запускаем бота

       sudo docker compose up -d

Для любого изменения в файлах перевода необходимо повторять этот алгоритм!

## Замена картинок

1. Перейти в папку с ботом

       cd PrivateClubBot

2. Остановить бота

       sudo docker compose down

3. Перейти в папку bot/img замените картинки в папке на свои главное оставить прежнее название и расширение .png

4. Запускаем бота

       sudo docker compose up -d


## Редактирование кода

1. Перейти в папку с ботом

       cd PrivateClubBot

2. Остановить бота

       sudo docker compose down

3. Внесите ваши изменения в код

4. Соберите контейнер

       sudo docker compose build

5. Запускаем бота

       sudo docker compose up -d



## Веб панель управления БД
## ВНИМАНИЕ ВСЕ ДЕЙСТВИЯ В ВЕБ ПАНЕЛИ ВЫ ДЕЛАЙТЕ НА СВОЙ СТРАХ И РИСК 
## ЕСЛИ ВЫ НЕ ЗНАЕТЕ ЧТО, ДЕЛАЕТЕ, ТО ЛУЧШЕ НЕ СТОИТ, 
## ДЛЯ РАБОТЫ БОТА ЭТО ДЕЛАТЬ НЕ ОБЯЗАТЕЛЬНО

1. Перейдите по адресу 

       http://vps_ip:5051/ (vps_ip - это ip адрес на котором установлен бот)

2. Введите email и пароль который вы указывали в .env файле в параметрах и поставьте Русский язык

       PGADMIN_DEFAULT_EMAIL и PGADMIN_DEFAULT_PASSWORD

3. Нажмите добавить новый сервер
4. В поле Имя впишите admin
5. Перейдите на вкладку Соединение
6. В поле "Имя/адрес сервера" впишите
   
       db_postgres

7. В поле "Порт" должно быть 5432
8. В поле "Служебная база данных" впишите значение из .env **POSTGRES_DB**
9. В поле "Имя пользователя" впишите значение из .env **POSTGRES_USER**
10. В поле "Пароль" впишите значение из .env **POSTGRES_PASSWORD**


# Все! Бот установлен, теперь вы можете пользоваться ботом
