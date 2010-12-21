from datetime import datetime
from functools import update_wrapper
from werkzeug.routing import Map, Rule
from delikat.store import Store

urls = Map([
    Rule('/<user>/', endpoint='user_tag', methods=['GET']),
    Rule('/<user>/<tag>', endpoint='user_tag', methods=['GET']),
    Rule('/l/new', endpoint='new_link', methods=['GET', 'POST']),
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
def get_new_link(ctx):
    pass

@page
def post_new_link(ctx):
    # FIXME - We need a form validation library.
    ctx.store.queue_save_link(ctx.user,
                              ctx.request.form['url'],
                              ctx.request.form['title'],
                              ctx.request.form.get('description', ''),
                              ctx.request.form['tags'].split())
    ctx.values['notice'] = 'Ok.'
