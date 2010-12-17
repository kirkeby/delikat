import lxml.etree
from time import mktime, strptime

from store import Store

def import_delicious_dump(store, f, username):
    doc = lxml.etree.parse(f)

    user_key = store.save_user(username)

    for post in doc.xpath('//post'):
        url = post.get('href')
        title = post.get('description')
        description = post.get('extended')
        tags = post.get('tag').split()

        created = mktime(strptime(post.get('time'), '%Y-%m-%dT%H:%M:%SZ'))

        store.save_link(user_key, url, title, description, tags, created)

if __name__ == '__main__':
    import sys
    with Store() as store:
        import_delicious_dump(store, sys.stdin, u'sune')
