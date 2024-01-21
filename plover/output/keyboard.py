from time import sleep

from plover.output import Output


class GenericKeyboardEmulation(Output):
  def __init__(self):
    super().__init__()
    self._key_press_delay_ms = 0

  def set_key_press_delay(self, delay_ms):
    self._key_press_delay_ms = delay_ms

  def delay(self):
    if self._key_press_delay_ms > 0:
      sleep(self._key_press_delay_ms / 1000)

  def half_delay(self):
    if self._key_press_delay_ms > 0:
      sleep(self._key_press_delay_ms / 2000)

  def with_delay(self, iterable):
    for item in iterable:
      yield item
      self.delay()
