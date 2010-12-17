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

@page
def get_user_index(ctx, user):
    ctx.values['links'] = ctx.store.latest_user_links(user)

@page
def get_user_tag(ctx, user, tag):
    ctx.values['links'] = ctx.store.latest_user_links(user, tags=[tag])
