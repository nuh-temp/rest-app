#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging
import time
from google.appengine.api import taskqueue
from google.appengine.ext import deferred

from server.main import app

def run_task():
  t_last = int(time.time())
  while True:
    t_now = int(time.time())
    if t_now >= t_last + 10:
      logging.info('alive')
      t_last = t_now

@app.http_get('/')
def get(handler):
  handler.response.write('Hello world!')

@app.http_get('/run_task')
def get(handler):
  deferred.defer(run_task, _name='task11111')

@app.http_get('/queue_stat')
def get(handler):
  stat = taskqueue.Queue().fetch_statistics()
  logging.info('stat: %s', stat)

def handle_500(request, response, exception):
  logging.exception(exception)
  response.write('A server error occurred!')
  response.set_status(500)

app.error_handlers[500] = handle_500

app.InitHandlers('server.handlers', ['api'])