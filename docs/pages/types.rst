Типы данных
===========

Все типы определены в модуле ``vk_bot.types`` и основаны на Pydantic.
Они автоматически создаются при получении событий - вам не нужно
конструировать их вручную (за исключением клавиатур).


Message
-------

Объект входящего сообщения - основной тип, с которым работает обработчик.

.. code-block:: python

    @bot.message_handler()
    def handle(message: types.Message):
        print(message.text)       # Текст сообщения
        print(message.from_id)    # ID отправителя
        print(message.peer_id)    # ID чата
        print(message.date)       # Дата (datetime)
        print(message.chat)       # Объект Chat
        print(message.is_private) # True если личное сообщение

Основные поля:

==================  ====================================  ===========================
Поле                Тип                                   Описание
==================  ====================================  ===========================
``id``              ``int``                               ID сообщения
``date``            ``datetime``                          Время отправки
``peer_id``         ``int``                               ID чата
``from_id``         ``int``                               ID отправителя
``text``            ``str``                               Текст сообщения
``out``             ``bool``                              ``True`` - исходящее
``attachments``     ``list[dict]``                        Вложения (сырые данные)
``reply_message``   ``Message | None``                    Ответ на сообщение
``fwd_messages``    ``list[Message]``                     Пересланные сообщения
``payload``         ``dict | None``                       Payload от кнопки
``action``          ``dict | None``                       Действие (приглашение и т.д.)
==================  ====================================  ===========================

Полезные свойства и методы:

.. code-block:: python

    message.chat           # Объект Chat (создаётся из peer_id)
    message.chat.type      # "private" или "group"
    message.content_type   # "text", "photo", "doc", "video", и т.д.
    message.is_private     # True если peer_id == from_id

    message.get_photos()     # list[Photo] - извлечь фото из вложений
    message.get_documents()  # list[Document] - извлечь документы


User
----

Объект пользователя VK.

.. code-block:: python

    user = message.from_user  # Может быть None

    user.id            # 123456
    user.first_name    # "Иван"
    user.last_name     # "Петров"
    user.full_name     # "Иван Петров"
    user.mention        # "[id123456|Иван]"
    user.photo_100     # URL фотографии
    user.online        # True/False


Chat
----

Объект чата (личное сообщение или беседа).

.. code-block:: python

    chat = message.chat

    chat.id      # ID чата
    chat.type    # "private" или "group"
    chat.title   # Название беседы (None для личных)

Создание из ``peer_id``:

.. code-block:: python

    # peer_id < 2_000_000_000 → private, иначе → group
    chat = types.Chat.from_peer_id(12345)


CallbackQuery
-------------

Событие нажатия на inline-кнопку.

.. code-block:: python

    @bot.callback_query_handler(data="action")
    def handle(callback: types.CallbackQuery):
        callback.id         # ID события
        callback.from_id    # ID пользователя
        callback.peer_id    # ID чата
        callback.message_id # ID сообщения с кнопкой
        callback.data       # Значение callback_data кнопки


Update
------

Обёртка над событием Long Poll. Обычно используется в middleware:

.. code-block:: python

    @bot.middleware_handler()
    def log(bot_instance, update: types.Update):
        print(update.type)            # "message_new", "message_event", и т.д.
        print(update.message)         # Message | None
        print(update.callback_query)  # CallbackQuery | None


Клавиатуры
----------

Клавиатуры - единственные типы, которые вы создаёте вручную.

Reply-клавиатура (обычные кнопки)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Отображается под полем ввода. Нажатие отправляет текст кнопки как обычное сообщение.

.. code-block:: python

    kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    kb.add(
        types.KeyboardButton(text="Да", color="positive"),
        types.KeyboardButton(text="Нет", color="negative"),
    )
    bot.send_message(chat_id, "Вы согласны?", reply_markup=kb)

Метод ``add()`` добавляет **строку** кнопок. Для нескольких строк вызовите
``add()`` несколько раз:

.. code-block:: python

    kb = types.ReplyKeyboardMarkup()
    kb.add(types.KeyboardButton(text="Строка 1, Кнопка 1"))
    kb.add(
        types.KeyboardButton(text="Строка 2, Кнопка 1"),
        types.KeyboardButton(text="Строка 2, Кнопка 2"),
    )

Цвета кнопок:

===============  ===========================================
Значение         Описание
===============  ===========================================
``"primary"``    Синяя кнопка (по умолчанию)
``"secondary"``  Белая/серая кнопка
``"positive"``   Зелёная кнопка
``"negative"``   Красная кнопка
===============  ===========================================

Чтобы **скрыть** клавиатуру, отправьте пустую:

.. code-block:: python

    empty = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    bot.send_message(chat_id, "Клавиатура скрыта", reply_markup=empty)

Inline-клавиатура (кнопки в сообщении)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Встраивается прямо в сообщение. Нажатие отправляет callback-событие.

.. code-block:: python

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="Да", callback_data="like"),
        types.InlineKeyboardButton(text="Нет", callback_data="dislike"),
    )
    kb.add(
        types.InlineKeyboardButton(text="Открыть сайт", url="https://vk.com"),
    )
    bot.send_message(chat_id, "Оцените:", reply_markup=kb)

Параметры ``InlineKeyboardButton``:

=====================  ======================================
Параметр               Описание
=====================  ======================================
``text``               Текст кнопки (обязательный)
``callback_data``      Данные для callback-обработчика
``url``                Ссылка для открытия в браузере
``vk_app_id``          ID VK Mini App
``owner_id``           Владелец VK Mini App
``hash``               Хеш для VK Mini App
=====================  ======================================

.. note::

   Укажите **один** из параметров: ``callback_data``, ``url`` или ``vk_app_id``.


Вложения (Attachment)
---------------------

Типы вложений для работы с медиа:

Photo
~~~~~

.. code-block:: python

    photos = message.get_photos()
    for photo in photos:
        print(photo.id)         # ID фото
        print(photo.owner_id)   # ID владельца
        print(photo.url)        # URL наибольшего размера
        print(photo.attachment)  # "photo-123_456_key"

Document
~~~~~~~~

.. code-block:: python

    docs = message.get_documents()
    for doc in docs:
        print(doc.id)         # ID документа
        print(doc.title)      # Имя файла
        print(doc.ext)        # Расширение ("pdf", "zip", ...)
        print(doc.size)       # Размер в байтах
        print(doc.url)        # URL для скачивания
        print(doc.attachment)  # "doc-123_456_key"

Video
~~~~~

.. code-block:: python

    video.id          # ID видео
    video.owner_id    # ID владельца
    video.title       # Название
    video.duration    # Длительность в секундах
    video.attachment  # "video-123_456_key"

Audio
~~~~~

.. code-block:: python

    audio.id       # ID аудио
    audio.artist   # Исполнитель
    audio.title    # Название
    audio.duration # Длительность
    audio.url      # URL потока
    audio.attachment  # "audio-123_456"
