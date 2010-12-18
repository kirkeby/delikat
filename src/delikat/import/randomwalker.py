'Importer for dumps from http://randomwalker.info/data/delicious/.'

import re
import jsonlib
from time import mktime, strptime

from delikat.store import Store

clean_user_re = re.compile('[^a-z0-9-_.]', re.I)
time_format = '%a, %d %b %Y %H:%M:%S +0000'

def import_json_dump(store, f):
    for i, line in enumerate(f):
        data = jsonlib.read(line)
        stamp = mktime(strptime(data['updated'],
                                time_format))
        user = clean_user_re.sub('', data['author'])
        user_key = store.do_save_user(user)
        tags = [t['term']
                for t in data.get('tags', [])]
        values = {
            'stamp': stamp,
            'user': user_key,
            'url': data['link'],
            'title': data['title'],
            'description': '',
            'tags': tags,
        }
        store.do_save_link(values)

        if i % 100 == 0:
            print i

if __name__ == '__main__':
    import sys
    with Store() as store:
        import_json_dump(store, sys.stdin)
