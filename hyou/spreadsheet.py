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

import datetime

from . import api
from . import util
from . import worksheet


SHEET_TYPE_GRID = 'GRID'


class Spreadsheet(util.LazyOrderedDictionary):

    def __init__(self, api, key, entry):
        super(Spreadsheet, self).__init__(self._worksheet_enumerator, None)
        self._api = api
        self._key = str(key)
        self._entry = entry
        self._updated = None
        self._properties = None

    def __repr__(self):
        return str('Spreadsheet(key=%r)') % (self.key,)

    @api.retry_on_server_error
    def refresh(self, entry=None):
        if entry is not None:
            self._entry = entry
        else:
            self._entry = self._api.sheets.spreadsheets().get(
                spreadsheetId=self.key, includeGridData=False).execute()
        self._updated = None
        super(Spreadsheet, self).refresh()

    def add_worksheet(self, title, rows=1000, cols=26):
        new_entry = self._make_single_batch_request(
            'addSheet',
            {
                'properties': {
                    'title': title,
                    'gridProperties': {
                        'rowCount': rows,
                        'columnCount': cols,
                    },
                },
            })
        self.refresh(new_entry)
        return self[title]

    def delete_worksheet(self, title):
        worksheet = self[title]
        new_entry = self._make_single_batch_request(
            'deleteSheet',
            {'sheetId': worksheet.key})
        self.refresh(new_entry)

    @property
    def key(self):
        return self._key

    @property
    def url(self):
        return 'https://docs.google.com/spreadsheets/d/%s/edit' % self.key

    @property
    def title(self):
        self._ensure_entry()
        return self._entry['properties']['title']

    @title.setter
    def title(self, new_title):
        new_entry = self._make_single_batch_request(
            'updateSpreadsheetProperties',
            {
                'properties': {
                    'title': new_title,
                },
                'fields': 'title',
            })
        self.refresh(new_entry)

    @property
    @api.retry_on_server_error
    def updated(self):
        if not self._updated:
            response = self._api.drive.files().get(fileId=self.key).execute()
            self._updated = datetime.datetime.strptime(
                response['modifiedDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
        return self._updated

    @property
    @api.retry_on_server_error
    def properties(self):
        if not self._properties:
            self._properties = self._api.drive.properties().list(fileId=self.key).execute()
        return self._properties


    def _ensure_entry(self):
        if self._entry is None:
            self.refresh()

    def _worksheet_enumerator(self):
        self._ensure_entry()
        for sheet_entry in self._entry['sheets']:
            if sheet_entry['properties']['sheetType'] != SHEET_TYPE_GRID:
                # "Object" worksheet, does not have any cells to manipulate
                continue
            aworksheet = worksheet.Worksheet(self, self._api, sheet_entry)
            yield (aworksheet.title, aworksheet)

    @api.retry_on_server_error
    def _make_single_batch_request(self, method, params):
        request = {
            'requests': [{method: params}],
            'include_spreadsheet_in_response': True,
        }
        response = self._api.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.key, body=request).execute()
        return response['updatedSpreadsheet']


    @classmethod
    def precache_worksheets(cls, api, key, sheets, fetch_params=None):
        fetch_params = fetch_params or {}
        fetch_params['prettyPrint'] = False  # Save space
        request = {
            'dataFilters': [],
            'includeGridData': True,
        }
        requested_range = {}
        for sheet in sheets:
            grid_range = {}

            grid_range['sheetId'] = sheet['sheetId']
            requested_range[sheet['sheetId']] = sheet

            if sheet.get('start_row') is not None:
                grid_range['startRowIndex'] = sheet['start_row']
            if sheet.get('end_row') is not None:
                grid_range['endRowIndex'] = sheet['end_row']
            if sheet.get('start_col') is not None:
                grid_range['startColumnIndex'] = sheet['start_col']
            if sheet.get('end_col') is not None:
                grid_range['endColumnIndex'] = sheet['end_col']

            request['dataFilters'].append({'gridRange': grid_range})

        response = api.sheets.spreadsheets().getByDataFilter(
            spreadsheetId=key, body=request, **fetch_params
        ).execute()

        for sheet in response['sheets']:
            sheet['fetched_properties'] = requested_range[sheet['properties']['sheetId']]
            end_row = sheet['properties']['gridProperties']['rowCount']
            end_col = sheet['properties']['gridProperties']['columnCount']

            sheet['fetched_properties'].setdefault('start_row', 0)
            sheet['fetched_properties'].setdefault('start_col', 0)
            sheet['fetched_properties'].setdefault('end_row', end_row)
            sheet['fetched_properties'].setdefault('end_col', end_col)

        return cls(api, key, response)

