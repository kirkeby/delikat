from itertools import chain
from hashlib import sha1
from time import time
import redis
import jsonlib

from delikat.prelude import grouper

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

    ### queue_ are for the frontend web-app
    def queue_save_link(self, user_key, url, title, description, tags,
                        created=None):
        self.redis.rpush('q:new-link', jsonlib.write({
            'stamp': created,
            'user': user_key,
            'url': url,
            'title': title,
            'description': description,
            'tags': tags,
        }))

    ### get_ are for the frontend web-app
    def get_latest_links(self, tags, count=10):
        keys = ['tag:' + tag for tag in tags]
        # FIXME - This tmp key thing sucks. And it should be unique. And tmp.
        self.redis.zinterstore('tmp:search', keys)
        return self.redis.zrange('tmp:search', 1, count, desc=True)

    def get_url_info(self, url_keys, info_buckets):
        '''Get info for each pair of URL and info-bucket.

        For example:

        >>> store.get_url_info(['abc...', 'def...'],
                               [('public', 'public-link-info'),
                                ('private', 'user-link-info:root')])
        [{'id': 'abc...',
          'public': <public-link-info:abc...>,
          'private': <user-link-info:root:abc...>},
         {'id': 'def...',
          'public': <public-link-info:def...>,
          'private': <user-link-info:root:def...>}]
        '''
        bucket_keys, bucket_prefix = zip(*info_buckets)
        info_keys = ['%s:%s' % (prefix, url_key)
                     for url_key in url_keys
                     for prefix in bucket_prefix]
        info_values = [jsonlib.read(json or '{}')
                       for json in self.redis.mget(info_keys)]
        return [dict(chain(zip(bucket_keys, values), [('id', id)]))
                for id, values in zip(url_keys, grouper(3, info_values))]

    ### do_ are for background workers.
    def do_save_url(self, url):
        key = self._url_key(url)
        self.redis.setnx('url:' + key, jsonlib.write({
            'url': url,
            'created': time(),
        }))
        return key

    def do_save_user(self, login):
        self.redis.setnx('user:' + login, jsonlib.write({
            'login': login,
            'created': time(),
        }))
        return login

    def do_remove_tags(self, url_key, tags):
        for tag in tags:
            self.redis.zrem('tag:' + tag, url_key)

    def do_add_tags(self, created, url_key, tags):
        for tag in tags:
            self.redis.zadd('tag:' + tag, url_key, created)

    def do_save_link_user(self, values):
        key = 'user-link-info:%(user)s:%(id)s' % values

        old_values = jsonlib.read(self.redis.get(key) or '{}')
        self.do_remove_tags(values['id'], old_values.get('tags', []))
        self.do_add_tags(values['stamp'], values['id'], values['tags'])

        json = jsonlib.write({
            'created': old_values.get('created', time()),
            'title': values['title'],
            'description': values['description'],
            'tags': values['tags'],
            'stamp': values.get('stamp', time()),
        })
        self.redis.set(key, json)

    def do_save_link(self, values):
        values['id'] = self.do_save_url(values['url'])
        values['tags'] = values['tags'][:]
        values['tags'].append('user:' + values['user'])
        self.do_save_link_user(values)
