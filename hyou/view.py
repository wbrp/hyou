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


from . import api
from . import util


class View(util.CustomMutableFixedList):

    def __init__(self, worksheet, api, start_row, end_row, start_col, end_col,
                 fetch_params=None):
        self._worksheet = worksheet
        self._api = api
        self._start_row = start_row
        self._end_row = end_row
        self._start_col = start_col
        self._end_col = end_col
        self._view_rows = [
            ViewRow(self, row, start_col, end_col)
            for row in range(start_row, end_row)]
        self._input_value_map = {}
        self._cells_fetched = False
        self._queued_updates = []
        self._fetch_params = fetch_params or {}

    def refresh(self):
        self._input_value_map.clear()
        self._cells_fetched = False
        del self._queued_updates[:]

    @api.retry_on_server_error
    def _ensure_cells_fetched(self):
        if self._cells_fetched:
            return
        range_str = util.format_range_a1_notation(
            self._worksheet.title, self._start_row, self._end_row,
            self._start_col, self._end_col)
        response = self._api.sheets.spreadsheets().values().get(
            spreadsheetId=self._worksheet._spreadsheet.key,
            range=range_str,
            **self._fetch_params).execute()
        self._input_value_map = {}
        for i, row in enumerate(response.get('values', [])):
            index_row = self._start_row + i
            for j, value in enumerate(row):
                index_col = self._start_col + j
                self._input_value_map.setdefault((index_row, index_col), value)
        self._cells_fetched = True

    @api.retry_on_server_error
    def clear(self):
        """
        Clear all values of this view.

        All other properties of the contained cells (such as formatting, data
        validation etc.) are left unmodified.
        """
        params = {
            'spreadsheetId': self._worksheet._spreadsheet.key,
            'range': util.format_range_a1_notation(
                self._worksheet.title, self._start_row, self._end_row + 1,
                self._start_col, self._end_col + 1
            )
        }
        self._api.sheets.spreadsheets().values().clear(**params).execute()
        self.refresh()

    @api.retry_on_server_error
    def commit(self):
        if not self._queued_updates:
            return
        request = {
            'data': [
                {
                    'range': util.format_range_a1_notation(
                        self._worksheet.title, row, row + 1, col, col + 1),
                    'majorDimension': 'ROWS',
                    'values': [[value]],
                }
                for row, col, value in self._queued_updates
            ],
            'valueInputOption': 'USER_ENTERED',
            'includeValuesInResponse': False,
        }
        self._api.sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=self._worksheet._spreadsheet.key,
            body=request).execute()
        del self._queued_updates[:]

    def __getitem__(self, index):
        return self._view_rows[index]

    def __setitem__(self, index, new_value):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                raise NotImplementedError('slicing with step is not supported')
            if stop < start:
                stop = start
            if len(new_value) != stop - start:
                raise ValueError(
                    'Tried to assign %d values to %d element slice' %
                    (len(new_value), stop - start))
            for i, new_value_one in zip(range(start, stop), new_value):
                self[i] = new_value_one
            return
        self._view_rows[index][:] = new_value

    def __len__(self):
        return self.rows

    def __iter__(self):
        return iter(self._view_rows)

    def __repr__(self):
        return 'View(%r)' % self._view_rows

    @property
    def rows(self):
        return self._end_row - self._start_row

    @property
    def cols(self):
        return self._end_col - self._start_col

    @property
    def start_row(self):
        return self._start_row

    @property
    def end_row(self):
        return self._end_row

    @property
    def start_col(self):
        return self._start_col

    @property
    def end_col(self):
        return self._end_col


class ViewRow(util.CustomMutableFixedList):

    def __init__(self, view, row, start_col, end_col):
        self._view = view
        self._row = row
        self._start_col = start_col
        self._end_col = end_col

    def __getitem__(self, index):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                raise NotImplementedError('slicing with step is not supported')
            if stop < start:
                stop = start
            return ViewRow(
                self._view, self._row,
                self._start_col + start, self._start_col + stop)
        util.check_type(index, int)
        if index < 0:
            col = self._end_col + index
        else:
            col = self._start_col + index
        if not (self._start_col <= col < self._end_col):
            raise IndexError('Column %d is out of range.' % col)
        if (self._row, col) not in self._view._input_value_map:
            self._view._ensure_cells_fetched()
        return self._view._input_value_map.get((self._row, col), '')

    def __setitem__(self, index, new_value):
        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))
            if step != 1:
                raise NotImplementedError('slicing with step is not supported')
            if stop < start:
                stop = start
            if len(new_value) != stop - start:
                raise ValueError(
                    'Tried to assign %d values to %d element slice' %
                    (len(new_value), stop - start))
            for i, new_value_one in zip(range(start, stop), new_value):
                self[i] = new_value_one
            return
        util.check_type(index, int)
        if index < 0:
            col = self._end_col + index
        else:
            col = self._start_col + index
        if not (self._start_col <= col < self._end_col):
            raise IndexError('Column %d is out of range.' % col)
        if new_value is None:
            new_value = ''
        elif isinstance(new_value, int):
            pass
        elif isinstance(new_value, float):
            pass
        elif isinstance(new_value, bytes):
            # May raise UnicodeDecodeError.
            new_value = new_value.decode('ascii')
        else:
            new_value = str(new_value)
        self._view._input_value_map[(self._row, col)] = new_value
        self._view._queued_updates.append((self._row, col, new_value))

    def __len__(self):
        return self._end_col - self._start_col

    def __iter__(self):
        self._view._ensure_cells_fetched()
        for col in range(self._start_col, self._end_col):
            yield self._view._input_value_map.get((self._row, col), '')

    def __repr__(self):
        return repr(list(self))
