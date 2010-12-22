'Update the list of currently popular links.'

from pymongo.code import Code

from delikat.store import Store

url_mapper = Code('''
    function() {
        emit(this.url, 1);
    }
''')
title_mapper = Code('''
    function() {
        emit(this.title, 1);
    }
''')
tags_mapper = Code('''
    function() {
        for(var i = 0; i < this.tags.length; i++)
            emit(this.tags[i], 1);
    }
''')
reducer = Code('''
    function(key, values) {
        var total = 0;
        for(var i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
''')

def get_url(store, url, count):
    query = {'url': url}
    title = store.db.links.map_reduce(title_mapper, reducer, query=query) \
                .find().sort('value', -1).limit(1)[0]['_id']
    tags = [r['_id'] for r in
            store.db.links.map_reduce(tags_mapper, reducer, query=query) \
                .find().sort('value', -1).limit(5)]
    return {
        'url': url,
        'count': count,
        'title': title,
        'tags': tags,
    }

def main():
    with Store() as store:
        result = store.db.links.map_reduce(url_mapper, reducer)
        for r in result.find().sort('value', -1).limit(100):
            store.db.new_popular.save(get_url(store, r['_id'], r['value']))
        store.db.new_popular.rename('popular', dropTarget=True)

if __name__ == '__main__':
    main()
