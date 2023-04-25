from alice import Alisa
from data.database import Session
from create_database import create_database
import json
from flask import Flask, request
from data.__all_models import *
import random

create_database()
session = Session()


class ShowDialog:
    def __init__(self):
        self.alisa = None
        self.user = None

    # HANDLES
    def handle_dialog(self, alisa):
        self.alisa = alisa
        if self.is_accounted():
            self.user = session.query(User).filter(User.user_id == self.alisa.user_id).first()
        else:
            return self.not_accounted()
        if self.alisa.is_new_session():
            return self.new_session()
        if self.alisa.has_intent('Reset'):
            return self.reset()
        if self.alisa.has_intent('YANDEX.WHAT_CAN_YOU_DO'):
            return self.what_can_you_do_response()
        if self.alisa.has_intent('YANDEX.HELP'):
            return self.help_response()
        if self.alisa.is_button():
            self.handle_buttons()
            return self.base_response()
        if 'registration' in self.alisa.state_session:
            return self.registration()
        if 'registration_change' in self.alisa.state_session:
            return self.update_user()

        return self.dont_understand()

    def handle_buttons(self):
        if self.alisa.has_button_payload('see_people'):
            return self.see_peoples_start()
        elif self.alisa.has_button_payload('see_contacts'):
            return self.see_card_with_contacts()
        elif self.alisa.has_button_payload('liked'):
            return self.see_peoples_process()
        elif self.alisa.has_button_payload('connections'):
            self.see_liked_peoples()
        elif self.alisa.has_button_payload('connections_history'):
            self.see_history_liked_peoples()
        elif self.alisa.has_button_payload('registration_change'):
            self.change_registration()

    def help_response(self):
        if 'registration' in self.alisa.state_session:
            self.alisa.restore_session_state()
            self.alisa.tts_with_text('Сейчас вы регистрируетесь в навыке "TEAM SEARCH".\n')
            return self.help_registration()
        elif 'registration_change' in self.alisa.state_session:
            self.alisa.remove_session_state()
        self.alisa.tts_with_text('Вы сейчас находитесь в навыке "TEAM SEARCH"\n')
        self.alisa.tts_with_text('\nНапишите "Что ты умеешь" чтобы увидеть список доступных команд\n')
        self.only_buttons()
        self.base_response()

    def what_can_you_do_response(self):
        if 'registration_change' in self.alisa.state_session:
            self.alisa.remove_session_state()
        self.alisa.tts_with_text(
            'Я умею предлагать разные анкеты людей и выдавать тех с которыми у вас одинаковые вкусы \n')
        self.alisa.tts_with_text('Нажмите "Посмотреть анкеты" чтобы увидеть новые анкеты \n')
        self.alisa.tts_with_text(
            'Нажмите "Новые совпадения" или "История совпадений", чтобы увидеть с кем у вас похожие вкусы\n')
        if 'registration' in self.alisa.state_session:
            self.alisa.restore_session_state()
            self.alisa.tts_with_text(
                '\nВ данный момент эти функции заблокированы, так как вам нужно зарегестрироваться в навыке\n')
            return self.help_registration()
        self.base_response()

    def help_registration(self):
        field = self.alisa.get_session_object('registration', 'stage')
        if field == 'nameEnter':
            self.alisa.tts_with_text(f'Придумайте и введите ваш логин')
        elif field == 'aboutEnter':
            self.alisa.tts_with_text(
                f'Введите немного информации о себе')
        elif field == 'tagsEnter':
            self.alisa.tts_with_text(
                f'Введите ваши увлечения (В одном сообщении, через запятую)')
        elif field == 'contactsEnter':
            self.alisa.tts_with_text(
                f'Осталось последнее. Введите ваши контакты')

    # BUTTON FUNCS
    def see_peoples_start(self):
        person_card = self.find_next_person()
        self.show_new_card(person_card)

    def see_peoples_process(self):
        response = self.alisa.get_button_payload_value('liked')
        card_id = self.alisa.get_button_payload_value('card')
        if response:
            self.add_connection_to_base(card_id)
        else:
            self.add_to_skipped(card_id)
        person_card = self.find_next_person(self.alisa.get_skipped_list())
        return self.show_new_card(person_card)

    def see_card_with_contacts(self):
        card_id = self.alisa.get_button_payload_value('see_contacts')
        card = self.get_one_card(card_id)
        self.alisa.show_one_card(card.name, card.about, card.tags, card.contacts)
        return self.alisa.tts_with_text('Вот контакты этого пользователя')  # change

    def see_liked_peoples(self):
        liked_cards = self.get_both_liked_cards(checked=False)[:5]
        if liked_cards:
            self.to_update_cards_check(liked_cards)
            return self.show_liked_cards(liked_cards)
        return self.alisa.tts_with_text('Новые совпадения отсутствуют')

    def see_history_liked_peoples(self):
        history_type = self.alisa.get_button_payload_value('connections_history')
        if history_type['type'] == 'start':
            self.history_start()
        elif history_type['type'] == 'next':
            self.history_next(history_type['value'])

    def history_start(self):
        history_cards = self.get_history_cards()
        if history_cards:
            return self.show_history_cards(history_cards, len(history_cards))
        return self.alisa.tts_with_text('Совпадения отсутствуют')

    def history_next(self, num):
        history_cards = self.get_history_cards(num)
        print(num + len(history_cards))
        self.show_history_cards(history_cards, num + len(history_cards))

    def change_registration(self):  # Изменение регистрации через itemlist
        button_payload: dict = self.alisa.get_button_payload_value('registration_change')
        if button_payload == 'start':
            self.alisa.show_change_registration_block()
            return self.alisa.tts_with_text('Выберите то что хотите изменить')
        else:
            self.add_change_to_state(button_payload['type'])
            return self.alisa.tts_with_text('\nВведите новое значение')

    def add_change_to_state(self, update_field):
        self.alisa.add_to_session_state('registration_change', update_field)
        value = ''
        if update_field == 'name':
            value = self.user.card.name
        elif update_field == 'about':
            value = self.user.card.about
        elif update_field == 'tags':
            value = self.user.card.tags
        elif update_field == 'contacts':
            value = self.user.card.contacts
        self.alisa.tts_with_text(f'Текущее значение: {value}\n')

    # SHOW FUNCS
    def show_one_card(self, card):
        self.alisa.show_one_card(card.name, card.about, card.tags, card.contacts)

    def show_liked_cards(self, cards):
        cards = [i.liked_card for i in cards]
        self.alisa.show_cards(cards)
        # self.alisa.button('Посмотреть следующих', None, payload={'connections': 'next'})
        return self.greetings()

    def show_new_card(self, card):
        if card is None:
            return self.alisa.tts_with_text('Пользователи закончились')
        self.alisa.show_card_item(card.id, card.name, card.about, card.tags)
        self.alisa.add_to_session_state('card', card.id)
        return self.alisa.tts_with_text('')

    def show_history_cards(self, cards, value=0):
        if cards:
            self.alisa.show_cards(cards)
            self.alisa.button('Посмотреть следующих', None,
                              payload={'connections_history': {'type': 'next', 'value': value}})
            return self.alisa.tts_with_text('Найдена история')
        return self.alisa.tts_with_text('Совпадения закончились')
        # self.alisa.button('Посмотреть предыдущих', None, payload={'connections_history': 'last'})

    # DATABASE FUNCS
    def to_update_cards_check(self, cards):
        for card in cards:
            card.is_checked = True
        session.commit()

    def get_one_card(self, card_id):
        return session.query(Card).filter(Card.id == card_id).first()

    def add_connection_to_base(self, card_id):
        self.delete_from_skipped(card_id)
        liked_user = session.query(LikedUser).filter(LikedUser.user == self.user,
                                                     LikedUser.liked_card_id == card_id).all()
        if not liked_user:
            liked = LikedUser(user=self.user, liked_card_id=card_id, is_checked=False)
            session.add(liked)
            session.commit()

    def get_both_liked_cards(self, checked=False):
        user_card = self.user.card
        users_who_liked = [i.user.card.id for i in
                           session.query(LikedUser).filter(LikedUser.liked_card == user_card).all()]

        return session.query(LikedUser).filter(LikedUser.user == self.user,
                                               LikedUser.is_checked == checked,
                                               LikedUser.liked_card_id.in_(
                                                   users_who_liked)).all()

    def get_history_cards(self, num=0):
        'history_count: 123'
        # history_count = self.alisa.get_session_object('history_count')
        cards = [i.liked_card for i in self.get_both_liked_cards(checked=True)]
        return cards[num:num + 5]

    def add_to_skipped(self, card_id):
        self.alisa.update_skipped_list(card_id)

    def delete_from_skipped(self, card_id):
        if card_id in self.alisa.get_skipped_list():
            self.alisa.delete_from_skipped_list(card_id)

    def find_next_person(self, skipped=None):  # Доработать
        if skipped is None:
            skipped = []
        liked_cards = [row.liked_card.id for row in session.query(LikedUser).filter(LikedUser.user == self.user).all()]
        next_card = session.query(Card).filter(Card.id.not_in(liked_cards + skipped),
                                               Card.id != self.user.card_id).all()
        if self.find_sort(next_card):
            next_card = next_card[0][0]
        else:
            current_card = self.alisa.get_session_object('card')
            if isinstance(current_card, dict):
                current_card = []
            elif isinstance(current_card, int):
                current_card = [current_card]
            next_cards = session.query(Card).filter(Card.id.not_in(liked_cards + current_card),
                                                    Card.id != self.user.card_id).all()
            if len(next_cards) > 0:
                next_card = random.choice(next_cards)
            else:
                return None
        return next_card

    def find_sort(self, cards):
        if len(cards) == 0:
            return False
        links = session.query(LikedUser).filter(LikedUser.user_id.in_([card.user.id for card in cards]),
                                                LikedUser.liked_card_id == self.user.card_id).all()
        links = [i.user_id for i in links]
        for i in range(len(cards)):
            if cards[i].user.id in links:
                cards[i] = (cards[i], 0)
            else:
                cards[i] = (cards[i], 1)
        cards.sort(key=lambda x: x[1])
        return True

    def update_user(self):
        card = self.user.card
        text = self.alisa.get_original_utterance()
        field = self.alisa.get_session_object('registration_change')
        if field == 'name':
            card.name = text
        elif field == 'about':
            card.about = text
        elif field == 'tags':
            card.tags = text
        elif field == 'contacts':
            card.contacts = text
        session.commit()
        self.base_response()
        return self.alisa.tts_with_text("Значение успешно изменено")

    def add_user(self):
        # Card add
        user_card = Card(**self.alisa.state_session['registration'])
        session.add(user_card)
        session.commit()

        # User add
        user = User(user_id=self.alisa.user_id, card_id=user_card.id)
        session.add(user)
        session.commit()

        self.user = user

    # JUST COMMANDS
    def dont_understand(self):
        self.alisa.tts_with_text('Я вас не поняла \n')
        self.only_buttons()
        self.base_response()

    def cancel_command(self):
        self.alisa.remove_session_state()

    def base_response(self):
        both_liked_cards = self.get_both_liked_cards()
        self.alisa.button('Просмотреть анкеты', 'yes', hide=True, payload={'see_people': 'start'})
        if len(both_liked_cards) > 0:
            self.alisa.button(f'({len(both_liked_cards)}) Новые совпадения', 'yes', hide=True,
                              payload={'connections': 'start'})
        else:
            self.alisa.button('Новые совпадения', 'yes', hide=True, payload={'connections': 'start'})
        self.alisa.button('История совпадений', 'yes', hide=True, payload={'connections_history': {'type': 'start'}})
        self.alisa.button('Изменить данные', 'yes', hide=True, payload={'registration_change': 'start'})
        self.alisa.button('Что ты умеешь', 'yes', hide=True)
        self.alisa.button('Помощь', 'yes', hide=True)

    def greetings(self):
        self.alisa.tts_with_text('Добро пожаловать в навык для поиска партнёра/друга/товарища для игры\n')

    def not_accounted(self):
        self.alisa.tts_with_text('Чтобы пользоваться этим навыком нужно войти в яндекс аккаунт')
        self.alisa.end_session()

    def only_buttons(self):
        self.alisa.tts_with_text('Общение в этом навыке ведётся только с помощью кнопок.\n')

    def come_back(self):
        self.alisa.tts_with_text(self.user.card.name + ', вы вернулись.\n')
        self.only_buttons()
        self.base_response()

    def reset(self):
        self.alisa.remove_session_state()
        self.greetings()
        if not self.is_authorized():
            return self.start_registration()
        return self.base_response()

    # REGISTRATION FUNCS
    def start_registration(self):
        self.alisa.add_to_session_state('registration',
                                        {'stage': 'nameEnter', 'name': '', 'about': '', 'tags': '', 'contacts': ''})
        self.alisa.tts_with_text('\n Чтобы пользоваться данным навыком нужно для начала рассказать о себе.\n'
                                 'Придумайте и напишите свой логин (Имя, которое будет видно всем)')

    def registration(self):
        self.alisa.restore_session_state()
        info = self.alisa.get_original_utterance()
        if len(info) >= 255:
            return self.alisa.tts_with_text('Поле слишком длинное. Попробуйте ещё раз.')
        field = self.alisa.get_session_object('registration', 'stage')
        if field == 'nameEnter':
            self.alisa.tts_with_text(f'Хорошо {info}. Теперь напиши немного о себе (В одном сообщении):')
            self.alisa.add_to_reg_state('name', info)
            self.alisa.add_to_reg_state('stage', 'aboutEnter')
        elif field == 'aboutEnter':
            self.alisa.tts_with_text(
                f'Отлично. Чтобы найти людей по интересам нужно написать свои увлечения (В одном сообщении, '
                f'через запятую).')
            self.alisa.add_to_reg_state('about', info)
            self.alisa.add_to_reg_state('stage', 'tagsEnter')
        elif field == 'tagsEnter':
            self.alisa.tts_with_text(
                f'Осталось последнее. Нужно написать свои контакты (телеграм, vk и т.п.), не волнуйтесь, их увидят только понравившиеся '
                f'вам люди')
            self.alisa.add_to_reg_state('tags', info)
            self.alisa.add_to_reg_state('stage', 'contactsEnter')
        elif field == 'contactsEnter':
            self.alisa.tts_with_text(
                f'Вот и всё, регистрация завершена. Теперь вы можете просматривать других людей.\n')
            self.alisa.add_to_reg_state('contacts', info)
            del self.alisa.state_session['registration']['stage']
            self.end_registration()

    def end_registration(self):
        self.add_user()
        self.alisa.remove_session_state_key('registration')
        self.only_buttons()
        self.base_response()

    # SUB FUNCS
    def new_session(self):
        self.greetings()
        self.alisa.tts_with_text('\n Данный навык поможет вам найти товарища для игры в какую-либо игру \n')
        if self.user:
            return self.come_back()
        return self.start_registration()

    def is_accounted(self):
        if self.alisa.user_id:
            return True
        return False

    def is_authorized(self):
        return self.user is not None


dialog = ShowDialog()

# def main_handler(request, context):
#     response = {
#         "version": request['version'],
#         "response": {
#             "end_session": False
#         }
#     }
#
#     dialog.handle_dialog(Alisa(request, response))
#
#     session.close()
#     return response


# Start


app = Flask(__name__)


@app.route('/')
def index():
    return ''


@app.route("/", methods=['POST'])
def main():
    response = {
        "version": request.json['version'],
        "response": {
            "end_session": False
        }
    }

    dialog.handle_dialog(Alisa(request.json, response))

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


if __name__ == '__main__':
    app.run('192.168.25.17', port=36080)
