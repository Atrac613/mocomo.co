# -*- coding: utf-8 -*-

def create_callback_key(google_id):
    import hashlib
    from config import CALLBACK_SECRET_KEY
    str = '%s-%s' % (CALLBACK_SECRET_KEY, google_id.user_id())
    return hashlib.sha1(str).hexdigest()