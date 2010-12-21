from werkzeug import Request, Response
from werkzeug.exceptions import HTTPException
from resolver import resolve

from genshi.output import DocType
from delikat.web.templates import template_loader

class Context(object):
    def __init__(self, url_map, environ):
        self.request = Request(environ)
        self.response = Response(mimetype='text/html')
        self.adapter = url_map.bind_to_environ(environ)
        self.endpoint, self.url_values = self.adapter.match()
        self.user = 'sune'
        self.values = {
            'context': self,
        }

class Application(object):
    def __init__(self, url_map, handler):
        self.url_map = url_map
        self.handler = handler

    def __call__(self, environ, start_response):
        response = self.response_for(environ)
        return response(environ, start_response)

    def response_for(self, environ):
        try:
            ctx = Context(self.url_map, environ)
            self.handler(ctx)
            ctx.response.data = self.render(ctx)
            return ctx.response
        except HTTPException, e:
            return e

    def render(self, ctx):
        template = self.template_for(ctx)
        stream = template.generate(
            request=ctx.request,
            response=ctx.response,
            endpoint=ctx.endpoint,
            url_values=ctx.url_values,
            url_for=lambda e, **v: ctx.adapter.build(e, v),
            **ctx.values
        )
        return stream.render('html', doctype=DocType.get('html5'))

    def template_for(self, ctx):
        return template_loader.load(ctx.endpoint + '.shpaml')

def application_factory(global_conf, **local_conf):
    'Paste Script compatible application faactory.'
    url_map = resolve(local_conf['urls'])
    handler = resolve(local_conf['handler'])
    return Application(url_map, handler)
