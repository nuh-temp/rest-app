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


class IndexPage(webapp2.RequestHandler):

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


class Indexer(background_thread.BackgroundThread):

  def __init__(self):
    super(Indexer, self).__init__()
    self.daemon = True
    self._q = taskqueue.Queue('pullq')
    self.start()

  def _AddReqHandler(self, payloads):
    for payload in payloads:
      now = time.time()
      logging.info('--> ADD payload: %s', [now, payload])

  def _RemoveReqHandler(self, payloads):
    for payload in payloads:
      now = time.time()
      logging.info('--> REMOVE payload: %s', [now, payload])

  def _ProcessReq(self, tag, handler):
    try:
      tasks = self._q.lease_tasks_by_tag(3600, 1000, deadline=60, tag=tag)
    except (taskqueue.TransientError,
            apiproxy_errors.DeadlineExceededError) as e:
      logging.exception(e)
      return

    if tasks:
      handler([simplejson.loads(task.payload) for task in tasks])
      self._q.delete_tasks(tasks)

  def run(self):
    cnt = 0
    while True:
      logging.info('tick %s', cnt)
      cnt += 1
      self._ProcessReq('add', self._AddReqHandler)
      self._ProcessReq('remove', self._RemoveReqHandler)

      time.sleep(1)


class Workers(webapp2.RequestHandler):

  _indexer = None

  def get(self):
    if self._indexer is None or not self._indexer.isAlive():
      self._indexer = Indexer()
      logging.info('Indexer has been started: %s', id(self._indexer))


ROUTES = [
  routes.PathPrefixRoute('/threads', [
    routes.RedirectRoute('/', IndexPage, 'index-page', strict_slash=True),
  ]),
  routes.RedirectRoute('/_ah/start', Workers, 'workers', strict_slash=True),
]

app = webapp2.WSGIApplication(ROUTES, debug=True)