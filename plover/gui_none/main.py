from threading import Event

from plover.oslayer.keyboardcontrol import KeyboardEmulation

from plover.gui_none.engine import Engine


def show_error(title, message):
    print('%s: %s' % (title, message))


def main(config, controller):
    engine = Engine(config, controller, KeyboardEmulation())
    if not engine.load_config():
        return 3
    quitting = Event()
    engine.hook_connect('quit', quitting.set)
    engine.start()
    try:
        quitting.wait()
    except KeyboardInterrupt:
        engine.quit()
    return engine.join()
