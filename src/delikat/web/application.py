import os
from werkzeug import BaseRequest, Response, cached_property
from werkzeug.exceptions import HTTPException
from werkzeug.contrib.securecookie import SecureCookie
from resolver import resolve

from genshi.output import DocType
from genshi.filters import HTMLFormFiller
from delikat.web.templates import template_loader

class Request(BaseRequest):
    @cached_property
    def session(self):
        secret = self.environ['delikat.web.secret']
        return SecureCookie.load_cookie(self, key='auth', secret_key=secret)

class Context(object):
    def __init__(self, url_map, environ):
        self.request = Request(environ)
        self.response = Response(mimetype='text/html')
        self.adapter = url_map.bind_to_environ(environ)
        self.endpoint, self.url_values = self.adapter.match()
        self.values = {
            'context': self,
        }

    @cached_property
    def user(self):
        return self.request.session.get('user')

class Application(object):
    def __init__(self, url_map, handler, secret):
        self.url_map = url_map
        self.handler = handler
        self.secret = secret

    def __call__(self, environ, start_response):
        environ['delikat.web.secret'] = self.secret
        response = self.response_for(environ)
        return response(environ, start_response)

    def response_for(self, environ):
        try:
            ctx = Context(self.url_map, environ)
            self.handler(ctx)
            ctx.response.data = self.render(ctx)
            ctx.request.session.save_cookie(ctx.response,
                                            key='auth',
                                            httponly=True)
            return ctx.response
        except HTTPException, e:
            return e

    def render(self, ctx):
        if ctx.response.status_code <> 200:
            return ctx.response.status
        template = self.template_for(ctx)
        stream = template.generate(
            request=ctx.request,
            response=ctx.response,
            endpoint=ctx.endpoint,
            url_values=ctx.url_values,
            url_for=lambda e, **v: ctx.adapter.build(e, v),
            **ctx.values
        )
        stream = stream | HTMLFormFiller(data=ctx.values)
        return stream.render('html', doctype=DocType.get('html5'))

    def template_for(self, ctx):
        return template_loader.load(ctx.endpoint + '.shpaml')

def load_secret(name):
    if os.path.exists(name):
        secret = open(name, 'rb').read()
    else:
        secret = os.urandom(40)
        open(name, 'wb').write(secret)
    return secret

def application_factory(global_conf, **local_conf):
    'Paste Script compatible application faactory.'
    url_map = resolve(local_conf['urls'])
    handler = resolve(local_conf['handler'])
    app_secret = load_secret(os.path.join(global_conf['here'],
                                          local_conf['secret-file']))
    return Application(url_map, handler, app_secret)
