from datetime import datetime
from functools import update_wrapper
from werkzeug.routing import Map, Rule
from delikat.store import Store

urls = Map([
    Rule('/_/save', endpoint='save_link', methods=['GET', 'POST']),
    Rule('/_/help', endpoint='help', methods=['GET']),
    Rule('/<user>/', endpoint='user_tag', methods=['GET']),
    Rule('/<user>/<tag>', endpoint='user_tag', methods=['GET']),
])

def handler(ctx):
    handler_name = '%s_%s' % (ctx.request.method.lower(),
                              ctx.endpoint)
    handler = globals()[handler_name]
    handler(ctx, **ctx.url_values)

def page(f):
    def wrapper(ctx, *args, **kwargs):
        with Store() as ctx.store:
            f(ctx, *args, **kwargs)
    update_wrapper(wrapper, f)
    return wrapper

def template_links(links):
    'Modify list of links with values used by templates.'
    last_date = None
    for link in links:
        link['stamp'] = datetime.utcfromtimestamp(link['stamp'])
        link['date'] = link['stamp'].strftime('%e. %b %Y')
        if link['date'] == last_date:
            link['date'] = None
        else:
            last_date = link['date']
    return links

@page
def get_user_tag(ctx, user, tag=None):
    tags = tag.split('+') if tag else None
    ctx.values['links'] = \
        template_links(ctx.store.get_latest_links(user=user, tags=tags))
    ctx.values['all_tags'] = ctx.store.get_user_tags(user, tags=[])
    ctx.values['related_tags'] = ctx.store.get_user_tags(user, tags=tags)

@page
def get_save_link(ctx):
    url = ctx.request.args.get('url', '')
    values = ctx.store.get_user_link(ctx.user, url)
    values = values or {
        'url': url,
        'title': ctx.request.args.get('title'),
    }
    ctx.values.update(values)

@page
def post_save_link(ctx):
    # FIXME - We need a form validation library.
    values = {
        '_id': ctx.request.form.get('_id'),
        'url': ctx.request.form['url'],
        'title': ctx.request.form['title'],
        'description': ctx.request.form.get('description', ''),
        'tags': ctx.request.form['tags'].split(),
    }
    ctx.store.queue_save_link(ctx.user, values)
    ctx.values['notice'] = 'Ok.'

bookmarklet = '''
    javascript:(function() {
        f = '__save_url__'
          + '?url=' + encodeURIComponent(window.location.href)
          + '&title=' + encodeURIComponent(document.title);
        window.open(f, 'location=yes,links=no,scrollbars=no,' +
                       'toolbar=no,width=550,height=550');
    })();
'''

@page
def get_help(ctx):
    save_url = ctx.adapter.build('save_link', force_external=True)
    ctx.values['bookmarklet'] = \
        ''.join(bookmarklet.split()).replace('__save_url__', save_url)
