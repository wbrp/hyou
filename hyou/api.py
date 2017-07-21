# Copyright 2017 Google Inc. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import functools
import random
import time

import googleapiclient.discovery
import googleapiclient.errors

from . import schema

SHEETS_API_DISCOVERY_URL = (
    'https://sheets.googleapis.com/$discovery/rest?version=v4')

NUM_RETRIES = 4


def retry_on_server_error(wrapped_func):
    """
    Return a decorator to retry API calls which fail with 50x status codes,
    using an exponential backoff strategy with up to `NUM_RETRIES` retries.
    """

    @functools.wraps(wrapped_func)
    def wrapper(*args, **kwargs):
        partial_func = functools.partial(wrapped_func, *args, **kwargs)
        return _do_exp_backoff(partial_func, NUM_RETRIES)

    return wrapper


def _do_exp_backoff(func, max_num_retries):
    """Call `func` and perform exponential backoff for 50x errors."""
    num_retry = 0
    upper_bound = 0
    while True:
        backoff = random.random() * upper_bound
        time.sleep(backoff)
        try:
            return func()
        except googleapiclient.errors.HttpError as err:
            if err.resp.status >= 500 and num_retry < max_num_retries:
                upper_bound = 2 ^ num_retry
                num_retry += 1
            else:
                raise


class API(object):

    @retry_on_server_error
    def __init__(self, http, discovery=False):
        if discovery:
            self.sheets = googleapiclient.discovery.build(
                'sheets', 'v4', http=http,
                discoveryServiceUrl=SHEETS_API_DISCOVERY_URL)
            self.drive = googleapiclient.discovery.build(
                'drive', 'v2', http=http)
        else:
            self.sheets = googleapiclient.discovery.build_from_document(
                schema.SHEETS_V4, http=http)
            self.drive = googleapiclient.discovery.build_from_document(
                schema.DRIVE_V2, http=http)
