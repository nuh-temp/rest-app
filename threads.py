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
_ACTION_PRIORITY = {
    'add': 10,
    'remove': 20,
}


class Monitor(threading.Thread):

  _values = set()

  def __init__(self, q):
    super(Monitor, self).__init__()
    logging.info('Init monitor')
    self._q = q

  @classmethod
  def GetMonitor(cls, q):
    m = cls(q)
    m.daemon = True
    m.start()
    return m

  def run(self):
    while True:
      action_p, name, action, item = self._q.get()
      logging.info('item: %s', [name, action, item])

      if action == 'dump':
        logging.info('DUMP: %s', self._values)
      elif action == 'add':
        self._values.add(item)
      elif action == 'remove':
        self._values.discard(item)

      self._q.task_done()
      # time.sleep(0.2)

class Updater(threading.Thread):

  def __init__(self, name, q, limit=10):
    super(Updater, self).__init__(name=name)
    self.daemon = False
    self._q = q
    self.name = name
    self.limit = limit
    logging.info('Init Updater: %s', name)

  def run(self):
    for n in xrange(self.limit):
      action = random.choice(_ACTIONS)
      action_p = _ACTION_PRIORITY[action]
      item = (action_p, self.name, action, random.randrange(self.limit))
      logging.info('put: %s', item)
      self._q.put(item)
      # time.sleep(random.randrange(2, 10) / 10.0)
    logging.info('Done Updater: %s', self.name)


# class BaseHandler(webapp2.RequestHandler):
#   _q = Queue.PriorityQueue()
#   _monitor = Monitor.GetMonitor(_q)


class Index(webapp2.RequestHandler):

  limit = 100
  def get(self):
    logging.info('threads: %s', threading.enumerate())
    q = taskqueue.Queue('pullq')

    for n in xrange(self.limit):
      now = time.time()
      action = random.choice(_ACTIONS)
      payload = simplejson.dumps({
          'time': now,
          'num': n,
      })
      logging.info('--- add to q: %s', action)
      q.add(taskqueue.Task(payload=payload, method='PULL', tag=action))
      # time.sleep(random.randrange(2, 10) / 10.0)

    self.response.write('Threads Index Page. (%s)' % now)


class Dump(webapp2.RequestHandler):

  def get(self):
    self._q.put((1, 'main', 'dump', None))


class Worker(webapp2.RequestHandler):

  worker_thread = None

  @classmethod
  def ProcessAdd(cls, q):
    try:
      tasks = q.lease_tasks_by_tag(3600, 1000, deadline=60, tag='add')
    except (taskqueue.TransientError,
            apiproxy_errors.DeadlineExceededError) as e:
      logging.exception(e)
      return

    if tasks:
      for task in tasks:
        now = time.time()
        payload = simplejson.loads(task.payload)
        logging.info('--> ADD payload: %s', [now, payload, task.tag])
      q.delete_tasks(tasks)

  @classmethod
  def ProcessRemove(cls, q):
    try:
      tasks = q.lease_tasks_by_tag(3600, 1000, deadline=60, tag='remove')
    except (taskqueue.TransientError,
            apiproxy_errors.DeadlineExceededError) as e:
      logging.exception(e)
      return

    if tasks:
      for task in tasks:
        now = time.time()
        payload = simplejson.loads(task.payload)
        logging.info('--> REMOVE payload: %s', [now, payload, task.tag])
      q.delete_tasks(tasks)

  @classmethod
  def inThread(cls):
    cnt = 0
    q = taskqueue.Queue('pullq')
    while True:
      logging.info('tick %s', cnt)
      cnt += 1
      cls.ProcessAdd(q)
      cls.ProcessRemove(q)

      time.sleep(1)

  def get(self):
    if self.worker_thread is not None and self.worker_thread.isAlive():
      return
    self.worker_thread = background_thread.BackgroundThread(target=self.inThread)
    self.worker_thread.daemon = True
    self.worker_thread.start()
    logging.info('thread has been started: %s', [
        id(self.worker_thread),
        self.worker_thread.isDaemon(), self.worker_thread.isAlive()])


ROUTES = [
  routes.PathPrefixRoute('/threads', [
    routes.RedirectRoute('/', Index, 'index', strict_slash=True),
    routes.RedirectRoute('/dump', Dump, 'dump', strict_slash=True),
  ]),
  routes.RedirectRoute('/_ah/start', Worker, 'worker', strict_slash=True),
]

app = webapp2.WSGIApplication(ROUTES, debug=True)