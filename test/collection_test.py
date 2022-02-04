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


import unittest

import hyou.api
import hyou.collection

from . import http_mocks


class CollectionReadOnlyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = hyou.api.API(
            http_mocks.ReplayHttp('unittest-collection.json'),
            discovery=False)

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)

    def test_accessors_with_constructor(self):
        # Indexing by a key
        self.collection['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks']
        with self.assertRaises(Exception):
            self.collection['invalidkey']

    def test_accessors_with_enumerator(self):
        # iter()
        self.assertEqual(
            ['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
             '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY'],
            sorted(list(self.collection)))
        # len()
        self.assertEqual(2, len(self.collection))
        # keys()
        self.assertEqual(
            ['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
             '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY'],
            sorted(self.collection.keys()))
        # values()
        self.assertEqual(
            ['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
             '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY'],
            sorted(value.key for value in self.collection.values()))
        # items()
        self.assertEqual(
            ['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
             '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY'],
            sorted(key for key, value in self.collection.items()
                   if key == value.key))
        # Indexing by an integer
        value0 = self.collection[0]
        value1 = self.collection[1]
        self.assertEqual(
            ['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
             '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY'],
            sorted([value0.key, value1.key]))
        # Indexing by a key
        self.assertEqual(
            '1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks',
            self.collection['1BrbtLTiRzl_-sFJE9CjC9AFbpN7lizByyIqy3lRwkks']
            .key)
        self.assertEqual(
            '1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY',
            self.collection['1teBUg2ZcY1N1QLimcIXOliC6mL1O6G4mxPQCCbhj1eY']
            .key)


class CollectionReadWriteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = hyou.api.API(
            http_mocks.ReplayHttp('unittest-collection-write.json'),
            discovery=False)

    def setUp(self):
        self.collection = hyou.collection.Collection(self.api)

    def test_create_spreadsheet(self):
        self.collection.create_spreadsheet('Test', rows=10, cols=10)
