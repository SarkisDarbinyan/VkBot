from vk_bot import VKBot

bot = VKBot("GROUP_TOKEN")


@bot.message_handler()
def send_echo(message):
    bot.send_message(message.from_id, message.text)


bot.polling()
