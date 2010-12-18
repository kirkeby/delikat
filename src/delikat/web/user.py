from functools import update_wrapper
from werkzeug.routing import Map, Rule
from delikat.store import Store

urls = Map([
    Rule('/<user>/', endpoint='user_index', methods=['GET']),
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

def get_latest_links(ctx, info_for, tags):
    '''Get latest links with given tags for current user.

    Return a list of dicts with keys 'public', 'private' and if info_for is
    given also 'other'; each of these contains the information for each link
    saved by the system, by the current user and by the given other user.'''

    info_buckets = [
        ('public', 'url'),
        ('mine', 'user-link-info:' + ctx.user),
        ('here', 'user-link-info:' + ctx.user),
    ]
    url_keys = ctx.store.get_latest_links(tags)
    return ctx.store.get_url_info(url_keys, info_buckets)

@page
def get_user_index(ctx, user):
    ctx.values['links'] = get_latest_links(ctx, user, ['user:' + user])

@page
def get_user_tag(ctx, user, tag):
    ctx.values['links'] = get_latest_links(ctx, user, ['user:' + user, tag])
