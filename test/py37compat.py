import sys

if sys.version_info[:2] <= (3, 7):
    import mock
else:
    from unittest import mock
