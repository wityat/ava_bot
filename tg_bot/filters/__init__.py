from tg_bot import dp

filters = ()
for aiogram_filter in filters:
    dp.message.bind_filter(aiogram_filter)
    dp.callback_query.bind_filter(aiogram_filter)
    dp.inline_query.bind_filter(aiogram_filter)
