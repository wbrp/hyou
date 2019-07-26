# Copyright 2015 Google Inc. All rights reserved
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

import time
import unittest

import googleapiclient.errors
import hyou.api
import hyou.collection
import hyou.util
import mock
import nose.tools

import http_mocks


CREDENTIALS_FILE = 'unittest-sheets.json'


class WorksheetTestBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = hyou.api.API(
            http_mocks.ReplayHttp(CREDENTIALS_FILE),
            discovery=False)


class RetryTestBase(object):

    sleep_patcher = mock.patch('time.sleep')

    @classmethod
    def setUpClass(cls):
        cls.sleep_patcher.start()
        sleep_mock = time.sleep
        # Use an ErrorHttp that returns errors up until the last retry
        cls.error_http = http_mocks.ErrorHttp(
            CREDENTIALS_FILE,  hyou.api.MAX_WAIT_TIME-1, sleep_mock)
        cls.api = hyou.api.API(cls.error_http, discovery=False)

    @classmethod
    def tearDownClass(cls):
        cls.sleep_patcher.stop()


class WorksheetReadOnlyTest(WorksheetTestBase):

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)
        self.spreadsheet = self.collection[
            '1ZeOz9HFMJaS4GhZNAdr1Lb-326zVF0c7IG1RL9btlVI']
        self.worksheet1 = self.spreadsheet['Sheet1']

    def test_title(self):
        self.assertEqual('Sheet1', self.worksheet1.title)

    def test_rows(self):
        self.assertEqual(2, self.worksheet1.rows)

    def test_cols(self):
        self.assertEqual(5, self.worksheet1.cols)

    def test_repr(self):
        self.assertEqual(str('Worksheet(key=0)'), repr(self.worksheet1))

    def test_view(self):
        self.worksheet1.view(start_row=3)
        self.worksheet1.view(end_row=-1)
        self.worksheet1.view(start_row=1, end_row=0)
        self.worksheet1.view(start_col=6)
        self.worksheet1.view(end_col=-1)
        self.worksheet1.view(start_col=1, end_col=0)


class RetryWorksheetReadOnlyTest(RetryTestBase, WorksheetReadOnlyTest):
    """Same tests as above, but involving retries on server errors."""

    def setUp(self):
        super(RetryWorksheetReadOnlyTest, self).setUp()
        self.error_http.sleep_mock.reset_mock()


class WorksheetReadWriteTest(WorksheetTestBase):

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)
        self.spreadsheet = self.collection[
            '1IWcyjDQhL0X8wdb1BZFAigJJ7WpBpmbgDrw1zQxyUHI']
        self.worksheet1 = self.spreadsheet['Sheet1']

    def test_set_title(self):
        self.worksheet1.title = 'Sheet1'

    def test_set_size(self):
        self.worksheet1.set_size(2, 5)

    def test_set_rows(self):
        self.worksheet1.rows = 2

    def test_set_cols(self):
        self.worksheet1.cols = 5


class RetryWorksheetReadWriteTest(RetryTestBase, WorksheetReadWriteTest):
    """Same tests as above, but involving retries on server errors."""

    def setUp(self):
        super(RetryWorksheetReadWriteTest, self).setUp()
        self.error_http.sleep_mock.reset_mock()

    def test_too_many_errors(self):
        original_max_sleep = self.error_http.max_sleep
        self.error_http.max_sleep += 10

        with nose.tools.assert_raises(googleapiclient.errors.HttpError):
            self.test_set_size()

        self.error_http.max_sleep = original_max_sleep
