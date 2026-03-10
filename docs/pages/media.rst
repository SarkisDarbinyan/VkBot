Отправка медиа
==============

``vk-bot`` поддерживает отправку фотографий и документов с автоматической
загрузкой на серверы VK.


Отправка фотографий
--------------------

Метод ``send_photo`` принимает файл, загружает его через VK API
и отправляет как вложение к сообщению.

Из файла на диске
~~~~~~~~~~~~~~~~~

.. code-block:: python

    bot.send_photo(chat_id, photo="path/to/image.jpg")

Из байтов
~~~~~~~~~

.. code-block:: python

    with open("image.png", "rb") as f:
        image_bytes = f.read()

    bot.send_photo(chat_id, photo=image_bytes, caption="Мое фото")

Из файлового объекта
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    with open("photo.jpg", "rb") as f:
        bot.send_photo(chat_id, photo=f, caption="Фото из файла")

С клавиатурой
~~~~~~~~~~~~~

.. code-block:: python

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Нравится", callback_data="like"))

    bot.send_photo(
        chat_id,
        photo="photo.jpg",
        caption="Нравится?",
        reply_markup=kb,
    )


Отправка документов
-------------------

Метод ``send_document`` работает аналогично ``send_photo``,
но загружает файл как документ.

.. code-block:: python

    # Из пути к файлу
    bot.send_document(chat_id, document="report.pdf")

    # Из байтов
    bot.send_document(chat_id, document=pdf_bytes, caption="Отчёт")

    # Из файлового объекта
    with open("archive.zip", "rb") as f:
        bot.send_document(chat_id, document=f, caption="Архив")


Ответ на сообщение
------------------

Метод ``reply_to`` автоматически подставляет ``chat_id`` и ``reply_to``
из исходного сообщения:

.. code-block:: python

    @bot.message_handler(commands=["ping"])
    def handle_ping(message: types.Message):
        bot.reply_to(message, "pong!")


Работа с вложениями входящих сообщений
--------------------------------------

Извлечение фотографий и документов из полученного сообщения:

.. code-block:: python

    @bot.message_handler(content_types=["photo"])
    def handle_photo(message: types.Message):
        photos = message.get_photos()
        for photo in photos:
            print(f"URL: {photo.url}")
            print(f"Attachment: {photo.attachment}")

    @bot.message_handler(content_types=["doc"])
    def handle_doc(message: types.Message):
        docs = message.get_documents()
        for doc in docs:
            print(f"{doc.title}.{doc.ext} ({doc.size} байт)")
            print(f"Скачать: {doc.url}")


Длинные сообщения
-----------------

VK ограничивает длину сообщения **4096 символами**.
Используйте ``split_text`` для автоматического разбиения:

.. code-block:: python

    from vk_bot import util

    long_text = "..." * 5000  # Очень длинный текст

    for part in util.split_text(long_text):
        bot.send_message(chat_id, part)
