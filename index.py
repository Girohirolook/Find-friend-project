from alice import Alisa
from data.database import Session, create_db
import json
from flask import Flask, request
from data.user import User

create_db()
session = Session()


class ShowDialog:
    def handle_dialog(self, alisa):
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
        alisa.tts_with_text(person.name + '. Вы вернулись')

    def registration(self, alisa):
        alisa.restore_session_state()
        info = alisa.get_original_utterance()
        if 'registration' not in alisa.state_session:
            alisa.tts_with_text('Чтобы пользоваться данным навыком нужно для начала рассказать о себе.\n'
                                'Введите ваш логин (Имя, которое будет видно всем)')
            alisa.add_to_session_state('registration', {'name': '', 'about': '', 'tags': '', 'contacts': ''})
        elif not alisa.get_session_object('registration').get('name'):
            alisa.add_to_reg_state('name', info)
            alisa.tts_with_text(f'Хорошо {info}. Теперь расскажи немного о себе (В одном сообщении):')
        elif not alisa.get_session_object('registration').get('about'):
            alisa.add_to_reg_state('about', info)
            alisa.tts_with_text(f'Отлично. Чтобы найти людей по интересам нужно указать свои увлечения (В одном сообщении, Лучше через запятую).')
        elif not alisa.get_session_object('registration').get('tags'):
            alisa.add_to_reg_state('tags', info)
            alisa.tts_with_text(f'Осталось последнее. нужно указать свои контакты, не волнуйся, их увидят только понравившиеся тебе люди')
        elif not alisa.get_session_object('registration').get('contact'):
            alisa.add_to_reg_state('contacts', info)
            alisa.tts_with_text(f'Вот и всё, регистрация завершена. Теперь ты можешь просматривать других людей')
            print(alisa.state_session)
            alisa.remove_session_state_key('registration')



    def new_session(self, alisa):
        self.greetings(alisa)
        if not alisa.user_id:
            return self.not_accounted(alisa)
        person = session.query(User).filter_by(user_id=alisa.user_id).first()
        if person:
            return self.come_back(alisa, person)
        return self.registration(alisa)



dialog = ShowDialog()


def main_handler(request, context):
    response = {
        "version": request['version'],
        "response": {
            "end_session": False
        }
    }

    dialog.handle_dialog(Alisa(request, response))

    session.close()
    return response









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

