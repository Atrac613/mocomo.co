# -*- coding: utf-8 -*-

from django.utils import simplejson
from google.appengine.api import urlfetch

GOOGLE_SHORTNER_API_KEY = ''

try:
    from config import GOOGLE_SHORTNER_API_KEY
except:
    pass

api_url = 'https://www.googleapis.com/urlshortener/v1/url?key=%s' % GOOGLE_SHORTNER_API_KEY

def short(url):
    if url != '':
        body = simplejson.dumps({'longUrl': url})
        url_data = urlfetch.fetch(api_url, body, method=urlfetch.POST, headers={'Content-Type': 'application/json'})
        
    else:
        return ''
        
    if url_data.status_code == 200:
        url_info = simplejson.loads(url_data.content)
        return url_info['id']

    else:
        return ''