import web
from store import Store

urls = [
    '/', 'index',
]
app = web.application(urls, globals())

class index:
    def GET(self):
        with Store() as store:
            links = '<li>'.join(link['url']
                                for link in store.latest_user_links('sune'))
        return '<html><body><ul>' + links

if __name__ == '__main__':
    app.run()
