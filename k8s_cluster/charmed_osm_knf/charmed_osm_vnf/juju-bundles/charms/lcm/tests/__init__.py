#!/usr/bin/env python3
# Copyright 2020 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact: legal@canonical.com
#
# To get in touch with the maintainers, please contact:
# osm-charmers@lists.launchpad.net
##

"""Init mocking for unit tests."""

import sys


import mock


class OCIImageResourceErrorMock(Exception):
    pass


sys.path.append("src")

oci_image = mock.MagicMock()
oci_image.OCIImageResourceError = OCIImageResourceErrorMock
sys.modules["oci_image"] = oci_image
sys.modules["oci_image"].OCIImageResource().fetch.return_value = {}
