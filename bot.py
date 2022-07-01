from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.utils.markdown import hbold, hitalic, hspoiler
from aiogram.dispatcher.filters import Text

import os
import services

from typing import List

PAYMENT_TOKEN=os.getenv('PAYMENT_TOKEN')
ADMIN_ID=os.getenv('ADMIN_ID')
bot = Bot(token=os.getenv('BOT_TOKEN'), parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot=bot, storage=MemoryStorage())

def creation_markup(first_button_text, first_button_data):
    b1 = InlineKeyboardButton(text=first_button_text, callback_data=first_button_data)
    b2 = InlineKeyboardButton(text='Отмена', callback_data='cancel')

    return InlineKeyboardMarkup().add(b1, b2)


class AddItem(StatesGroup):
    name = State()
    description = State()
    amount = State()
    price = State()
    photo = State()


class ChangeAmount(StatesGroup):
    id: int
    new_amount = State()

class NewName(StatesGroup):
    enter_new_name = State()


class NewAdress(StatesGroup):
    enter_new_adress = State()


def show_items_template() -> str|List[services.Item]:
    try:
        return services.Items().get_items
    except services.NoItems as error:
        return error


async def no_items_check(message: types.Message) -> List[services.Item]:
    try:
        items = services.Items().get_items()
        return items
    except services.NoItems as error:
        await message.answer(error)
        return


@dp.message_handler(user_id=ADMIN_ID, commands=['start', 'help'], )
async def start_admin(message: types.Message):
    await message.answer('Управление ботом олежа\nДобавить товар /add\nПолучить список товаров /items\n')


@dp.message_handler(user_id=ADMIN_ID, commands='add')
async def add(message: types.Message):
    await message.answer('Введите название товара')
    await AddItem.name.set()


@dp.message_handler(user_id=ADMIN_ID, state=AddItem.name)
async def item_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Придумайте описание')
    await AddItem.next()


@dp.message_handler(user_id=ADMIN_ID, state=AddItem.description)
async def item_descript(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['descript'] = message.text
    await message.answer('Пришлите текущее количество товара')
    await AddItem.next()


@dp.message_handler(user_id=ADMIN_ID, state=AddItem.amount)
async def item_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = int(message.text)
    await message.answer('Пришлите стоимость в рублях')
    await AddItem.next()


@dp.message_handler(user_id=ADMIN_ID, state=AddItem.price)
async def item_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = int(message.text) * 100
    await message.answer('Пришлите фото товара')
    await AddItem.next()


@dp.message_handler(user_id=ADMIN_ID, state=AddItem.photo, content_types=ContentType.PHOTO)
async def item_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['img'] = message.photo[0].file_id
        services.Items().add_item(data)
    await message.answer('Товар добавлен')
    await state.finish()


@dp.message_handler(user_id=ADMIN_ID, commands='items')
async def show_admin_items(message: types.Message):
    items_list = await no_items_check(message)
    if items_list is None:
        return
    for item in items_list:
        text = f'{hbold(item.name)}\n{item.desc}\n\nЦена: {item.price//100}\n'
        text += "Количество: " + str(item.amount) if item in services.Items().in_stock_items else "Нет в наличии"
        text += f' нажмите /change_amount{item.id} чтобы изменить количество'
        text += f'\nНажмите /del{item.id} для удаления\n'
        await message.answer_photo(photo=item.img, caption=text)


@dp.message_handler(lambda message: message.text.startswith('/del'), user_id=ADMIN_ID)
async def delete_item(message: types.Message):
    await message.answer('Удалено')
    services.Items().delete_item(int(message.text[4:]))



@dp.message_handler(lambda message: message.text.startswith('/change_amount'), user_id=ADMIN_ID)
async def change_item_amount(message: types.Message):
    ChangeAmount.id = int(message.text[14:])
    await ChangeAmount.new_amount.set()
    await message.answer('Введите новое количество товара')


@dp.message_handler(regexp=r'\d+', state=ChangeAmount.new_amount, user_id=ADMIN_ID)
async def set_new_amount(message: types.Message, state: FSMContext):
    services.Items().change_amount(ChangeAmount.id, int(message.text))
    await state.finish()
    await message.answer('Изменено')


@dp.message_handler(commands=['start', 'help'])
async def user_start(message: types.Message):
    services.Users().save_user(message.from_user.id)
    await message.answer('Магазин товаров\nУвидеть список товаров /items\nДобавить почтовые данные /fullname /adress')


@dp.message_handler(commands='items')
async def show_user_items(message: types.Message):
    items_list = await no_items_check(message)
    if items_list is None:
        return
    for item in items_list:
        buy_button = InlineKeyboardButton(text='Купить', callback_data=f'buy{item.id}')
        buy_keyboard = InlineKeyboardMarkup().add(buy_button)
        text = f'{hbold(item.name)}\n{item.desc}\n{item.price//100} руб\n'
        text += 'Количество: ' + str(item.amount) if item in services.Items().in_stock_items else 'Нет в наличии'
        await message.answer_photo(photo=item.img, caption=text, reply_markup=buy_keyboard)


@dp.callback_query_handler(lambda callback: callback.data.startswith('buy'))
async def buy_item(callback: types.CallbackQuery):
    item_id = int(callback.data[3:])
    item = services.Items().get_item_by_id(item_id)
    user = services.Users().get_user_by_id(int(callback.from_user.id), is_tg_id=True)
    if item.amount <= 0:
        await bot.send_message(callback.from_user.id, 'Товар отсутствует')
        return
    if not user.fullname or not user.mail_adress:
        await callback.message.answer('Для начала заполните имя и фамилию')
        return
    await bot.send_invoice(chat_id=callback.from_user.id, title=item.name, description=item.desc,
    payload=f'item{item.id}', provider_token=PAYMENT_TOKEN, currency='RUB', prices=[{'label': 'Руб', 'amount': item.price}])


@dp.pre_checkout_query_handler()
async def pre_check_payment(precheck: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(precheck.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def after_payment(message: types.Message):
    item_id = int(message.successful_payment.invoice_payload[4:])
    services.buy_item(message.from_user.id, item_id)
    user_deliver_info = services.Deliveries.get_user_info()
    item_deliver_info = services.Deliveries.get_delivering_item_name()
    await bot.send_message(ADMIN_ID, f'{item_deliver_info} заказан пользователем {message.from_user.id}')
    await bot.send_message(ADMIN_ID, user_deliver_info)
    await bot.send_message(ADMIN_ID, f'Для подтверждения отправления заказа /confirm_sending{services.Deliveries.get_last_delivery()["id"]}')
    await message.answer('Админ получил уведомление о покупке товара')
    


@dp.message_handler(commands='fullname')
async def add_fullname(message: types.Message):
    await NewName.enter_new_name.set()
    await message.answer('Введите новое ФИО (например: Иванов Иван Иванович)')


@dp.message_handler(state=NewName.enter_new_name)
async def enter_fullname(message: types.Message, state: FSMContext):
    try:
        services.Users().change_fullname(message.from_user.id, message.text)
    except services.IncorrectMessage as e:
        await message.answer(e)
        return
    await message.answer('ФИО добавлено')
    await state.finish()


@dp.message_handler(commands='adress')
async def add_adress(message: types.Message):
    await NewAdress.enter_new_adress.set()
    await message.answer('Введите новый почтовый адрес (Например: ул.Воронежская д.10 кв.65)')


@dp.message_handler(state=NewAdress.enter_new_adress)
async def enter_adress(message: types.Message, state: FSMContext):
    try:
        services.Users().change_mail_adress(message.from_user.id, message.text)
    except services.IncorrectMessage as e:
        await message.answer(e)
        return
    await message.answer('Адрес добавлен')
    await state.finish()
    

@dp.message_handler(lambda message: message.text.startswith('/confirm_sending'), user_id=ADMIN_ID)
async def admin_confirm_sending(message: types.Message):
    delivery_id = int(message.text[16:])
    delivery = services.Deliveries.get_delivery_by_id(delivery_id)
    user = services.Users().get_user_by_id(delivery['user_id'], is_tg_id=False)
    await bot.send_message(user.tg_id, f'Админ отправил доставку заказа\nДля подтверждения получения нажмите /confirm_receiving{delivery_id}')


@dp.message_handler(lambda message: message.text.startswith('/confirm_receiving'))
async def confirm_receiving(message: types.Message):
    await bot.send_message(ADMIN_ID, f'товар для {message.from_user.id} доставлен')
    services.Deliveries.end_delivery(int(message.text[18:]))
    await message.answer('Спасибо за заказ!')



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)