from hashlib import sha1
from time import time
import redis
import jsonlib

__all__ = ['Store']

class Store(object):
    def __init__(self):
        self.redis = redis.Redis()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def _url_key(self, url):
        return sha1(url).hexdigest()

    def save_url(self, url):
        key = self._url_key(url)
        self.redis.setnx('url:' + key, jsonlib.write({
            'url': url,
            'created': time(),
        }))
        return key

    def save_user(self, login):
        self.redis.setnx('user:' + login, jsonlib.write({
            'login': login,
            'created': time(),
        }))
        return login

    def save_link(self, user_key, url, title, description, tags,
                  created=None):
        if created is None:
            created = time()

        url_key = self.save_url(url)

        self.redis.zadd('tag:user:' + user_key, url_key, created)
        # FIXME - Remove old tags first.
        for tag in tags:
            self.redis.zadd('tag:' + tag, url_key, created)

        # Per-user meta-data (title, comments, ..) about links.
        json = jsonlib.write({
            'id': url_key,
            'url': url,
            'title': title,
            'description': description,
            'tags': tags,
        })
        self.redis.set('link-info:%s:%s' % (user_key, url_key), json)

    def latest_user_links(self, user_key, count=10):
        url_keys = self.redis.zrange('tag:user:' + user_key,
                                     1, count, desc=True)
        if not url_keys:
            return []
        link_keys = ['link-info:%s:%s' % (user_key, url_key)
                     for url_key in url_keys]
        return map(jsonlib.read, self.redis.mget(link_keys))
