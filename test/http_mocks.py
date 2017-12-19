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

import hashlib
import json
import logging
import os
import random

import googleapiclient.errors
import httplib2
import hyou.py3
import hyou.util
from six.moves.urllib import parse


RECORDS_DIR = os.path.join(os.path.dirname(__file__), 'records')

ENV_RECORD = os.environ.get('HYOU_TEST_RECORD')


def _canonicalize_uri(uri):
    scheme, netloc, path, params, query, fragment = parse.urlparse(uri)
    if query:
        query = parse.urlencode(sorted(parse.parse_qsl(query)))
    return parse.urlunparse((scheme, netloc, path, params, query, fragment))


def _canonicalize_json(body_json):
    # body_json can be bytes or str.
    if isinstance(body_json, hyou.py3.str):
        json_str = body_json
    else:
        json_str = body_json.decode('utf-8')
    json_data = json.loads(json_str)
    canonicalized_json_binary = json.dumps(
        json_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return canonicalized_json_binary


def _build_signature(method, uri, body):
    sig = '%s %s' % (method, _canonicalize_uri(uri))
    if body is not None:
        sig += ' %s' % hashlib.sha1(_canonicalize_json(body)).hexdigest()
    return sig


def _load_records():
    records = {}
    for filename in sorted(os.listdir(RECORDS_DIR)):
        record_path = os.path.join(RECORDS_DIR, filename)
        with hyou.py3.open(record_path, 'r', encoding='utf-8') as f:
            record = json.load(f)
            record['_path'] = record_path
            body_bytes = (
                record['request'].encode('utf-8')
                if record['request']
                else None)
            sig = _build_signature(
                method=record['method'],
                uri=record['uri'],
                body=body_bytes)
            assert sig not in records, 'dup response: %s' % filename
            records[sig] = record
    return records


def _make_ok_response():
    return httplib2.Response({'status': 200})


class ReplayHttp(object):

    def __init__(self, json_name):
        if not json_name:
            self._real_http = None
        else:
            json_path = os.path.join(
                os.path.dirname(__file__), 'creds', json_name)
            with hyou.py3.open(json_path, 'r') as f:
                credentials = hyou.util.parse_credentials(f.read())
            self._real_http = credentials.authorize(httplib2.Http())
        self._records = _load_records()

    def request(self, uri, method='GET', body=None, *args, **kwargs):
        sig = _build_signature(method=method, uri=uri, body=body)

        if sig in self._records:
            record = self._records[sig]
            logging.info('Returning a recorded response: %s', record['_path'])
            response_body = record['response'].encode('utf-8')
            return (_make_ok_response(), response_body)

        if ENV_RECORD != '1':
            logging.info('Response not available!')
            logging.info('Requested: %s', sig)
            for s in sorted(self._records.keys()):
                logging.info('Candidate: %s', s)
            if self._real_http:
                logging.info(
                    'If this test issues new requests, run unit tests with '
                    'HYOU_TEST_RECORD=1.')
            raise Exception('Response not available')

        response_headers, response_body = self._real_http.request(
            uri, method, body, *args, **kwargs)
        if response_headers.status != 200:
            raise Exception(
                'Got status=%d: %s' % (response_headers.status, response_body))

        record = {
            'method': method,
            'uri': uri,
            'request': body,
            'response': response_body.decode('utf-8'),
        }
        sig_hash = hashlib.sha1(sig.encode('utf-8')).hexdigest()
        record_path = os.path.join(RECORDS_DIR, '%s.json' % sig_hash)
        with open(record_path, 'w') as f:
            json.dump(record, f)

        logging.info('Recorded a response: %s', record_path)

        record['_path'] = record_path
        self._records[sig] = record

        # Do not return |response_headers| for consistency on replay.
        return (_make_ok_response(), response_body)


class ErrorHttp(ReplayHttp):

    rate_error_dict = {
        'error': {
            'code': 429,
            'errors': [{
                'domain': 'global',
                'message': "Insufficient tokens for quota 'ReadGroup' "
                           "and limit 'USER-100s' of service "
                           "'sheets.googleapis.com' for consumer "
                           "'project_number:1234'.",
                'reason': 'rateLimitExceeded'
            }],
            'message': "Insufficient tokens for quota 'ReadGroup' and limit "
                       "'USER-100s' of service 'sheets.googleapis.com' for "
                       "consumer 'project_number:19957049059'.",
            'status': 'RESOURCE_EXHAUSTED'}
    }

    def __init__(self, json_name, num_errors):
        self.num_errors = num_errors
        self.request_num = 0
        super(ErrorHttp, self).__init__(json_name)

    def request(self, uri, method='GET', body=None, *args, **kwargs):
        """Raise a random error until we reach `num_errors` calls."""
        self.request_num += 1
        if self.request_num <= self.num_errors:
            random.choice([self.rate_error, self.server_error])()
        else:
            return super(ErrorHttp, self).request(
                uri, method, body, *args, **kwargs)

    @staticmethod
    def rate_error():
        error_code = 429
        error_content = json.dumps(ErrorHttp.rate_error_dict).encode('utf8')
        response = httplib2.Response({'status': error_code})
        raise googleapiclient.errors.HttpError(response, error_content)

    @staticmethod
    def server_error():
        error_code = random.randint(500, 599)
        response = httplib2.Response({'status': error_code})
        raise googleapiclient.errors.HttpError(response, b'')
