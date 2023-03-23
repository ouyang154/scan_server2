import redis

conn = redis.Redis()

conn.delete('context')
conn.delete('detection')