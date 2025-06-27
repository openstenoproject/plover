class CaptureOutput:

    def __init__(self):
        self.instructions = []
        self.text = ''

    def send_backspaces(self, n):
        assert n <= len(self.text)
        self.text = self.text[:-n]
        self.instructions.append(('b', n))

    def send_string(self, s):
        self.text += s
        self.instructions.append(('s', s))

    def send_key_combination(self, c):
        self.instructions.append(('c', c))

    def send_engine_command(self, c):
        self.instructions.append(('e', c))
