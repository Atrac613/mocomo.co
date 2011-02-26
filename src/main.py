# -*- coding: utf-8 -*-

import os
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

from twitter_oauth_handler import OAuthClient

from mocomoco_db import OAuthAccessToken
from mocomoco_db import UserPrefs

#MainPage
class MainPage(webapp.RequestHandler):
    def get(self):
            
        template_values = {
            }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, template_values))

#HomePage
class HomePage(webapp.RequestHandler):
    def get(self):
        
        user = users.get_current_user()
        nickname = user.nickname()
        logout_url = users.create_logout_url('/')
        
        template_values = {
            'nickname' : nickname,
            'logout_url' : logout_url
            }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/home.html')
        self.response.out.write(template.render(path, template_values))

#Config Page
class ConfigPage(webapp.RequestHandler):
    def get(self):
        from csrffilter import CSRFFilter
        from pubsubhubbub import pubSubHubbub
        
        user = users.get_current_user()
        
        user_prefs_query = UserPrefs.all()
        user_prefs_query.filter("google_id =", user)
        user_prefs = user_prefs_query.get()
        
        mode = self.request.get('mode')
        
        if mode == 'add_twitter_account':
            self.redirect('/oauth/twitter/login')
            
        elif mode == 'delete_twitter_account':
            if user_prefs.oauth_access_token_key:
                oauth_access_token_query = OAuthAccessToken.get_by_key_name(user_prefs.oauth_access_token_key.key().name())
                oauth_access_token_query.delete()
                user_prefs.oauth_access_token_key = None
                user_prefs.put()
                
        elif mode == 'enable_sync':
            hub = pubSubHubbub(self, user)
            
            subscribe_feed = 'http://buzz.googleapis.com/feeds/%s/public/posted' % user.nickname()
            hub.add_feed(subscribe_feed)
            
            user_prefs.callback_key = hub.callback_key
            user_prefs.put()
            
        elif mode == 'disable_sync':
            hub = pubSubHubbub(self, user)
            
            subscribe_feed = 'http://buzz.googleapis.com/feeds/%s/public/posted' % user.nickname()
            hub.remove_feed(subscribe_feed)
        
        template_values = {
            'nickname' : user.nickname(),
            'user_prefs': user_prefs,
            }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/config.html')
        html = template.render(path, template_values)
        self.response.out.write(CSRFFilter(self, user).insertCSRFToken(html))
            
    def post(self):
        from csrffilter import CSRFFilter
        
        user = users.get_current_user()

        #CSRF Protection
        filter = CSRFFilter(self, user)
        if not filter.checkCSRFToken():
            return filter.redirectCSRFWarning()

        user_prefs_query = UserPrefs.all()
        user_prefs_query.filter("google_id =", user)
        user_prefs = user_prefs_query.get()
        
        template_values = {
            'nickname': user.nickname(),
            'user_prefs': user_prefs,
            }
        
        path = os.path.join(os.path.dirname(__file__), 'templates/config.html')
        self.response.out.write(template.render(path, template_values))

#Callback Page
class CallbackPage(webapp.RequestHandler):
    def get(self, callback_key):
        from pubsubhubbub import pubSubHubbub
        hub = pubSubHubbub(self, None, callback_key)
        self.response.out.write(hub.receive_feeds('GET'))
        
    def post(self, callback_key):
        from pubsubhubbub import pubSubHubbub
        hub = pubSubHubbub(self, None, callback_key)
        self.response.out.write(hub.receive_feeds('POST'))

#Feed Page
class FeedPage(webapp.RequestHandler):
    def get(self):
        #from google.appengine.api import memcache
        import feedparser
        import google_url_shortner_api
        
        logging.debug('Starting feed taskqueue.')
        session_id = self.request.get('session_id')
        data = memcache.get('feed_%s' % session_id)
        if data is not None:
            logging.debug('Memcache receive success.')
            logging.debug(data)
            
            user_prefs_query = UserPrefs.all()
            user_prefs_query.filter('callback_key =', data['callback_key'])
            user_prefs = user_prefs_query.get()
            if user_prefs is not None:
                logging.info('Google Account: %s' % user_prefs.google_id.nickname())
                feed = feedparser.parse(data['feed'])
                logging.debug(feed)
                
                entry_count = 0
                for entry in feed['entries']:
                    if entry_count > 3:
                        logging.info('Entry count over capacity. count: %s' % len(feed['entries']))
                        break;
                    
                    tweet = entry['summary']
                    logging.info('Raw Tweet: %s' % tweet)
                    bitly_link = ''
                    logging.debug(entry)
                    logging.debug(entry['link'])
                    checked_link = []
                    for link in entry['links']:
                        if link['type'] == 'image/jpeg':
                            if not link['href'] in checked_link:
                                bitly_link = bitly_link + ' ' + google_url_shortner_api.short(link['href'])
                                checked_link.append(link['href'])
                    if entry.get('media_player'):
                        if not entry['media_player']['url'] in checked_link:
                            bitly_link = bitly_link + ' ' + google_url_shortner_api.short(entry['media_player']['url'])
                            checked_link.append(entry['media_player']['url'])
                        
                    #tweet = tweet.encode('utf-8')
                    tweet = tweet.replace('\r\n', '\n')
                    tweet = tweet.replace('\r', '\n')
                    tweet = tweet.replace('\n', '')
                    #tweet = unicode(tweet, 'utf-8')
                    
                    short_link_length = 21
                    twitter_max_length = 140
                    link_length = short_link_length * len(checked_link)
                    tweet_length = len(tweet)
                    logging.debug('Link length: %s' % link_length)
                    logging.debug('Tweet length: %s' % tweet_length)
                    if (tweet_length + link_length) > twitter_max_length:
                        limit_tweet_length = (tweet_length - twitter_max_length) + link_length
                        limit_tweet_length = tweet_length - limit_tweet_length - 3
                        tweet = tweet[0:limit_tweet_length]
                        tweet = tweet + '...' + bitly_link
                        logging.info('Limited Tweet: %s' % tweet)
                        logging.info('Limited Tweet Length: %s' % len(tweet))
                    else:
                        tweet = tweet + bitly_link
                        
                    tweet = tweet.encode('utf-8')
                    logging.info('Tweet: %s' % tweet)
                    if user_prefs.oauth_access_token_key is not None:
                        oauth_access_token = OAuthAccessToken.get_by_key_name(user_prefs.oauth_access_token_key.key().name())
                        if oauth_access_token is not None:
                            logging.info('Twitter Account: %s' % user_prefs.oauth_access_token_key.specifier)
                            try:
                                client = OAuthClient('twitter', self)
                                client.token = oauth_access_token
                                client.post('/statuses/update', status=tweet)
                            except Exception, error:
                                logging.error('Tweet Failed: %s' % error)
                    
                    entry_count = entry_count + 1
            else:
                logging.error('Callback_key not found.')
        else:
            logging.error('Memcache receive failed.')

#Logout Page
class LogoutPage(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url('/')
        
        self.redirect(logout_url)

#Error Page
class ErrorPage(webapp.RequestHandler):
    def get(self):
        from stripper import Stripper
        
        stripper = Stripper()
        
        error = stripper.strip(self.request.get('error'))

        template_values = {
            'error': error
            }
            
        if error == 'csrf':
            template_path = 'templates/error_csrf.html'
        else:
            template_path = 'templates/error.html'
            
        path = os.path.join(os.path.dirname(__file__), template_path)
        self.response.out.write(template.render(path, template_values))
    
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/home', HomePage),
                                      ('/config', ConfigPage),
                                      ('/callback/(.*)', CallbackPage),
                                      ('/feed', FeedPage),
                                      ('/logout', LogoutPage),
                                      ('/error', ErrorPage)],
                                     debug=False)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()
