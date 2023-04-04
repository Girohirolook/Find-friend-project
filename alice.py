from datetime import date, datetime


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
        self.response['session_state'] = self.state_session

    def update_user_state(self, key, value):
        self.response['user_state_update'] = self.response.get('user_state_update', {})
        self.response['user_state_update'][key] = value

    def get_session_object(self, key):
        return self.state_session.get(key, {})

    def get_user_state_object(self, key):
        return self.user_state.get(key, {})

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

    def add_transition(self, name, context, handler):
        self.response['session_state'] = self.response.get('session_state', {})
        self.response['session_state']['__transitions__'] = self.response.get('session_state', {}).get(
            '__transitions__', [])
        self.response['session_state']['__transitions__'].append(
            {'condition': {"name": name, "context": context}, 'handler': handler})

    def get_button_payload_value(self, value):
        return self.event.get('request', {}).get('payload', {}).get(value, {})

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