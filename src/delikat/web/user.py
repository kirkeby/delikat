from datetime import datetime
from functools import update_wrapper
from werkzeug.routing import Map, Rule
from delikat.store import Store

from openid.consumer.consumer import Consumer, SUCCESS
from openid.consumer.discover import DiscoveryFailure
from openid.store.filestore import FileOpenIDStore

urls = Map([
    Rule('/', endpoint='index', methods=['GET']),
    Rule('/_/save', endpoint='save_link', methods=['GET', 'POST']),
    Rule('/_/help', endpoint='help', methods=['GET']),
    Rule('/_/login', endpoint='login', methods=['GET', 'POST']),
    Rule('/_/logout', endpoint='logout', methods=['GET']),
    Rule('/_/openid-return', endpoint='openid_return', methods=['GET']),
    Rule('/_/register', endpoint='register', methods=['GET', 'POST']),
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
def get_index(ctx):
    ctx.values['links'] = ctx.store.get_popular_links()

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
    values['tags'] = ' '.join(values.get('tags', []))
    ctx.values.update(values)
    ctx.values.update({
        'saved': False,
        'windowed': ctx.request.form.has_key('w'),
    })

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
    ctx.values.update(values)
    ctx.values.update({
        'saved': True,
        'windowed': ctx.request.form.has_key('w'),
    })

bookmarklet = '''
    javascript: (function() {
        window.open(
            '__save_url__?w=1&url='
            + encodeURIComponent(window.location.href)
            + '&title=' + encodeURIComponent(document.title),
            'delikat',
            'location=yes,links=no,scrollbars=no,toolbar=no,'
            + 'width=550,height=300'
        );
    })();
'''

@page
def get_help(ctx):
    save_url = ctx.adapter.build('save_link', force_external=True)
    ctx.values['bookmarklet'] = \
        ''.join(bookmarklet.split()).replace('__save_url__', save_url)

@page
def get_login(ctx):
    if ctx.user:
        ctx.response.status_code = 302
        ctx.response.location = ctx.adapter.build('user_tag',
                                                  {'user': ctx.user})

def make_consumer(ctx):
    openid_store = FileOpenIDStore('/tmp/openid-store')
    consumer = Consumer(ctx.request.session, openid_store)
    return consumer

@page
def post_login(ctx):
    openid = ctx.request.form['openid']
    if not openid:
        return

    realm = ctx.adapter.build('index', force_external=True)
    return_to = ctx.adapter.build('openid_return', force_external=True)

    try:
        auth_req = make_consumer(ctx).begin(openid)
        redirect_url = auth_req.redirectURL(realm, return_to)

        ctx.response.status_code = 302
        ctx.response.location = redirect_url

    except DiscoveryFailure, e:
        ctx.values['error'] = e.message

    except Exception:
        ctx.values['error'] = 'Something failed.'

@page
def get_openid_return(ctx):
    return_to = ctx.adapter.build('openid_return', force_external=True)
    result = make_consumer(ctx).complete(ctx.request.args, return_to)

    ctx.response.status_code = 302
    if result.status <> SUCCESS:
        ctx.response.location = ctx.adapter.build('login')
        return

    user = ctx.store.get_user_for_openid(result.identity_url)

    if user:
        login = ctx.request.session['user'] = user['login']
        ctx.response.location = ctx.adapter.build('user_tag',
                                                  {'user': login})
    else:
        ctx.request.session['openid'] = result.identity_url
        ctx.response.location = ctx.adapter.build('register')

@page
def get_register(ctx):
    ctx.values['openid'] = ctx.request.session.get('openid', 'imposter')

@page
def post_register(ctx):
    openid = ctx.values['openid'] = ctx.request.session.get('openid')
    if not openid:
        ctx.response.status_code = 302
        ctx.response.location = ctx.adapter.build('login')
        return

    login = ctx.request.form.get('login')
    if ctx.store.register_user(login, openid):
        del ctx.request.session['openid']
        ctx.request.session['user'] = login
        ctx.response.status_code = 302
        ctx.response.location = ctx.adapter.build('user_tag',
                                                  {'user': login})
    else:
        ctx.values['error'] = True

@page
def get_logout(ctx):
    ctx.request.session['user'] = None
    ctx.response.status_code = 302
    ctx.response.location = '/'
