from os import path
from genshi.output import DocType
from genshi.template import MarkupTemplate, TemplateLoader
import shpaml
from StringIO import StringIO

html_begin = '<html xmlns:py="http://genshi.edgewall.org/" \
                    xmlns:xi="http://www.w3.org/2001/XInclude"'
class ShpamlTemplate(MarkupTemplate):
    def __init__(self, f, **kwargs):
        html = shpaml.convert_text(f.read())
        html = html.replace('<html', html_begin)
        print `html`
        html_f = StringIO(html)
        MarkupTemplate.__init__(self, html_f, **kwargs)

template_class = {
    '.shpaml': ShpamlTemplate,
}
class OurTemplateLoader(TemplateLoader):
    '''A Genshi TemplateLoader which understand that different extensions map
    to different template classes.'''
    def load(self, name, cls=MarkupTemplate, relative_to=None):
        _, ext = path.splitext(name)
        cls = template_class.get(ext, cls)
        return TemplateLoader.load(self, name,
                                   cls=cls,
                                   relative_to=relative_to)

here = path.abspath(path.dirname(__file__))
template_root = path.join(here, 'templates')
template_loader = OurTemplateLoader(template_root)
