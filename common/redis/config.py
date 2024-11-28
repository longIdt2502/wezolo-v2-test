from redis import Redis
from rq import Queue

redis_conn = Redis(host='localhost', port=6379)
task_queue = Queue('task_queue', connection=redis_conn)
