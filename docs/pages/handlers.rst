Обработчики и фильтры
=====================

``vk-bot`` предоставляет декораторы для обработки различных событий:
сообщений, нажатий на inline-кнопки и middleware-прослоек.
Каждый декоратор принимает набор **фильтров**, определяющих, какие события
будет обрабатывать функция.

Обработчики сообщений
---------------------

Декоратор ``@bot.message_handler()`` регистрирует функцию для обработки
входящих сообщений. Без фильтров обработчик срабатывает на **все** сообщения.

.. code-block:: python

    @bot.message_handler()
    def handle_all(message: types.Message):
        bot.send_message(message.from_id, f"Получено: {message.text}")

.. important::

   Обработчики проверяются **по порядку** регистрации.
   Первый подходящий обработчик выполняется, остальные - пропускаются.
   Поэтому более специфичные обработчики следует регистрировать **раньше** общих.

Фильтр ``commands``
~~~~~~~~~~~~~~~~~~~

Реагирует на команды вида ``/start``, ``/help``, и т.д.
Слэш в начале **не указывается**:

.. code-block:: python

    @bot.message_handler(commands=["start", "help"])
    def handle_commands(message: types.Message):
        bot.send_message(message.from_id, "Добро пожаловать!")

Чтобы получить аргументы команды, используйте утилиту ``extract_command``:

.. code-block:: python

    from vk_bot.handlers import extract_command

    @bot.message_handler(commands=["echo"])
    def handle_echo(message: types.Message):
        cmd, args = extract_command(message.text)
        bot.send_message(message.from_id, args or "Нет аргументов")

    # Сообщение "/echo привет мир" → args = "привет мир"

Фильтр ``regexp``
~~~~~~~~~~~~~~~~~

Срабатывает при совпадении текста сообщения с регулярным выражением:

.. code-block:: python

    @bot.message_handler(regexp=r"привет|здравствуй")
    def handle_greeting(message: types.Message):
        bot.send_message(message.from_id, "Привет!")

Фильтр ``func``
~~~~~~~~~~~~~~~~

Произвольная функция-предикат, принимающая ``Message`` и возвращающая ``bool``:

.. code-block:: python

    @bot.message_handler(func=lambda m: m.text and m.text.startswith("!"))
    def handle_exclamation(message: types.Message):
        bot.send_message(message.from_id, "Обнаружена команда с '!'")

    # Пример с именованной функцией
    def is_admin(message: types.Message) -> bool:
        return message.from_id in [123456, 789012]

    @bot.message_handler(func=is_admin)
    def handle_admin(message: types.Message):
        bot.send_message(message.from_id, "Вы администратор")

Фильтр ``content_types``
~~~~~~~~~~~~~~~~~~~~~~~~~

Фильтрация по типу содержимого сообщения:

.. code-block:: python

    @bot.message_handler(content_types=["photo"])
    def handle_photo(message: types.Message):
        photos = message.get_photos()
        bot.send_message(message.from_id, f"Получено {len(photos)} фото")

    @bot.message_handler(content_types=["doc"])
    def handle_doc(message: types.Message):
        docs = message.get_documents()
        bot.send_message(message.from_id, f"Документ: {docs[0].title}")

Доступные типы содержимого:

- ``text`` - текстовое сообщение
- ``photo`` - фотография
- ``doc`` - документ
- ``video`` - видео
- ``audio`` - аудио
- ``sticker`` - стикер
- ``wall`` - запись со стены

Фильтр ``chat_types``
~~~~~~~~~~~~~~~~~~~~~~

Ограничивает обработчик определёнными типами чатов:

.. code-block:: python

    @bot.message_handler(chat_types=["private"])
    def handle_private(message: types.Message):
        bot.send_message(message.from_id, "Это личное сообщение")

    @bot.message_handler(chat_types=["group"])
    def handle_group(message: types.Message):
        bot.send_message(message.peer_id, "Сообщение из беседы")

Фильтр ``state``
~~~~~~~~~~~~~~~~~

Срабатывает только когда пользователь находится в определённом состоянии FSM:

.. code-block:: python

    from vk_bot.state.group import StatesGroup
    from vk_bot.state.manager import State

    class Form(StatesGroup):
        waiting_name = State()
        waiting_age = State()

    @bot.message_handler(state=Form.waiting_name)
    def handle_name(message: types.Message, state: StateContext):
        state.update(name=message.text)
        state.set(Form.waiting_age)
        bot.send_message(message.from_id, "Сколько вам лет?")

.. tip::

   Когда обработчик принимает второй аргумент ``state: StateContext``,
   библиотека автоматически передаёт контекст состояния пользователя.

Можно указать несколько состояний списком:

.. code-block:: python

    @bot.message_handler(state=[Form.waiting_name, Form.waiting_age])
    def handle_any_form_step(message: types.Message, state: StateContext):
        ...

Комбинирование фильтров
~~~~~~~~~~~~~~~~~~~~~~~~

Фильтры комбинируются через логическое **И** - все условия должны совпасть:

.. code-block:: python

    @bot.message_handler(
        content_types=["text"],
        chat_types=["private"],
        func=lambda m: len(m.text or "") > 10,
    )
    def handle_long_private_text(message: types.Message):
        bot.send_message(message.from_id, "Длинное сообщение!")


Обработчики callback-запросов
-----------------------------

Декоратор ``@bot.callback_query_handler()`` обрабатывает нажатия на
inline-кнопки:

.. code-block:: python

    @bot.callback_query_handler(data="confirm")
    def handle_confirm(callback: types.CallbackQuery):
        bot.answer_callback_query(
            callback_query_id=callback.id,
            user_id=callback.from_id,
            peer_id=callback.peer_id,
            text="Подтверждено!",
        )

Фильтр ``data``
~~~~~~~~~~~~~~~~

Может быть строкой (точное совпадение) или регулярным выражением:

.. code-block:: python

    import re

    # Точное совпадение
    @bot.callback_query_handler(data="btn_like")
    def on_like(callback: types.CallbackQuery):
        ...

    # Регулярное выражение
    @bot.callback_query_handler(data=re.compile(r"^page_\d+$"))
    def on_page(callback: types.CallbackQuery):
        page = callback.data.split("_")[1]
        ...

Фильтр ``func``
~~~~~~~~~~~~~~~~

Произвольная функция-предикат:

.. code-block:: python

    @bot.callback_query_handler(func=lambda cb: cb.from_id == 12345)
    def on_admin_callback(callback: types.CallbackQuery):
        ...

Фильтр ``state``
~~~~~~~~~~~~~~~~~

Аналогичен фильтру состояния для сообщений:

.. code-block:: python

    @bot.callback_query_handler(data="next_step", state=Form.waiting_confirm)
    def on_confirm(callback: types.CallbackQuery, state: StateContext):
        state.finish()
        bot.answer_callback_query(
            callback.id, callback.from_id, callback.peer_id,
            text="Готово!",
        )


Middleware
----------

Middleware - функции, которые выполняются **до** обработчиков.
Если middleware возвращает ``False``, обработка события прекращается.

.. code-block:: python

    @bot.middleware_handler()
    def log_all_events(bot_instance, update: types.Update):
        print(f"Событие: {update.type}")
        # Не возвращаем False - обработка продолжится

    @bot.middleware_handler(update_types=["message_new"])
    def check_ban_list(bot_instance, update: types.Update):
        if update.message and update.message.from_id in BANNED_USERS:
            return False  # Блокируем обработку

Параметр ``update_types``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ограничивает middleware определёнными типами событий.
Если не указан - middleware срабатывает на **все** события:

.. code-block:: python

    @bot.middleware_handler(update_types=["message_new", "message_event"])
    def only_messages(bot_instance, update: types.Update):
        print("Только сообщения и callback-события")


Вспомогательные функции
-----------------------

Модуль ``vk_bot.handlers`` предоставляет утилиты для работы с текстом сообщений:

.. code-block:: python

    from vk_bot.handlers import extract_command, extract_mentions, is_group_event

    # Парсинг команд
    cmd, args = extract_command("/start hello world")
    # cmd = "start", args = "hello world"

    cmd, args = extract_command("просто текст")
    # cmd = None, args = None

    # Извлечение упоминаний
    user_ids = extract_mentions("Привет [id123|Иван] и @id456")
    # user_ids = [123, 456]

    # Проверка группового события
    is_group_event("group_join")   # True
    is_group_event("message_new")  # False
