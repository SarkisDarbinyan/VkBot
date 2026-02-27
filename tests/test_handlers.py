from __future__ import annotations

from vk_bot import VKBot


def test_no_handler(bot: VKBot, message_update_factory) -> None:
    bot._process_update(message_update_factory(text="no one listens"))


def test_message_handler_dispatch(bot: VKBot, message_update_factory) -> None:
    called: list[str] = []

    @bot.message_handler()
    def handle(message) -> None:
        called.append(message.text)

    bot._process_update(message_update_factory(text="hello"))
    assert called == ["hello"]


def test_callback_query_handler_with_data_filter(
    bot: VKBot,
    callback_update_factory,
) -> None:
    called: list[str] = []

    @bot.callback_query_handler(data=r"^confirm:")
    def handle(callback) -> None:
        called.append(callback.data)

    bot._process_update(callback_update_factory(data="confirm:yes"))
    bot._process_update(callback_update_factory(data="reject:no"))

    assert called == ["confirm:yes"]


def test_handler_priority_first_match(bot: VKBot, message_update_factory) -> None:
    called: list[str] = []

    @bot.message_handler(func=lambda m: m.text == "specific")
    def specific_handler(message):
        called.append("specific")

    @bot.message_handler()
    def catch_all_handler(message):
        called.append("general")

    bot._process_update(message_update_factory(text="specific"))
    assert called == ["specific"]

    called.clear()
    bot._process_update(message_update_factory(text="normal"))
    assert called == ["general"]
