from alice import Alisa
from data.database import Session
from create_database import create_database
import json
from flask import Flask, request
from data.__all_models import *

create_database()
session = Session()


class ShowDialog:
    def __init__(self):
        self.alisa = None

    def handle_dialog(self, alisa):
        self.alisa = alisa

        if self.alisa.has_intent('Reset'):
            self.alisa.remove_session_state()
        if self.alisa.is_new_session():
            return self.new_session()
        if 'registration' in self.alisa.state_session:
            return self.registration()
        if self.alisa.is_button():
            self.handle_buttons()
        if self.is_authorized():
            return self.base_response()

        return self.greetings()

    def handle_buttons(self):
        if self.alisa.get_button_payload_value('see_people'):
            return self.see_peoples()

    def see_peoples(self): # Доработать
        user = session.query(User).filter(User.user_id == self.alisa.user_id).first()
        liked_cards = [row.liked_card.id for row in session.query(LikedUser).filter(LikedUser.user == user).all()]
        next_card: Card = session.query(Card).filter(Card.id.not_in(liked_cards), Card.id != user.card_id).first()
        self.alisa.show_card_item(next_card.name, next_card.about, next_card.tags)
        self.alisa.add_to_session_state('card', next_card.id)

        return self.greetings()


    def cancel_command(self):
        self.alisa.remove_session_state()

    def base_response(self):
        self.alisa.button('Просмотреть людей', 'yes', hide=True, payload={'see_people': 'start'})

    def greetings(self):
        self.alisa.tts_with_text('Добро пожаловать в навык для поиска партнёра/друга/товарища для игры\n')

    def not_accounted(self):
        self.alisa.tts_with_text('Чтобы пользоваться этим навыком нужно войти в яндекс аккаунт')
        self.alisa.end_session()

    def only_buttons(self):
        self.alisa.tts_with_text('Общение в этом навыке ведётся только с помощью кнопок.\n')

    def come_back(self, person):
        self.alisa.tts_with_text(person.card.name + '. Вы вернулись.\n')
        self.only_buttons()
        self.base_response()

    def start_registration(self):
        self.alisa.add_to_session_state('registration', {'stage': 'nameEnter', 'name': '', 'about': '', 'tags': '', 'contacts': ''})
        self.alisa.tts_with_text('Чтобы пользоваться данным навыком нужно для начала рассказать о себе.\n'
                            'Введите ваш логин (Имя, которое будет видно всем)')

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

    def new_session(self):
        self.greetings()
        if not self.alisa.user_id:
            return self.not_accounted()
        person = session.query(User).filter_by(user_id=self.alisa.user_id).first()
        if person:
            return self.come_back(person)
        return self.start_registration()

    def is_authorized(self):
        person = session.query(User).filter_by(user_id=self.alisa.user_id).first()
        if person:
            return True
        return False


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

