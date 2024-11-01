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

import os
import random

import hyou


def test_integration():
    json_path = os.path.join(
        os.path.dirname(__file__), 'creds', 'unittest-sheets.json')
    collection = hyou.login(json_path)

    spreadsheet = collection['1AJSfI3vDtb0CI4EPO9UnJ3Sg1D5ii33_t4qI2jl59SQ']

    print('Running tests with %s ...' % spreadsheet.url)

    worksheet_title = 'sheet%08d' % random.randrange(100000000)
    worksheet = spreadsheet.add_worksheet(worksheet_title, rows=20, cols=10)

    print('Created %s' % worksheet_title)

    try:
        print('Testing...')

        assert worksheet.title == worksheet_title
        assert worksheet.rows == 20
        assert worksheet.cols == 10

        worksheet.rows = 15

        assert worksheet.rows == 15

        view = worksheet.view(start_row=2, end_row=4, start_col=3, end_col=6)

        assert len(view) == 2
        assert len(view[0]) == 3

        view[0][0] = 'a'
        view[0][1:] = ['b', 'c']
        view[-1][:] = ['d', 'e', 'f']
        view.commit()

        assert view[1][1] == 'e'

        worksheet.refresh()
        assert worksheet.view()[3][4] == 'e'

        data_view = worksheet.view()
        data_view[0][0] = '1'
        data_view[0][1] = '2'
        data_view[0][2] = '=A1/B1'
        data_view.commit()
        # We need to refresh the view so the entered formula is replaced by
        # the calculated value
        data_view.refresh()

        formula_view = worksheet.view(
            fetch_params=dict(valueRenderOption='FORMULA')
        )
        assert data_view[0][2] == '0.5'
        assert formula_view[0][2] == '=A1/B1'

        data_view.clear()
        assert all(value == '' for row in data_view for value in row)

    finally:
        spreadsheet.delete_worksheet(worksheet_title)
        print('Removed %s' % worksheet_title)

    print('PASSED!')
