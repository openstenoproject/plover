from threading import Event

from plover.gui_none.engine import Engine


def show_error(title, message):
    print('%s: %s' % (title, message))


def main(config):
    engine = Engine(config)
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
