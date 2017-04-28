import os
import site

site.addsitedir(os.path.join(os.path.dirname(__file__), 'site-packages'))
