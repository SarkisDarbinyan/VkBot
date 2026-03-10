.. Главный файл документации vk-bot

vk-bot
======

Библиотека для создания ботов ВКонтакте на Python.

**Возможности:**

- Декораторы ``@message_handler``, ``@callback_query_handler`` с гибкими фильтрами
- FSM (конечный автомат) для многошаговых сценариев
- Три хранилища состояний: Memory, Redis, PostgreSQL
- Reply и Inline-клавиатуры
- Загрузка и отправка фото и документов
- Автоматические ретраи с экспоненциальной задержкой
- Полная типизация (mypy, PEP 561)

.. code-block:: python

   from vk_bot import VKBot, types

   bot = VKBot(token="YOUR_TOKEN")

   @bot.message_handler(commands=["start"])
   def handle_start(message: types.Message):
       bot.send_message(message.from_id, "Привет!")

   bot.polling()

.. toctree::
   :maxdepth: 2
   :caption: Руководство

   pages/quickstart.rst
   pages/handlers.rst
   pages/types.rst
   pages/media.rst
   pages/fsm.rst
   pages/configuration.rst
   pages/utilities.rst

.. toctree::
   :maxdepth: 1
   :caption: Справочник

   pages/api_reference.rst
   pages/changelog.rst

Индексы и таблицы
-----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
