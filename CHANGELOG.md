Changelog
---------

4.1.1 (2021-06-08)

- Fix `Spreadsheet.make_batch_request`'s response handling.

4.1.0 (2020-03-06)

- Add `Spreadsheet.make_batch_request` method.

4.0.0 (2020-02-14)

- Send numbers to the API instead of strings.

3.2.2 (2020-02-05)

- Retry all HTTP 429 errors.

3.2.1 (2019-11-11)

- Handle new Google Sheets 100s error message.

3.2.0 (2019-07-26)

- Add `clear` method to `view.View`.

3.1.4 (2019-04-04)

- Relax requirements in `setup.py`.

3.1.3 (2019-02-27)

- Add read timeouts to retryable exceptions.

3.1.2 (2019-02-19)

- Increase maximum retry time to 200 seconds.

3.1.1 (2018-11-29)

- Retry for a maximum amount of time instead of a maximum number of requests.

3.1.0 (2018-10-24)

- Use `google-auth` in place of `oauth2client`

3.0.0 (2017-MM-DD)

- Added Python 3.3+ support.
- Switched to Sheets API v4.

2.1.2 (2017-04-21)

- Dropped Python 2.6 support.
- Disallow oauth2client 4.x to avoid warnings.
- Follow PEP8 coding style.

2.1.1 (2016-07-04)

- Support oauth2client v2.0.0+.

2.1.0 (2015-10-28)

- Worksheets emulate standard lists better.
- Support Python 2.6.
- Bugfixes.

2.0.0 (2015-08-14)

- First stable release with 100% test coverage.

1.x

- Beta releases.
