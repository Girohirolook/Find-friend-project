from alice import Alisa
from data.database import Session
from create_database import create_database
import json
from flask import Flask, request
from data.__all_models import *

create_database()
session = Session()


class ShowDialog:
    def handle_dialog(self, alisa):
        # if 'отмена' in alisa.
        if 'registration' in alisa.state_session:
            return self.registration(alisa)
        if alisa.is_new_session():
            return self.new_session(alisa)
        if alisa.command == 'да':
            alisa.add_to_session_state('e', 'error')

        return self.greetings(alisa)

    def cancel_command(self, alisa):
        alisa.remove_session_state()


    def greetings(self, alisa):
        alisa.tts_with_text('Добро пожаловать в навык для поиска партнёра/друга/товарища для игры\n')

    def not_accounted(self, alisa):
        alisa.tts_with_text('Чтобы пользоваться этим навыком нужно войти в яндекс аккаунт')
        alisa.end_session()

    def come_back(self, alisa, person):
        alisa.tts_with_text(person.card.name + '. Вы вернулись')

    def start_registration(self, alisa):
        alisa.add_to_session_state('registration', {'stage': 'nameEnter', 'name': '', 'about': '', 'tags': '', 'contacts': ''})
        alisa.tts_with_text('Чтобы пользоваться данным навыком нужно для начала рассказать о себе.\n'
                            'Введите ваш логин (Имя, которое будет видно всем)')

    def end_registration(self, alisa):
        # Card add
        user_card = Card(**alisa.state_session['registration'])
        session.add(user_card)
        session.commit()

        # User add
        user = User(user_id=alisa.user_id, card_id=user_card.id)
        session.add(user)
        session.commit()

        alisa.remove_session_state_key('registration')

    def registration(self, alisa):
        alisa.restore_session_state()
        info = alisa.get_original_utterance()
        match alisa.get_session_object('registration', 'stage'):
            case 'nameEnter':
                alisa.tts_with_text(f'Хорошо {info}. Теперь расскажи немного о себе (В одном сообщении):')
                alisa.add_to_reg_state('name', info)
                alisa.add_to_reg_state('stage', 'aboutEnter')
            case 'aboutEnter':
                alisa.tts_with_text(f'Отлично. Чтобы найти людей по интересам нужно указать свои увлечения (В одном сообщении, через запятую).')
                alisa.add_to_reg_state('about', info)
                alisa.add_to_reg_state('stage', 'tagsEnter')
            case 'tagsEnter':
                alisa.tts_with_text(f'Осталось последнее. Нужно указать свои контакты, не волнуйся, их увидят только понравившиеся тебе люди')
                alisa.add_to_reg_state('tags', info)
                alisa.add_to_reg_state('stage', 'contactsEnter')
            case 'contactsEnter':
                alisa.tts_with_text(f'Вот и всё, регистрация завершена. Теперь ты можешь просматривать других людей')
                alisa.add_to_reg_state('contacts', info)
                del alisa.state_session['registration']['stage']
                self.end_registration(alisa)

    def new_session(self, alisa):
        self.greetings(alisa)
        if not alisa.user_id:
            return self.not_accounted(alisa)
        person = session.query(User).filter_by(user_id=alisa.user_id).first()
        if person:
            return self.come_back(alisa, person)
        return self.start_registration(alisa)



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

