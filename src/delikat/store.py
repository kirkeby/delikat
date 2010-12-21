from itertools import chain
from hashlib import sha1
from time import time
import redis
import jsonlib
import pymongo

from delikat.prelude import grouper

__all__ = ['Store']

class Store(object):
    def __init__(self):
        self.redis = redis.Redis()
        self.mongo = pymongo.connection.Connection()
        self.db = self.mongo.delikat

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    ### queue_ are for the frontend web-app
    def queue_save_link(self, user_key, url, title, description, tags,
                        created=None):
        self.push_queue('new-link', {
            'stamp': created or time(),
            'user': user_key,
            'url': url,
            'title': title,
            'description': description,
            'tags': tags,
        })

    ### get_ are for the frontend web-app
    def get_latest_links(self, filter, count=50):
        return list(self.db.links.find(filter).limit(count).sort('stamp', -1))

    ### do_ are for background workers.
    def do_save_link(self, values):
        if not 'stamp' in values:
            values['stamp'] = time()
        old_values = self.db.links.find_one({'user': values['user'],
                                             'url': values['url']})
        if old_values:
            values['_id'] = old_values['_id']
        self.db.links.save(values)

    ### Various operations related to queues.
    def pop_queue(self, name):
        queue, value = self.redis.blpop('q:' + name)
        return jsonlib.read(value)

    def push_queue(self, name, values):
        self.redis.rpush('q:' + name, jsonlib.write(values))
