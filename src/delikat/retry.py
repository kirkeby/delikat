'Retry failed background jobs.'

from store import Store
import jsonlib

def main():
    with Store() as store:
        while True:
            failed = store.redis.lpop('q:failed')
            if not failed:
                break

            failed = jsonlib.read(failed)
            print 'retrying', `failed`
            store.push_queue(failed['queue'],
                             failed['values'])

if __name__ == '__main__':
    main()

