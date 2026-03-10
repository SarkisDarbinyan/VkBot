Справочник API
==============

Автоматически сгенерированная документация из исходного кода.
Для руководств с примерами смотрите соответствующие разделы документации.

Класс VKBot
------------

Основной класс для создания и управления ботом.

.. autoclass:: vk_bot.VKBot
   :members:
   :undoc-members:
   :show-inheritance:

Типы данных
-----------

Pydantic-модели для объектов VK API: сообщения, пользователи, клавиатуры и вложения.

.. automodule:: vk_bot.types
   :members:
   :undoc-members:
   :show-inheritance:

Конечный автомат (FSM)
-----------------------

Граф переходов
~~~~~~~~~~~~~~

.. autoclass:: vk_bot.state.fsm.VKBotFSM
   :members:
   :undoc-members:

.. autoclass:: vk_bot.state.fsm.FSMRegistry
   :members:
   :undoc-members:

Группы состояний
~~~~~~~~~~~~~~~~

.. autoclass:: vk_bot.state.group.StatesGroup
   :members:
   :undoc-members:

.. autoclass:: vk_bot.state.manager.State
   :members:
   :undoc-members:

Контекст состояния
~~~~~~~~~~~~~~~~~~

.. autoclass:: vk_bot.state.context.StateContext
   :members:
   :undoc-members:

Хранилища состояний
-------------------

.. autoclass:: vk_bot.state.storage.BaseStorage
   :members:
   :undoc-members:

.. autoclass:: vk_bot.state.storage.MemoryStorage
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: vk_bot.state.storage.RedisStorage
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: vk_bot.state.storage.PostgresStorage
   :members:
   :undoc-members:
   :show-inheritance:

Конфигурация
------------

.. autoclass:: vk_bot.config.HttpConfig
   :members:
   :undoc-members:

Исключения
----------

.. autoclass:: vk_bot.exception.VKAPIError
   :members:
   :undoc-members:

Утилиты
-------

.. automodule:: vk_bot.util
   :members:
   :undoc-members:

Обработчики
-----------

.. autofunction:: vk_bot.handlers.extract_command

.. autofunction:: vk_bot.handlers.extract_mentions

.. autofunction:: vk_bot.handlers.is_group_event

