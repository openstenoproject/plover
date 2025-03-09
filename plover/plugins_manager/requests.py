import os

from requests_futures.sessions import FuturesSession
from requests_cache import CachedSession

from plover.oslayer.config import CONFIG_DIR


CACHE_NAME = os.path.join(CONFIG_DIR, '.cache', 'plugins')


class CachedSession(CachedSession):

    def __init__(self):
        dirname = os.path.dirname(CACHE_NAME)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        super().__init__(cache_name=CACHE_NAME,
                         backend='sqlite',
                         expire_after=600)
        self.remove_expired_responses()


class CachedFuturesSession(FuturesSession):

    def __init__(self, session=None):
        if session is None:
            session = CachedSession()
        super().__init__(session=session, max_workers=4)
