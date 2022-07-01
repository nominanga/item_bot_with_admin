from typing import NamedTuple, Optional, List

import db
import re


class IncorrectMessage(Exception):
    pass


class NoItems(Exception):
    pass


class Item(NamedTuple):
    id: Optional[int]
    name: str
    desc: str
    amount: int
    price: int
    img: str
    

class User(NamedTuple):
    id: Optional[int]
    tg_id: str
    fullname: Optional[str]
    mail_adress: Optional[str]


class Items:
    def __init__(self):
        self._items_list = self._load_items()

    
    def _load_items(self) -> List[Item]:
        result = []
        for item_dict in db.fetchall('items', ['id', 'name', 'descript', 'amount', 'price', 'img']):
            result.append(Item(id=item_dict['id'], name=item_dict['name'], desc=item_dict['descript'],
            amount=item_dict['amount'], price=item_dict['price'], img=item_dict['img']))
        return result


    def get_items(self) -> List[Item]:
        if not self._items_list:
            raise NoItems('Товары отсутсвуют')
        return self._items_list


    def add_item(self, new_item: dict) -> None:
        db.insert('items', new_item)

    
    def delete_item(self, index: int) -> None:
        db.delete('items', index)


    def change_amount(self, index: int, new_value: int) -> None:
        db.update('items', {'amount': new_value}, index)


    def decrement_amount(self, index: int) -> None:
        print(*[item.amount for item in self.get_items() if item.id == index and item.amount > 0])
        self.change_amount(index, [item.amount for item in self.get_items() 
            if item.id == index and item.amount > 0][0] - 1)


    def get_item_by_id(self, index: int) -> Item:
        for item in self.get_items():
            if item.id == index:
                return item


    @property
    def in_stock_items(self) -> List[Item]:
        return [item for item in self.get_items() if item.amount > 0]


class Users:
    def __init__(self):
        self._users = self._load_users()

    
    def _load_users(self) -> List[User]:
        result = [User(id=user['id'], tg_id=user['tg_id'], 
        fullname=user['fullname'], mail_adress=user['mail_adress']) for user in db.fetchall('users', ['id', 
        'tg_id', 'fullname', 'mail_adress'])]
        return result


    def save_user(self, tg_id: int):
        if tg_id not in self.user_tg_ids:
            db.insert('users', {'tg_id': tg_id})

    
    def change_fullname(self, tg_id: int, fullname: str):
        if re.fullmatch(r'[А-я]{1}[а-я]+ [А-я]{1}[а-я]+ [А-я]{1}[а-я]+', fullname):
            db.update('users', {'fullname': fullname}, 
            [user.id for user in self._users if int(user.tg_id) == tg_id][0])
        else:
            raise IncorrectMessage('Неправильный формат ввода имени и фамилии')


    def change_mail_adress(self, tg_id: int, adress: str):
        if re.fullmatch(r'ул\.[А-я]+ д\.\d+ кв\.\d+', adress):
            db.update('users', {'mail_adress': adress}, 
            [user.id for user in self._users if int(user.tg_id) == tg_id][0])
        else:
            raise IncorrectMessage('Неправильный формат ввода адреса(доставка только по москве')


    @property
    def user_tg_ids(self) -> List[str]:
        return [int(user.tg_id) for user in self._users]


    def get_users(self) -> List[User]:
        return self._users


    def get_user_by_id(self, index: int, is_tg_id=True) -> User:
        for user in self.get_users(): 
            if int(user.tg_id) == index and is_tg_id:
                return user
            elif user.id == index and not is_tg_id:
                return user

    


class Deliveries:
    @staticmethod
    def create(item_id, user_id):
        db.insert('item_deliver', {'delivered': False, 'user_id': user_id, 'item_id': item_id})


    @staticmethod
    def get_delivery_by_id(index: int) -> dict:
        for delivery in Deliveries.get_all_deliveries():
            if delivery['id'] == index:
                return delivery
    

    @staticmethod
    def get_all_deliveries() -> List[dict]:
        return db.fetchall('item_deliver', ['id', 'delivered', 'user_id', 'item_id'])


    @staticmethod
    def get_last_delivery() -> dict:
        return Deliveries.get_all_deliveries()[-1]


    @staticmethod
    def end_delivery(index: int) -> None:
        db.update('item_deliver', {'delivered': True}, index)

    
    @staticmethod
    def get_delivering_item_name() -> str:
        return Items().get_item_by_id(Deliveries.get_last_delivery()['item_id']).name


    @staticmethod
    def get_user_info() -> str:
        print(Deliveries.get_last_delivery()['user_id'], type(Deliveries.get_last_delivery()['user_id']))
        user = Users().get_user_by_id(Deliveries.get_last_delivery()['user_id'], is_tg_id=False)
        return f'{user.fullname} сделал заказ на адрес {user.mail_adress}'


def buy_item(user_tg_id, item_id):
    user = Users().get_user_by_id(user_tg_id, is_tg_id=True)
    item = Items().get_item_by_id(item_id)

    Items().decrement_amount(item.id)
    Deliveries.create(item.id, user.id)
