import logging
import random
import time
import threading
import Queue

import json as simplejson

import webapp2
from webapp2_extras import routes

from google.appengine.api import background_thread
from google.appengine.api import taskqueue

_ACTIONS = ['add', 'remove']


class Index(webapp2.RequestHandler):

  limit = 100
  count = 0

  @classmethod
  def IncCount(cls, increment=1):
    cls.count += increment

  @classmethod
  def GetCount(cls):
    return cls.count

  def get(self):
    q = taskqueue.Queue('pullq')

    for n in xrange(self.limit):
      now = time.time()
      action = random.choice(_ACTIONS)
      payload = simplejson.dumps({
          'time': now,
          'num': self.GetCount(),
      })
      self.IncCount()
      logging.info('--- add to q: %s', action)
      q.add(taskqueue.Task(payload=payload, method='PULL', tag=action))

    self.response.write('Threads Index Page. (%s)' % now)


class Worker(webapp2.RequestHandler):

  _indexer = None

  @classmethod
  def _AddReqHandler(cls, payloads):
    for payload in payloads:
      now = time.time()
      logging.info('--> ADD payload: %s', [now, payload])

  @classmethod
  def _RemoveReqHandler(cls, payloads):
    for payload in payloads:
      now = time.time()
      logging.info('--> REMOVE payload: %s', [now, payload])

  @classmethod
  def _ProcessReq(cls, q, tag, handler):
    try:
      tasks = q.lease_tasks_by_tag(3600, 1000, deadline=60, tag=tag)
    except (taskqueue.TransientError,
            apiproxy_errors.DeadlineExceededError) as e:
      logging.exception(e)
      return

    if tasks:
      handler([simplejson.loads(task.payload) for task in tasks])
      q.delete_tasks(tasks)

  @classmethod
  def StartIndexer(cls):
    cnt = 0
    q = taskqueue.Queue('pullq')
    while True:
      logging.info('tick %s', cnt)
      cnt += 1
      cls._ProcessReq(q, 'add', cls._AddReqHandler)
      cls._ProcessReq(q, 'remove', cls._RemoveReqHandler)

      time.sleep(1)

  def get(self):
    if self._indexer is not None and self._indexer.isAlive():
      return
    self._indexer = background_thread.BackgroundThread(
        target=self.StartIndexer)
    self._indexer.daemon = True
    self._indexer.start()
    logging.info('Indexer has been started: %s', id(self._indexer))


ROUTES = [
  routes.PathPrefixRoute('/threads', [
    routes.RedirectRoute('/', Index, 'index', strict_slash=True),
  ]),
  routes.RedirectRoute('/_ah/start', Worker, 'worker', strict_slash=True),
]

app = webapp2.WSGIApplication(ROUTES, debug=True)