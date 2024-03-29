'Delikat background worker process.'

from store import Store

def main():
    with Store() as store:
        while True:
            new_link = store.pop_queue('new-link')
            try:
                store.do_save_link(new_link)
            except Exception:
                store.push_queue('failed', {
                    'queue': 'new-link',
                    'values': new_link,
                })
                raise

if __name__ == '__main__':
    main()
