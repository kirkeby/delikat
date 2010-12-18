import lxml.etree
from time import mktime, strptime

from store import Store

def import_delicious_dump(store, f, username):
    doc = lxml.etree.parse(f)

    user_key = store.do_save_user(username)

    for post in doc.xpath('//post'):
        url = post.get('href')
        title = post.get('description')
        description = post.get('extended')
        tags = post.get('tag').split()

        stamp = mktime(strptime(post.get('time'), '%Y-%m-%dT%H:%M:%SZ'))

        store.do_save_link({
            'stamp': stamp,
            'user': user_key,
            'url': url,
            'title': title,
            'description': description,
            'tags': tags,
        })

if __name__ == '__main__':
    import sys
    with Store() as store:
        import_delicious_dump(store, sys.stdin, u'sune')
