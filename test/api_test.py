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

import contextlib
import logging
import unittest

import googleapiclient.errors
import hyou.api
import mock
import nose.tools

import http_mocks


CREDENTIALS_FILE = 'unittest-collection.json'


@contextlib.contextmanager
def suppress_oauth2client_warnings():
    """Suppresses warnings from oauth2client not being available"""
    logger = logging.getLogger('googleapiclient.discovery_cache')
    logger.setLevel(logging.ERROR)
    try:
        yield
    finally:
        logger.setLevel(logging.NOTSET)


class APITest(unittest.TestCase):

    def test_no_discovery(self):
        hyou.api.API(
            http_mocks.ReplayHttp(None),
            discovery=False)

    def test_discovery(self):
        with suppress_oauth2client_warnings():
            hyou.api.API(
                http_mocks.ReplayHttp(CREDENTIALS_FILE),
                discovery=True)

    def test_discovery_retry_on_error(self):
        patcher = mock.patch('time.sleep')  # Makes the following much faster
        patcher.start()

        with suppress_oauth2client_warnings():
            hyou.api.API(
                http_mocks.ErrorHttp(
                    CREDENTIALS_FILE, num_errors=hyou.api.NUM_RETRIES),
                discovery=True)
            with nose.tools.assert_raises(googleapiclient.errors.HttpError):
                hyou.api.API(
                    http_mocks.ErrorHttp(
                        CREDENTIALS_FILE, num_errors=hyou.api.NUM_RETRIES+1),
                    discovery=True)

        patcher.stop()
