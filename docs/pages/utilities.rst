Утилиты
=======

Вспомогательные функции для повседневных задач при разработке бота.


Модуль ``vk_bot.util``
-----------------------

split_text
~~~~~~~~~~

Разбивает длинный текст на части, не превышающие лимит VK (4096 символов).
Разбиение происходит по строкам и словам - слова не разрываются.

.. code-block:: python

    from vk_bot import util

    parts = util.split_text(very_long_text)
    for part in parts:
        bot.send_message(chat_id, part)

    # С кастомным лимитом
    parts = util.split_text(text, max_length=2000)

create_link
~~~~~~~~~~~

Создаёт ссылку в формате VK: ``[url|текст]``.

.. code-block:: python

    from vk_bot import util

    link = util.create_link("Наш сайт", "https://example.com")
    # "[https://example.com|Наш сайт]"

    bot.send_message(chat_id, f"Посетите {link}")

format_time
~~~~~~~~~~~

Форматирует Unix-timestamp в читаемую строку ``ДД.ММ.ГГГГ ЧЧ:ММ``.

.. code-block:: python

    from vk_bot import util

    readable = util.format_time(1709042400)
    # "27.02.2024 12:00"


Модуль ``vk_bot.handlers``
---------------------------

extract_command
~~~~~~~~~~~~~~~

Извлекает команду и аргументы из текста сообщения.

.. code-block:: python

    from vk_bot.handlers import extract_command

    cmd, args = extract_command("/start привет мир")
    # cmd = "start", args = "привет мир"

    cmd, args = extract_command("/help")
    # cmd = "help", args = None

    cmd, args = extract_command("обычный текст")
    # cmd = None, args = None

extract_mentions
~~~~~~~~~~~~~~~~

Извлекает ID упомянутых пользователей из текста.
Поддерживает форматы ``[id123|Имя]`` и ``@id123``.

.. code-block:: python

    from vk_bot.handlers import extract_mentions

    ids = extract_mentions("Привет [id123|Иван] и @id456!")
    # ids = [123, 456]

    ids = extract_mentions("Без упоминаний")
    # ids = []

is_group_event
~~~~~~~~~~~~~~

Проверяет, является ли тип события групповым.

.. code-block:: python

    from vk_bot.handlers import is_group_event

    is_group_event("group_join")    # True
    is_group_event("group_leave")   # True
    is_group_event("message_new")   # False
