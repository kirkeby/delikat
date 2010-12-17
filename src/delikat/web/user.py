from functools import update_wrapper
from werkzeug.routing import Map, Rule
from delikat.store import Store

urls = Map([
    Rule('/', endpoint='index', methods=['GET']),
])

def handler(ctx):
    handler_name = '%s_%s' % (ctx.request.method.lower(),
                              ctx.endpoint)
    handler = globals()[handler_name]
    handler(ctx)

def page(f):
    def wrapper(ctx, *args, **kwargs):
        with Store() as ctx.store:
            f(ctx, *args, **kwargs)
    update_wrapper(wrapper, f)
    return wrapper

@page
def get_index(ctx):
    ctx.values['links'] = ctx.store.latest_user_links('sune')
