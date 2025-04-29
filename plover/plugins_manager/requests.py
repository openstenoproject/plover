import os

from requests_futures import sessions
import requests_cache

from plover.oslayer.config import CONFIG_DIR


CACHE_NAME = os.path.join(CONFIG_DIR, '.cache', 'plugins')


class CachedSession(requests_cache.CachedSession):

    def __init__(self):
        dirname = os.path.dirname(CACHE_NAME)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        super().__init__(cache_name=CACHE_NAME,
                         backend='sqlite',
                         expire_after=600)
        self.cache.delete(expired=True)


class CachedFuturesSession(sessions.FuturesSession):

    def __init__(self, session=None):
        if session is None:
            session = CachedSession()
        super().__init__(session=session, max_workers=4)
