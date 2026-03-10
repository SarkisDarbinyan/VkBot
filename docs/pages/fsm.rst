Конечный автомат состояний (FSM)
================================

Менеджер состояний (FSM) в ``vk-bot`` позволяет реализовывать многошаговые сценарии
(формы, опросы, онбординг), закрепляя *текущее состояние* за каждым пользователем.
Данные состояний могут храниться в оперативной памяти (in-memory), Redis или PostgreSQL.

Основная концепция
------------------

- :class:`~vk_bot.state.fsm.VKBotFSM` - **граф переходов без состояния**. Общий для всех пользователей.
- :class:`~vk_bot.state.manager.StateManager` - сохраняет состояние каждого пользователя в хранилище.
- :class:`~vk_bot.state.context.StateContext` - интерфейс для обработчиков: ``state.set()``, ``state.data``, ``state.finish()``.

Объявление состояний
--------------------

.. code-block:: python

    from vk_bot import StatesGroup
    from vk_bot.state.manager import State

    class Form(StatesGroup):
        waiting_name = State()
        waiting_age  = State()

Использование состояний в обработчиках
--------------------------------------

.. code-block:: python

    from vk_bot import VKBot, types
    from vk_bot.state.context import StateContext

    bot = VKBot(token="...")

    @bot.message_handler(commands=["start"])
    def cmd_start(message: types.Message):
        bot.set_state(message.from_id, Form.waiting_name)
        bot.send_message(message.chat.id, "Как вас зовут?")

    @bot.message_handler(state=Form.waiting_name)
    def handle_name(message: types.Message, state: StateContext):
        state.update(name=message.text)
        state.set(Form.waiting_age)
        bot.send_message(message.chat.id, "Сколько вам лет?")

    @bot.message_handler(state=Form.waiting_age)
    def handle_age(message: types.Message, state: StateContext):
        data = state.data
        state.finish()
        bot.send_message(
            message.chat.id,
            f"Сохранено: {data['name']}, {message.text} лет.",
        )

Хранилища состояний
-------------------

**In-memory** (по умолчанию, без зависимостей):

.. code-block:: python

    bot = VKBot(token="...")

**Redis:**

.. code-block:: python

    from vk_bot import VKBot, RedisStorage

    bot = VKBot(token="...", state_storage=RedisStorage())

**PostgreSQL:**

.. code-block:: python

    from vk_bot import PostgresStorage

    bot = VKBot(
        token="...",
        state_storage=PostgresStorage("postgresql://user:pass@localhost/db"),
    )

Граф FSM с переходами
----------------------

Для строгого управления навигацией задайте явный граф FSM:

.. code-block:: python

    from vk_bot.state.fsm import VKBotFSM, FSMRegistry

    fsm = VKBotFSM("registration")
    fsm.set_initial("idle")
    fsm.add_state("waiting_name")
    fsm.add_state("waiting_age")
    fsm.add_transition("idle", "waiting_name")
    fsm.add_transition("waiting_name", "waiting_age")
    FSMRegistry.register("registration", fsm)

API StateContext
----------------

Подробная документация класса ``StateContext`` доступна в :doc:`api_reference`.

Основные методы:

- ``state.set(new_state)`` - перейти в новое состояние
- ``state.data`` - получить данные пользователя
- ``state.update(**kwargs)`` - обновить данные
- ``state.finish()`` - сбросить состояние и данные
- ``state["key"]`` - чтение/запись данных как в ``dict``
- ``state.is_state(state)`` - проверить текущее состояние
- ``state.is_in_group(group)`` - проверить принадлежность к группе
