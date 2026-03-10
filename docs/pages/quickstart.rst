Быстрый старт
=============

Установка
---------

.. code-block:: bash

    pip install vk-bot

Или через Poetry:

.. code-block:: bash

    poetry add vk-bot

Для поддержки Redis или PostgreSQL установите с дополнительными зависимостями:

.. code-block:: bash

    pip install "vk-bot[redis]"       # Хранилище состояний в Redis
    pip install "vk-bot[postgres]"    # Хранилище состояний в PostgreSQL

Получение токена
-----------------

1. Создайте сообщество ВКонтакте (или используйте существующее).
2. Перейдите в **Управление → Работа с API → Ключи доступа**.
3. Создайте ключ с правами на **сообщения сообщества**.
4. Включите **Long Poll API** в разделе **Управление → Работа с API → Long Poll API**.
5. Отметьте нужные события (минимум: ``message_new``, ``message_event``).

Первый бот
----------

Создайте файл ``bot.py``:

.. code-block:: python

    from vk_bot import VKBot, types

    bot = VKBot(token="YOUR_TOKEN")

    @bot.message_handler(commands=["start"])
    def handle_start(message: types.Message):
        bot.send_message(message.from_id, "Привет! Я бот ВКонтакте.")

    @bot.message_handler()
    def handle_echo(message: types.Message):
        bot.send_message(message.from_id, f"Вы написали: {message.text}")

    if __name__ == "__main__":
        bot.polling()

Запустите:

.. code-block:: bash

    python bot.py

.. tip::

   Рекомендуется хранить токен в переменной окружения:

   .. code-block:: python

       import os
       bot = VKBot(token=os.getenv("VK_TOKEN"))

Reply-клавиатуры (Обычные кнопки)
---------------------------------

Обычные кнопки отображаются под полем ввода.
Нажатие отправляет текст кнопки как сообщение.

.. code-block:: python

    from vk_bot import types

    kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    kb.add(
        types.KeyboardButton(text="Вариант А", color="primary"),
        types.KeyboardButton(text="Вариант Б", color="secondary"),
    )
    bot.send_message(chat_id, "Выберите вариант:", reply_markup=kb)

Обработка нажатия - обычный обработчик текста:

.. code-block:: python

    @bot.message_handler(func=lambda m: m.text == "Вариант А")
    def handle_option_a(message: types.Message):
        bot.send_message(message.from_id, "Вы выбрали А!")

Чтобы скрыть клавиатуру, отправьте пустую:

.. code-block:: python

    empty_kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    bot.send_message(chat_id, "Клавиатура скрыта", reply_markup=empty_kb)

Inline-клавиатуры
-----------------

Inline-кнопки встраиваются в сообщение.
Нажатие генерирует callback-событие.

.. code-block:: python

    from vk_bot import types

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="Подтвердить", callback_data="yes"),
        types.InlineKeyboardButton(text="Отменить", callback_data="no"),
    )
    bot.send_message(chat_id, "Вы уверены?", reply_markup=kb)

    @bot.callback_query_handler(data="yes")
    def handle_yes(callback: types.CallbackQuery):
        bot.answer_callback_query(
            callback_query_id=callback.id,
            user_id=callback.from_id,
            peer_id=callback.peer_id,
            text="Подтверждено!",
        )

Что дальше?
-----------

- :doc:`handlers` - подробно о фильтрах и декораторах
- :doc:`types` - все типы данных
- :doc:`media` - отправка фото и документов
- :doc:`fsm` - многошаговые сценарии (формы, опросы)
- :doc:`configuration` - настройка HTTP, прокси, обработка ошибок
