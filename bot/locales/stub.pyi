from typing import Literal

    
class TranslatorRunner:
    def get(self, path: str, **kwargs) -> str: ...
    
    user: User
    button: Button
    admin: Admin


class User:
    text: UserText
    error: UserError
    button: UserButton
    link: UserLink


class UserText:
    support: UserTextSupport
    subscription: UserTextSubscription
    account: UserTextAccount
    error: UserTextError

    @staticmethod
    def main() -> Literal["""Приветствую 👋
Этот бот поможет тебе попасть в приватный канал
&#34;Путь боксера&#34;

Подписка - ежемесячная, оплату принимаем в любой валюте и крипте.

Отписаться можно в любой момент 🤝"""]: ...

    @staticmethod
    def faq() -> Literal["""Добро пожаловать в наш закрытый канал! 🎟️

Здесь вы найдете эксклюзивный контент, который недоступен в открытом доступе. 🌟
Каждый подписчик получает уникальные материалы, такие как:

1.Личный путь в боксе
2. Обучение техникам
3. Эксклюзивный контент
4. Мотивация и поддержка
5. Общение и ответы на вопросы
6 Тренировки и программы

Этот канал предоставляет эксклюзивный доступ к опыту профессионалов,
персонализированные советы и постоянную мотивацию для достижения ваших целей в боксе."""]: ...


class UserTextSupport:
    input: UserTextSupportInput

    @staticmethod
    def __call__() -> Literal["""🗣 Помощь"""]: ...

    @staticmethod
    def reply() -> Literal["""Ответ администратора на ваше обращение ⬇️"""]: ...


class UserTextSupportInput:
    @staticmethod
    def __call__() -> Literal["""Оставьте своё сообщение, и мы обязательно вам ответим! 💬✨"""]: ...

    @staticmethod
    def succes() -> Literal["""✅ Администраторы уже получили ваше сообщение и вскоре свяжутся с вами"""]: ...

    @staticmethod
    def error() -> Literal["""🚫 Мы не смогли доставить ваше сообщение, попробуйте позже"""]: ...


class UserError:
    message: UserErrorMessage


class UserErrorMessage:
    @staticmethod
    def user_block_bot() -> Literal["""Сообщение не дошло, скорее всего пользователь заблокировал бота"""]: ...


class UserTextSubscription:
    active: UserTextSubscriptionActive
    input: UserTextSubscriptionInput
    description: UserTextSubscriptionDescription
    approve: UserTextSubscriptionApprove
    add: UserTextSubscriptionAdd

    @staticmethod
    def month() -> Literal["""Выберите период оплаты:"""]: ...

    @staticmethod
    def link(*, link) -> Literal["""Ваша ссылка для вступления:

{ $link }"""]: ...

    @staticmethod
    def one_day(*, day) -> Literal["""📢 Внимание ваша подписка закончится через { $day } дн
Скорее продлите подписку пока она не закончится 😁"""]: ...

    @staticmethod
    def end() -> Literal["""😨 Подписка закончилась, скорее возвращайтесь в наше сообщество"""]: ...

    @staticmethod
    def year() -> Literal["""г."""]: ...

    @staticmethod
    def mon() -> Literal["""мес."""]: ...

    @staticmethod
    def day() -> Literal["""дн."""]: ...

    @staticmethod
    def hour() -> Literal["""ч."""]: ...

    @staticmethod
    def minute() -> Literal["""мин."""]: ...

    @staticmethod
    def approv() -> Literal["""Ваша заявка одобрена, добро пожаловать в канал 🎉"""]: ...


class UserTextSubscriptionActive:
    @staticmethod
    def __call__(*, date) -> Literal["""Ваша подписка активна до: { $date }"""]: ...

    @staticmethod
    def no() -> Literal["""Скорее присоединяйся и становись лучше"""]: ...


class UserTextSubscriptionInput:
    email: UserTextSubscriptionInputEmail


class UserTextSubscriptionInputEmail:
    @staticmethod
    def __call__() -> Literal["""Введите ваш Email✉️ что бы мы смогли отправить вам чек"""]: ...

    @staticmethod
    def error() -> Literal["""Email введён не правльно попробуйте еще раз"""]: ...


class UserTextSubscriptionDescription:
    @staticmethod
    def payment() -> Literal["""Оплата подписки"""]: ...

    @staticmethod
    def amount(*, amount) -> Literal["""Оплата на { $amount }₽"""]: ...


class UserTextAccount:
    no: UserTextAccountNo
    list_payment_text: UserTextAccountList_payment_text

    @staticmethod
    def info(*, full_name, id_user, date_sub, date_amount, date_registred) -> Literal["""💎 Ваш профиль:
👤 Имя: { $full_name }
🆔: { $id_user }
📅 Подписка до: { $date_sub }
💳 Полседние продление: { $date_amount }
💠 Дата регистрации: { $date_registred }"""]: ...

    @staticmethod
    def list_payment_file() -> Literal["""Вот файл с вашими платежами"""]: ...


class UserTextAccountNo:
    @staticmethod
    def payment() -> Literal["""Отсутствует 😔"""]: ...

    @staticmethod
    def subscription() -> Literal["""Вы не подписаны 😔"""]: ...


class UserTextAccountList_payment_text:
    @staticmethod
    def __call__() -> Literal["""📊Ваши платежи:"""]: ...

    @staticmethod
    def no() -> Literal["""Вы не совершали платежей 😔"""]: ...

    @staticmethod
    def date(*, date) -> Literal["""Дата: { $date }"""]: ...

    @staticmethod
    def amount(*, amount) -> Literal["""Оплата на : { $amount }₽"""]: ...


class Button:
    @staticmethod
    def pressed() -> Literal["""Начинаем работать"""]: ...


class UserTextSubscriptionApprove:
    @staticmethod
    def none() -> Literal["""У вас отсутствует подписка, здесь вы можете получить ее"""]: ...


class UserTextError:
    input: UserTextErrorInput


class UserTextErrorInput:
    @staticmethod
    def number() -> Literal["""🚫 Ошибка 🚫
Вы ввели не число"""]: ...


class UserTextSubscriptionAdd:
    @staticmethod
    def time(*, link, new_date) -> Literal["""Администратор изменил ваше время подписки!
Вот ваша ссылка на канал: { $link }
&lt;b&gt;Теперь ваша подписка активна до { $new_date }&lt;/b&gt;"""]: ...


class UserButton:
    account: UserButtonAccount
    back: UserButtonBack
    input: UserButtonInput
    link: UserButtonLink
    subscription: UserButtonSubscription
    open: UserButtonOpen

    @staticmethod
    def subscribe() -> Literal["""📥 Подписка"""]: ...

    @staticmethod
    def support() -> Literal["""🛠 Поддержка"""]: ...

    @staticmethod
    def faq() -> Literal["""📣 О канале"""]: ...

    @staticmethod
    def kassasmart() -> Literal["""🟣 ЮКасса 🟣"""]: ...

    @staticmethod
    def yoomoney() -> Literal["""🟣 ЮMoney 🟣"""]: ...

    @staticmethod
    def cryptomus() -> Literal["""🔵 Cryptomus 🔵"""]: ...

    @staticmethod
    def cryptobot() -> Literal["""🔵 CryptoBot 🔵"""]: ...

    @staticmethod
    def lava() -> Literal["""🟠 Lava 🟠"""]: ...

    @staticmethod
    def stars() -> Literal["""🟡 Stars 🟡"""]: ...

    @staticmethod
    def no_payment() -> Literal["""Отсутствуют платежные системы"""]: ...


class UserButtonAccount:
    @staticmethod
    def __call__() -> Literal["""💼 Профиль"""]: ...

    @staticmethod
    def payment() -> Literal["""🕗 Мои платежи"""]: ...


class UserButtonBack:
    @staticmethod
    def __call__() -> Literal["""◀️ Вернутся"""]: ...

    @staticmethod
    def general() -> Literal["""⏬ Главное меню"""]: ...


class UserButtonInput:
    @staticmethod
    def support() -> Literal["""💬 Написать в поддержку"""]: ...


class UserButtonLink:
    @staticmethod
    def faq() -> Literal["""📄 Часто задаваемые вопросы"""]: ...


class UserButtonSubscription:
    pay: UserButtonSubscriptionPay

    @staticmethod
    def link() -> Literal["""📄 Инструкция по подключению"""]: ...

    @staticmethod
    def month(*, count, period, amount) -> Literal["""📆 { $count } { $period } - { $amount } ₽"""]: ...


class UserButtonSubscriptionPay:
    @staticmethod
    def __call__() -> Literal["""💳 Оплатить доступ"""]: ...

    @staticmethod
    def friend() -> Literal["""🎁 Подарить подписку"""]: ...


class UserButtonOpen:
    channel: UserButtonOpenChannel


class UserButtonOpenChannel:
    @staticmethod
    def __call__() -> Literal["""Открыть канал 📣"""]: ...

    @staticmethod
    def v2() -> Literal["""Доступ к каналу 📣"""]: ...


class UserLink:
    support: UserLinkSupport

    @staticmethod
    def subscription() -> Literal["""https://telegra.ph/Instrukciya-po-podklyucheniyu-09-06"""]: ...


class UserLinkSupport:
    @staticmethod
    def faq() -> Literal["""https://telegra.ph/CHasto-zadavaemye-voprosy-09-05-7"""]: ...


class Admin:
    text: AdminText
    error: AdminError
    button: AdminButton


class AdminText:
    support: AdminTextSupport
    admin_menu: AdminTextAdmin_menu
    message: AdminTextMessage
    account: AdminTextAccount


class AdminTextSupport:
    reply: AdminTextSupportReply

    @staticmethod
    def __call__(*, full_name, user_id) -> Literal["""Пользователь { $full_name } - ID &lt;code&gt;{ $user_id }&lt;/code&gt; написал обращение 👇"""]: ...


class AdminTextSupportReply:
    @staticmethod
    def __call__() -> Literal["""Напишите сообщение, которое увидит пользователь"""]: ...

    @staticmethod
    def all(*, admin_name, user_id) -> Literal["""Ответ { $admin_name } пользователю { $user_id }"""]: ...


class AdminError:
    unban: AdminErrorUnban

    @staticmethod
    def user_not_found() -> Literal["""Ошибка! Пользователь не найден"""]: ...


class AdminErrorUnban:
    @staticmethod
    def user(*, id_user) -> Literal["""Не вышло разбанить пользователся { $id_user }"""]: ...


class AdminTextAdmin_menu:
    milling: AdminTextAdmin_menuMilling
    statistic: AdminTextAdmin_menuStatistic
    user_control: AdminTextAdmin_menuUser_control

    @staticmethod
    def __call__() -> Literal["""🃏 Управление ботом 🦾"""]: ...

    @staticmethod
    def group_milling() -> Literal["""Кому отправить сообщение?"""]: ...


class AdminTextAdmin_menuMilling:
    @staticmethod
    def __call__() -> Literal["""Отправьте сообщение которое увидять пользователи"""]: ...

    @staticmethod
    def wait(*, percent) -> Literal["""Статуст выполния рассылики { $percent }%"""]: ...

    @staticmethod
    def result(*, all_count, suc_count, not_suc_count) -> Literal["""Рассылка выполнена ✅
Всего отправлено: { $all_count }
Получено: { $suc_count }
Недошло: { $not_suc_count }"""]: ...


class AdminTextAdmin_menuStatistic:
    payment: AdminTextAdmin_menuStatisticPayment
    all_users: AdminTextAdmin_menuStatisticAll_users
    active: AdminTextAdmin_menuStatisticActive

    @staticmethod
    def __call__() -> Literal["""Статистика бота 🤖"""]: ...


class AdminTextAdmin_menuStatisticPayment:
    caption: AdminTextAdmin_menuStatisticPaymentCaption

    @staticmethod
    def __call__(*, number, user_name, user_id, payment_system, amount, date) -> Literal["""{ $number }) Пользователь: { $user_name }({ $user_id }) - Платежная система: { $payment_system } - Сумма { $amount }₽ | Дата: { $date }"""]: ...

    @staticmethod
    def not_caption() -> Literal["""Поступлений нет"""]: ...


class AdminTextAdmin_menuStatisticPaymentCaption:
    @staticmethod
    def __call__() -> Literal["""Список поступлений"""]: ...

    @staticmethod
    def user() -> Literal["""Платежи пользователя"""]: ...


class AdminTextAdmin_menuStatisticAll_users:
    @staticmethod
    def __call__(*, number, fullname, username, telegram_id, lang, date, subscription) -> Literal["""{ $number }) { $fullname } - ({ $username }|{ $telegram_id }) - (Язык в TG:{ $lang }) Дата регистрации: { $date } Подписка: { $subscription }"""]: ...

    @staticmethod
    def caption() -> Literal["""Список всех пользователей"""]: ...

    @staticmethod
    def not_caption() -> Literal["""Пользователи отсутствуют"""]: ...


class AdminTextAdmin_menuStatisticActive:
    @staticmethod
    def caption() -> Literal["""Список всех пользователей с подпиской"""]: ...


class AdminTextAdmin_menuUser_control:
    account: AdminTextAdmin_menuUser_controlAccount

    @staticmethod
    def input(*, users) -> Literal["""Введите ID Telegram пользователя 👤
&lt;b&gt;(Вы можете посмотеть его в статистике)&lt;/b&gt;

👥 Последние пользователи бота:
{ $users }"""]: ...

    @staticmethod
    def not_user() -> Literal["""🚫 Пользователь не найден, введите заново"""]: ...


class AdminTextAdmin_menuUser_controlAccount:
    ban: AdminTextAdmin_menuUser_controlAccountBan
    un_ban: AdminTextAdmin_menuUser_controlAccountUn_ban

    @staticmethod
    def __call__(*, full_name, username, subscription, blocked, lang) -> Literal["""👤 Пользователь { $full_name } - { $username }
📆 Подписка: { $subscription }
🔸 Статус: { $blocked }
🈸 Язык в Telegram: { $lang }"""]: ...

    @staticmethod
    def sub(*, date) -> Literal["""активна до { $date } ✅"""]: ...

    @staticmethod
    def no_sub() -> Literal["""Отсутствует ❌"""]: ...

    @staticmethod
    def input_message_text(*, full_name, username) -> Literal["""Напишите сообщение для пользователя { $full_name } { $username }"""]: ...

    @staticmethod
    def message_admin() -> Literal["""Вам написал администратор ⬇️"""]: ...

    @staticmethod
    def add_time() -> Literal["""Выберете до какого числа у пользователя будет активна подписка
Подписка будет активна до 23:59 выбранного дня
Если вы выберете старое число, подписка будет сброшена"""]: ...


class AdminTextAdmin_menuUser_controlAccountBan:
    @staticmethod
    def __call__() -> Literal["""Заблокирован 🔒"""]: ...

    @staticmethod
    def alert() -> Literal["""Пользователь заблокирован"""]: ...


class AdminTextAdmin_menuUser_controlAccountUn_ban:
    @staticmethod
    def __call__() -> Literal["""Разблокирован ✅"""]: ...

    @staticmethod
    def alert() -> Literal["""Пользователь разблокирован"""]: ...


class AdminTextMessage:
    @staticmethod
    def success() -> Literal["""Пользователь получил ваше сообщение ✅"""]: ...


class AdminTextAccount:
    add_time: AdminTextAccountAdd_time


class AdminTextAccountAdd_time:
    reset: AdminTextAccountAdd_timeReset
    new: AdminTextAccountAdd_timeNew


class AdminTextAccountAdd_timeReset:
    @staticmethod
    def time(*, full_name) -> Literal["""Пользователю { $full_name } сброшено время подписки"""]: ...


class AdminTextAccountAdd_timeNew:
    @staticmethod
    def time(*, full_name, new_date) -> Literal["""Пользователю { $full_name } изменено время подписки на { $new_date }"""]: ...


class AdminButton:
    reply: AdminButtonReply
    milling: AdminButtonMilling
    user_control: AdminButtonUser_control

    @staticmethod
    def menu() -> Literal["""Админ панель 🚀"""]: ...

    @staticmethod
    def statistic() -> Literal["""📊 Статистика"""]: ...

    @staticmethod
    def payments() -> Literal["""🏦 Платежи"""]: ...

    @staticmethod
    def all_users() -> Literal["""📚 Все пользователи"""]: ...

    @staticmethod
    def active_users() -> Literal["""📗 Активные пользователи"""]: ...


class AdminButtonReply:
    @staticmethod
    def message() -> Literal["""💬 Ответить клиенту"""]: ...


class AdminButtonMilling:
    @staticmethod
    def __call__() -> Literal["""📢 Рассылка"""]: ...

    @staticmethod
    def all() -> Literal["""📒 Всем"""]: ...

    @staticmethod
    def sub() -> Literal["""📗 Только с подпиской"""]: ...

    @staticmethod
    def not_sub() -> Literal["""📕 Только без подписки"""]: ...


class AdminButtonUser_control:
    @staticmethod
    def __call__() -> Literal["""💻 Управление пользователями"""]: ...

    @staticmethod
    def ban() -> Literal["""💢 Заблокировать"""]: ...

    @staticmethod
    def unban() -> Literal["""❇️ Разблокировать"""]: ...

    @staticmethod
    def message() -> Literal["""📨 Написать клиенту"""]: ...

    @staticmethod
    def add_time() -> Literal["""📆 Изменить время подписки"""]: ...

    @staticmethod
    def payments() -> Literal["""💳 Платежи пользователя"""]: ...

