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

import datetime
import time
import unittest

import googleapiclient.errors
import hyou.api
import hyou.collection
import mock
import nose.tools

import http_mocks


CREDENTIALS_FILE = 'unittest-sheets.json'


class SpreadsheetTestBase(unittest.TestCase):

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


class SpreadsheetReadOnlyTest(SpreadsheetTestBase):

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)
        self.spreadsheet = self.collection[
            '11NoixDrkf3GIFaJTbWYccHuNIkgtxIqeyf-oOSBttPA']

    def test_repr(self):
        self.assertEqual(
            str('Spreadsheet('
                'key=\'11NoixDrkf3GIFaJTbWYccHuNIkgtxIqeyf-oOSBttPA\')'),
            repr(self.spreadsheet))

    def test_worksheet_accessors(self):
        # iter()
        self.assertEqual(
            ['Sheet1', 'Sheet2', 'Sheet3'],
            list(self.spreadsheet))
        # len()
        self.assertEqual(3, len(self.spreadsheet))
        # keys()
        self.assertEqual(['Sheet1', 'Sheet2', 'Sheet3'],
                         self.spreadsheet.keys())
        # values()
        values = self.spreadsheet.values()
        self.assertEqual(3, len(values))
        self.assertEqual('Sheet1', values[0].title)
        self.assertEqual('Sheet2', values[1].title)
        self.assertEqual('Sheet3', values[2].title)
        # items()
        items = self.spreadsheet.items()
        self.assertEqual(3, len(items))
        self.assertEqual('Sheet1', items[0][0])
        self.assertEqual('Sheet1', items[0][1].title)
        self.assertEqual('Sheet2', items[1][0])
        self.assertEqual('Sheet2', items[1][1].title)
        self.assertEqual('Sheet3', items[2][0])
        self.assertEqual('Sheet3', items[2][1].title)
        # Indexing by an integer
        self.assertEqual('Sheet1', self.spreadsheet[0].title)
        self.assertEqual('Sheet2', self.spreadsheet[1].title)
        self.assertEqual('Sheet3', self.spreadsheet[2].title)
        # Indexing by a key
        self.assertEqual('Sheet1', self.spreadsheet['Sheet1'].title)
        self.assertEqual('Sheet2', self.spreadsheet['Sheet2'].title)
        self.assertEqual('Sheet3', self.spreadsheet['Sheet3'].title)

    def test_refresh(self):
        self.spreadsheet.refresh()

    def test_url(self):
        self.assertEqual(
            'https://docs.google.com/spreadsheets/d/'
            '11NoixDrkf3GIFaJTbWYccHuNIkgtxIqeyf-oOSBttPA/edit',
            self.spreadsheet.url)

    def test_title(self):
        self.assertEqual('SpreadsheetReadOnlyTest', self.spreadsheet.title)

    def test_updated(self):
        self.assertTrue(
            isinstance(self.spreadsheet.updated, datetime.datetime))


class RetrySpreadsheetReadOnlyTest(RetryTestBase, SpreadsheetReadOnlyTest):
    """Same tests as above, but involving retries on server errors."""

    def setUp(self):
        super(RetrySpreadsheetReadOnlyTest, self).setUp()
        self.error_http.sleep_mock.reset_mock()

    def test_too_many_errors(self):
        original_max_sleep = self.error_http.max_sleep
        self.error_http.max_sleep += 10

        with nose.tools.assert_raises(googleapiclient.errors.HttpError):
            self.test_refresh()

        self.error_http.max_sleep = original_max_sleep


class SpreadsheetReadWriteTest(SpreadsheetTestBase):

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)
        self.spreadsheet = self.collection[
            '1uzMKIenUo_ougmt_yS4qfcBx-q6KGLl6mD06CUI4ppA']

    def test_set_title(self):
        self.spreadsheet.title = 'SpreadsheetReadWriteTest'

    def test_add_delete_worksheet(self):
        worksheet = self.spreadsheet.add_worksheet('Sheet9', rows=2, cols=8)
        self.assertEqual('Sheet9', worksheet.title)
        self.assertEqual(2, worksheet.rows)
        self.assertEqual(8, worksheet.cols)
        self.spreadsheet.delete_worksheet('Sheet9')


class RetrySpreadsheetReadWriteTest(RetryTestBase, SpreadsheetReadWriteTest):
    """Same tests as above, but involving retries on server errors."""

    def setUp(self):
        self.error_http.sleep_mock.reset_mock()
        super(RetrySpreadsheetReadWriteTest, self).setUp()
