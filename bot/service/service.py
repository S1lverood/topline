import io
import logging

from aiogram.types import Message, BufferedInputFile

from bot.misc import Config


async def check_admin(id_user):
    return id_user in Config.ADMINS_ID



async def send_admin(message: Message,  text=None, reply_markup=None) -> bool:
    result = False
    for admin in Config.ADMINS_ID:
        try:
            if text is None:
                await message.send_copy(admin, reply_markup=reply_markup)
            else:
                await message.bot.send_message(
                    admin, reply_markup=reply_markup, text=text
                )
            result = True
        except Exception as e:
            logging.error(e)
            continue
    return result


async def send_document(message: Message, text, name_document, caption):
    file_stream = io.BytesIO(text.encode()).getvalue()
    input_file = BufferedInputFile(file_stream, f'{name_document}.txt')
    try:
        await message.answer_document(
            input_file,
            caption=caption
        )
        return True
    except Exception as e:
        logging.error(e, f'error send file {name_document}.txt')
        return False


async def check_number_int(message: Message, i18n, text):
    if text.isdigit():
        return int(text)
    else:
        await message.answer(i18n.user.text.error.input.number())
        raise ValueError('input not number text')
