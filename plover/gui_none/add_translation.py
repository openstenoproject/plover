
from plover.engine import StartingStrokeState


class AddTranslation:

    def __init__(self, engine):
        self._status = None
        self._engine = engine
        self._translator_states = []
        self._strokes, self._translation = (None, None)
        engine.hook_connect('add_translation', self.trigger)

    def _get_state(self):
        return (
            self._engine.translator_state,
            self._engine.starting_stroke_state,
        )

    def _set_state(self, translator_state, starting_stroke_state):
        self._engine.translator_state = translator_state
        self._engine.starting_stroke_state = starting_stroke_state

    def _clear_state(self, undo=False):
        self._engine.clear_translator_state(undo)
        self._engine.starting_stroke_state = StartingStrokeState(False, False)

    def _push_state(self):
        self._translator_states.insert(0, self._get_state())

    def _pop_state(self, undo=False):
        if undo:
            self._engine.clear_translator_state(True)
        self._set_state(*self._translator_states.pop(0))

    @staticmethod
    def _stroke_filter(key, value):
        return value != '{PLOVER:ADD_TRANSLATION}'

    def send_string(self, s):
        self._translation += s

    def send_backspaces(self, b):
        self._translation = self._translation[:-b]

    def trigger(self):
        if self._status is None:
            self._push_state()
            self._clear_state()
            self._engine.add_dictionary_filter(self._stroke_filter)
            self._status = 'strokes'
        elif self._status == 'strokes':
            self._engine.remove_dictionary_filter(self._stroke_filter)
            state = self._get_state()[0]
            # Ignore add translation stroke.
            state.translations = state.translations[1:]
            strokes = []
            for t in state.translations:
                strokes.extend(t.strokes)
            if not strokes:
                # Abort add translation.
                self._pop_state(undo=True)
                self._status = None
                return
            self._strokes = tuple(s.rtfcre for s in strokes)
            self._clear_state(undo=True)
            self._translation = ''
            self._status = 'translations'
            self._engine.hook_connect('send_string', self.send_string)
            self._engine.hook_connect('send_backspaces', self.send_backspaces)
        elif self._status == 'translations':
            state = self._get_state()[0]
            # Ignore add translation stroke.
            state.translations = state.translations[1:]
            self._engine.hook_disconnect('send_string', self.send_string)
            self._engine.hook_disconnect('send_backspaces', self.send_backspaces)
            self._translation = self._translation.strip()
            self._engine.add_translation(self._strokes, self._translation)
            self._pop_state(undo=True)
            self._status = None
