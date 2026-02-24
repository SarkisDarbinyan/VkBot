from __future__ import annotations
from vk_bot import VKBot
from vk_bot.types import Message

def test_command_filter(bot: VKBot, message_update_factory) -> None:
    results = []

    @bot.message_handler(commands=['start', 'help'])
    def handle_commands(message: Message):
        results.append(message.text)

    bot._process_update(message_update_factory(text='/start'))
    bot._process_update(message_update_factory(text='/help info'))
    bot._process_update(message_update_factory(text='normal text'))

    assert results == ['/start', '/help info']

def test_regexp_filter(bot: VKBot, message_update_factory) -> None:
    results = []

    @bot.message_handler(regexp=r'Order: (\d+)')
    def handle_regexp(message: Message):
        results.append(message.text)

    bot._process_update(message_update_factory(text='Order: 12345'))
    bot._process_update(message_update_factory(text='Just a message'))

    assert results == ['Order: 12345']

def test_func_filter(bot: VKBot, message_update_factory) -> None:
    results = []

    @bot.message_handler(func=lambda msg: msg.text == 'Secret')
    def handle_func(message: Message):
        results.append('found')

    bot._process_update(message_update_factory(text='Secret'))
    bot._process_update(message_update_factory(text='Not secret'))

    assert results == ['found']

def test_content_types_filter(bot: VKBot, message_update_factory) -> None:
    text_results = []
    photo_results = []

    @bot.message_handler(content_types=['text'])
    def handle_text(message: Message):
        text_results.append(message.text)

    @bot.message_handler(content_types=['photo'])
    def handle_photo(message: Message):
        photo_results.append('photo_received')

    bot._process_update(message_update_factory(text='just text'))
    
    photo_update = message_update_factory(text='', content={'attachments': [{'type': 'photo'}]})
    bot._process_update(photo_update)

    assert text_results == ['just text']
    assert photo_results == ['photo_received']

def test_chat_types_filter(bot: VKBot, message_update_factory) -> None:
    private_results = []
    group_results = []

    @bot.message_handler(chat_types=['private'])
    def handle_private(message: Message):
        private_results.append(message.peer_id)

    @bot.message_handler(chat_types=['group'])
    def handle_group(message: Message):
        group_results.append(message.peer_id)

    bot._process_update(message_update_factory(user_id=111222333, peer_id=111222333))
    bot._process_update(message_update_factory(user_id=111222333, peer_id=2000000001))

    assert private_results == [111222333]
    assert group_results == [2000000001]

def test_middleware_blocking(bot: VKBot, message_update_factory) -> None:
    results = []

    @bot.middleware_handler()
    def my_middleware(bot_instance, update):
        if update.message and 'spam' in (update.message.text or ''):
            return False
        return True

    @bot.message_handler()
    def handle_any(message):
        results.append(message.text)

    bot._process_update(message_update_factory(text='hello'))
    bot._process_update(message_update_factory(text='this is spam message'))

    assert results == ['hello']
