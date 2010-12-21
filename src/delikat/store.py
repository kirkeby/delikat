from itertools import chain, groupby
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
    def queue_save_link(self, user_key, values):
        values['user'] = user_key
        values['stamp'] = values.get('stamp', time())
        self.push_queue('new-link', values)

    ### get_ are for the frontend web-app
    def get_latest_links(self, user, tags, count=50):
        filter = {'user': user}
        if tags:
            filter['tags'] = {'$all': tags}
        return list(self.db.links.find(filter).limit(count).sort('stamp', -1))

    def get_user_tags(self, user, tags):
        filter = {'user': user}
        if tags:
            filter['tags'] = {'$all': tags}
        links = self.db.links.find(filter, {'tags': 1})
        all_tags = sorted(chain(*(l['tags'] for l in links)),
                          key=lambda s: s.lower())
        return [{'tag': tag, 'count': len(list(tags))}
                for tag, tags in groupby(all_tags)]

    def get_user_link(self, user, url):
        return self.db.links.find_one({'user': user, 'url': url})

    ### do_ are for background workers.
    def _find_old_link(self, values):
        for key in ['_id', 'url']:
            if key not in values:
                continue
            v = self.db.links.find_one({'user': values['user'],
                                        key: values[key]})
            if v:
                return v

    def do_save_link(self, values):
        if not 'stamp' in values:
            values['stamp'] = time()
        old_values = self._find_old_link(values)
        if old_values:
            values['_id'] = str(old_values['_id'])
        elif '_id' in values:
            del values['_id']
        self.db.links.save(values)

    ### Various operations related to queues.
    def pop_queue(self, name):
        queue, value = self.redis.blpop('q:' + name)
        return jsonlib.read(value, use_float=True)

    def push_queue(self, name, values):
        self.redis.rpush('q:' + name, jsonlib.write(values))
