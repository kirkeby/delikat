from itertools import chain, groupby
from hashlib import sha1
from time import time
import redis
import json
import pymongo
from pymongo.objectid import ObjectId
from pymongo.errors import OperationFailure
from pymongo import json_util

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

    def get_popular_links(self, count=50):
        return list(self.db.popular.find().limit(count).sort('count', -1))

    ### user accounts
    def get_user_for_openid(self, openid):
        return self.db.users.find_one({'openid': openid})

    def register_user(self, login, openid):
        try:
            return self.db.users.insert({'login': login, 'openid': openid},
                                        safe=True)
        except OperationFailure:
            # Ought to check that the failure really is a unique-index error.
            return None

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
            values['_id'] = ObjectId(old_values['_id'])
            values['stamp'] = old_values['stamp']
        elif '_id' in values:
            del values['_id']
        self.db.links.save(values)

    ### Various operations related to queues.
    def pop_queue(self, name):
        queue, value = self.redis.blpop('q:' + name)
        return json.loads(value, object_hook=json_util.object_hook)

    def push_queue(self, name, values):
        wire = json.dumps(values, default=json_util.default)
        self.redis.rpush('q:' + name, wire)

def main():
    with Store() as store:
        exists = store.db.collection_names()
        for coll in ['links', 'users']:
            if coll not in exists:
                store.db.create_collection(coll)

        store.db.links.ensure_index([('user', 1), ('url', 1)],
                                    unique=True)

        store.db.users.ensure_index([('login', 1)], unique=True)
        store.db.users.ensure_index([('openid', 1)], unique=True)

if __name__ == '__main__':
    main()
