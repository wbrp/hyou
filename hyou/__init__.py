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

from .collection import Collection
from .spreadsheet import Spreadsheet
from .util import SCOPES
from .view import View
from .worksheet import Worksheet

login = Collection.login


__version__ = '4.1.1'

__all__ = [
    'Collection',
    'SCOPES',
    'Spreadsheet',
    'View',
    'Worksheet',
    'login',
]
