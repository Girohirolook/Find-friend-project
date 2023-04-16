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

    def handle_dialog(self, alisa):
        self.alisa = alisa
        if self.is_accounted():
            self.user = session.query(User).filter(User.user_id == self.alisa.user_id).first()
        else:
            return self.not_accounted()
        if self.alisa.is_new_session():
            return self.new_session()
        if self.alisa.command == 'да':
            self.test_del()
        if self.alisa.has_intent('Reset'):
            self.alisa.remove_session_state()
        if 'registration' in self.alisa.state_session:
            return self.registration()
        if self.alisa.is_button():
            self.handle_buttons()
        if self.is_authorized():
            return self.base_response()

        return self.greetings()

    def handle_buttons(self):
        if self.alisa.has_button_payload('see_people'):
            return self.see_peoples_start()
        elif self.alisa.has_button_payload('liked'):
            return self.see_peoples_process()
        elif self.alisa.has_button_payload('connections'):
            self.see_liked_peoples()

    def see_peoples_start(self):
        person_card = self.find_next_person()
        self.show_new_card(person_card)

    def see_liked_peoples(self):
        liked_cards = [row.liked_card for row in session.query(LikedUser).filter(LikedUser.user == self.user,
                                                                                LikedUser.is_checked == False).all()]
        user_card = self.user.card
        users_who_liked = [i.user.card for i in session.query(LikedUser).filter(LikedUser.liked_card == user_card,
                                                          LikedUser.is_checked == False).all()]
        for card in liked_cards:
            if card in users_who_liked:
                print(card.user.user_id)




    def find_next_person(self, skipped=None): # Доработать
        if skipped is None:
            skipped = []
        liked_cards = [row.liked_card.id for row in session.query(LikedUser).filter(LikedUser.user == self.user).all()]
        next_card: Card = session.query(Card).filter(Card.id.not_in(liked_cards + skipped), Card.id != self.user.card_id).first()

        if not next_card:
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

    def see_peoples_process(self):
        response = self.alisa.get_button_payload_value('liked')
        card_id = self.alisa.get_button_payload_value('card')
        if response:
            self.add_connection_to_base(card_id)
        else:
            self.add_to_skipped(card_id)
        person_card = self.find_next_person(self.alisa.get_skipped_list())
        return self.show_new_card(person_card)

    def show_new_card(self, card):
        if card is None:
            return self.alisa.tts_with_text('Пользователи закончились')
        self.alisa.show_card_item(card.id, card.name, card.about, card.tags)
        self.alisa.add_to_session_state('card', card.id)
        return self.alisa.tts_with_text('')

    def add_to_skipped(self, card_id):
        # asdsdads
        self.alisa.update_skipped_list(card_id)

    def add_connection_to_base(self, card_id):
        liked_user = session.query(LikedUser).filter(LikedUser.user == self.user, LikedUser.liked_card_id == card_id).all()
        if not liked_user:
            liked = LikedUser(user=self.user, liked_card_id=card_id, is_checked=False)
            session.add(liked)
            session.commit()

    def cancel_command(self):
        self.alisa.remove_session_state()

    def base_response(self):
        self.alisa.button('Просмотреть людей', 'yes', hide=True, payload={'see_people': 'start'})
        self.alisa.button('Новые совпадения', 'yes', hide=True, payload={'connections': 'start'})

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

    def start_registration(self):
        self.alisa.add_to_session_state('registration', {'stage': 'nameEnter', 'name': '', 'about': '', 'tags': '', 'contacts': ''})
        self.alisa.tts_with_text('Чтобы пользоваться данным навыком нужно для начала рассказать о себе.\n'
                            'Введите ваш логин (Имя, которое будет видно всем)')

    def test_del(self):
        self.alisa.update_user_state('skipped', [])
        return self.greetings()

    def end_registration(self):
        # Card add
        user_card = Card(**self.alisa.state_session['registration'])
        session.add(user_card)
        session.commit()

        # User add
        user = User(user_id=self.alisa.user_id, card_id=user_card.id)
        session.add(user)
        session.commit()

        self.alisa.remove_session_state_key('registration')
        self.only_buttons()
        self.base_response()

    def registration(self):
        self.alisa.restore_session_state()
        info = self.alisa.get_original_utterance()
        match self.alisa.get_session_object('registration', 'stage'):
            case 'nameEnter':
                self.alisa.tts_with_text(f'Хорошо {info}. Теперь расскажи немного о себе (В одном сообщении):')
                self.alisa.add_to_reg_state('name', info)
                self.alisa.add_to_reg_state('stage', 'aboutEnter')
            case 'aboutEnter':
                self.alisa.tts_with_text(f'Отлично. Чтобы найти людей по интересам нужно указать свои увлечения (В одном сообщении, через запятую).')
                self.alisa.add_to_reg_state('about', info)
                self.alisa.add_to_reg_state('stage', 'tagsEnter')
            case 'tagsEnter':
                self.alisa.tts_with_text(f'Осталось последнее. Нужно указать свои контакты, не волнуйся, их увидят только понравившиеся тебе люди')
                self.alisa.add_to_reg_state('tags', info)
                self.alisa.add_to_reg_state('stage', 'contactsEnter')
            case 'contactsEnter':
                self.alisa.tts_with_text(f'Вот и всё, регистрация завершена. Теперь ты можешь просматривать других людей')
                self.alisa.add_to_reg_state('contacts', info)
                del self.alisa.state_session['registration']['stage']
                self.end_registration()

    def is_accounted(self):
        if self.alisa.user_id:
            return True
        return False

    def new_session(self):
        self.greetings()
        if self.user:
            return self.come_back()
        return self.start_registration()

    # Насколько она важна????
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
    app.run('192.168.25.17', port=26080)

