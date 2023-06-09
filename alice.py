from datetime import date, datetime

import pymorphy2.analyzer
from pymorphy2.analyzer import MorphAnalyzer


class Alisa:
    def __init__(self, request: dict, response: dict):
        self.event, self.answer, self.response = request, response['response'], response
        self.intents = self.event.get('request', {}).get('nlu', {}).get('intents', {})
        self.command = self.event.get('request', {}).get('command')
        self.state_session = self.event.get('state', {}).get('session', {})
        self.application_state = self.event.get('state', {}).get('application', {})
        self.user_state = self.event.get('state', {}).get('user', {})
        self.original_utterance = self.event.get('request', {}).get('original_utterance')
        self.user_id = self.event.get('session', {}).get('user', {}).get('user_id', {})

    def is_new_session(self):
        return self.event['session']['new']

    def is_show_request(self):
        return self.event['request']['type'] == "Show.Pull"

    def get_state(self):
        return self.event['state']

    def get_intent_slot_value(self, intent, slot):
        return self.intents.get(intent, {}).get('slots', {}).get(slot, {}).get('value', {})

    def get_original_utterance(self):
        return self.original_utterance

    def add_to_session_state(self, key, value):
        self.response['session_state'] = self.response.get('session_state', {})
        self.response['session_state'][key] = value

    def add_to_reg_state(self, k, v):
        self.response['session_state'] = self.response.get('session_state', {})
        self.get_session_object('registration')[k] = v

    def remove_session_state(self):
        self.state_session = {}

    def remove_session_state_key(self, key):
        del self.state_session[key]

    def restore_session_state(self):
        if self.state_session:
            self.response['session_state'] = self.state_session

    def get_user_state_update(self):
        return self.response.get('user_state_update', {})

    def update_user_state(self, key, value):
        self.response['user_state_update'] = self.response.get('user_state_update', {})
        self.response['user_state_update'][key] = value

    def update_skipped_list(self, value):
        cards = self.get_skipped_list()
        if value not in cards:
            cards.append(value)
            self.update_user_state('skipped', cards)

    def delete_from_skipped_list(self, value):
        cards = self.get_skipped_list()
        del cards[cards.index(value)]
        self.update_user_state('skipped', cards)

    def get_session_object(self, *args):
        session_object = self.state_session
        for key in args:
            session_object = session_object.get(key, {})
        return session_object

    def get_user_state_object(self, key):
        return self.user_state.get(key, {})

    def get_skipped_list(self):
        if self.get_user_state_update():
            cards = self.get_user_state_update()['skipped']
        else:
            cards = self.get_user_state_object('skipped')
        if not cards:
            return []
        return cards

    def end_session(self):
        self.answer['end_session'] = True

    def voice_button(self, condition, handler):
        matcher, context = condition
        self.add_transition(matcher, context, handler)

    def suggest(self, title, handler, url=None, payload=None):
        if payload is None:
            payload = {}
        self.button(title, handler, True, url, payload)

    def button(self, title, handler, hide=False, url=None, payload=None):
        if payload is None:
            payload = {}
        self.answer['buttons'] = self.answer.get('buttons', [])
        payload["__transition__"] = {'condition': {"name": 'call_handler', "context": {}}, 'handler': handler}
        button = {"title": title,
                  "payload": payload,
                  "hide": hide}
        if url:
            button["url"] = url
        self.answer['buttons'].append(button)

    def call_after(self, handler):
        self.add_transition('call_handler', {}, handler)

    def show_card_item(self, card_id, header, title, description):
        self.answer['card'] = {'type': 'ItemsList'}
        self.answer['card']['header'] = {'text': header}
        self.answer['card']['items'] = [{'title': title, 'description': description}]
        self.button('Нравиться', None, payload={'liked': True, 'card': card_id})
        self.button('Пропустить', None, payload={'liked': False, 'card': card_id})

    def show_one_card(self, name, about, tags, contacts):
        self.answer['card'] = {'type': 'ItemsList'}
        self.answer['card']['header'] = {'text': name}
        self.answer['card']['items'] = [{'title': about, 'description': tags}]
        self.answer['card']['footer'] = {'text': contacts}

    def show_change_registration_block(self):
        self.answer['card'] = {'type': 'ItemsList'}
        self.answer['card']['header'] = {'text': 'Выберите то что хотите изменить'}
        change_types = {'Имя': 'name', 'О себе': 'about', 'Увлечения': 'tags', 'Контакты': 'contacts'}
        self.answer['card']['items'] = [{}]
        for k, v in change_types.items():
            self.button(k, None, payload={'registration_change': {'type': v}})

    def show_cards(self, cards):
        analyzer = MorphAnalyzer()
        find = 'Найдено'
        if len(cards) == 1:
            find = 'Найден'
        users = analyzer.parse('пользователь')[0]
        self.answer['card'] = {'type': 'ItemsList'}
        self.answer['card']['header'] = {'text': f'{find} {len(cards)} {users.make_agree_with_number(len(cards)).word}. Нажмите на них чтобы посмотреть контакты'}
        items = []
        for card in cards:
            items.append({'title': card.name, 'description': card.about, 'button':
                {'text': 'Посмотреть контакты', 'payload': {'see_contacts': card.id}}})
        self.answer['card']['items'] = items

    def add_transition(self, name, context, handler):
        self.response['session_state'] = self.response.get('session_state', {})
        self.response['session_state']['__transitions__'] = self.response.get('session_state', {}).get(
            '__transitions__', [])
        self.response['session_state']['__transitions__'].append(
            {'condition': {"name": name, "context": context}, 'handler': handler})

    def get_button_payload_value(self, value):
        return self.event.get('request', {}).get('payload', {}).get(value, {})

    def has_button_payload(self, value):
        return value in self.event.get('request', {}).get('payload', {})

    def get_transitions(self):
        transitions = self.state_session.get('__transitions__', [])
        if self.event.get('request', {}).get('type', '') == 'ButtonPressed':
            button_transition = self.event.get('request', {}).get('payload', {}).get('__transition__')
            if button_transition:
                transitions.append(button_transition)
        return transitions

    def show_episode(self, text, episode_id=None, title=None, tts=None, title_tts=None, pub_date=None, exp_date=None):
        show_item_meta = {}
        show_item_meta['content_id'] = episode_id if episode_id is not None else str(date.today())
        if title:
            show_item_meta['title'] = title
        if title_tts:
            show_item_meta['title_tts'] = title_tts

        show_item_meta['publication_date'] = pub_date if pub_date is not None else datetime.now().isoformat() + "Z"
        if exp_date:
            show_item_meta['exp_date'] = exp_date

        self.answer['text'] = text
        if tts:
            self.answer['tts'] = tts
        self.answer['show_item_meta'] = show_item_meta

    def tts_with_text(self, tts):
        self.answer['text'] = self.answer.get('text', '') + tts
        self.answer['tts'] = self.answer.get('tts', '') + tts

    def text(self, tts):
        self.answer['text'] = self.answer.get('text', '') + tts

    def tts(self, tts):
        self.answer['tts'] = self.answer.get('tts', '') + tts

    def has_intent(self, intent):
        return self.intents.get(intent)

    def is_button(self):
        return self.event['request']['type'] == "ButtonPressed"