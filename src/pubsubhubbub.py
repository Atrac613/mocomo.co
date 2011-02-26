# -*- coding: utf-8 -*-

import logging
import urllib
from google.appengine.api import urlfetch

from config import PUBSUBHUBBUB_HUB
from config import CALLBACK

from common_libs import create_callback_key

class pubSubHubbub(object):
    def __init__(self, handler, google_id=None, callback_key=None):
        self.handler = handler
        self.google_id = google_id
        self.pubsubhubbub_hub = PUBSUBHUBBUB_HUB
        if self.google_id is not None:
            self.callback_key = create_callback_key(self.google_id)
            self.callback = CALLBACK % self.callback_key
        else:
            self.callback = None
            self.callback_key = callback_key

    def request(self, post_data):
        form_data = urllib.urlencode(post_data)
        try:
            result = urlfetch.fetch(url=self.pubsubhubbub_hub,
                            payload=form_data,
                            method=urlfetch.POST)
            if result.status_code == 204:
                logging.info('Request Success.')
            logging.debug(result.status_code)
        except:
            logging.error('Request Failed.')
 
    def add_feed(self, subscribe_feed):
        form_fields = {
            'hub.mode' : 'subscribe',
            'hub.callback' : self.callback,
            'hub.topic' : subscribe_feed,
            'hub.verify' : 'sync',
            'hub.verify_token' : '',
         }
        self.request(form_fields)
 
    def remove_feed(self, subscribe_feed):
        form_fields = {
            'hub.mode' : 'unsubscribe',
            'hub.callback' : self.callback,
            'hub.topic' : subscribe_feed,
            'hub.verify' : 'sync',
            'hub.verify_token' : '',
         }
        self.request(form_fields)
    
    def receive_feeds(self, method):
        logging.info('Receiving feed.')
        logging.info('Callback_key: %s' % self.callback_key)
        
        if method == 'GET':
            logging.debug('Authenticating feed.')
            challenge = self.handler.request.get('hub.challenge')
            logging.debug(challenge)
            
            return challenge
        
        elif method == 'POST':
            from google.appengine.api import memcache
            from google.appengine.api.labs import taskqueue
            from google.appengine.runtime import apiproxy_errors
            from uuid import uuid4
            
            logging.debug('Saving feed data.')
            data = {'feed' : self.handler.request.body, 'callback_key': self.callback_key}
            logging.debug(data)
            
            session_id = uuid4()
            
            memcache.Client().add('feed_%s' % session_id, data)
            
            try:
                taskqueue.add(url='/feed', method='GET', params={'session_id' : session_id})
            except (taskqueue.Error, apiproxy_errors.Error):
                logging.exception('Failed to add taskqueue.')
                        
            return ''
        
        else:
            logging.debug('Nope.')
            logging.debug(self.handler.request.body)
            
            return 'hub.receive'