#!/usr/bin/env python
#
# Copyright 2014 Timothy Sutton
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import plistlib

from autopkglib import Processor, ProcessorError

try:
    from urllib.parse import urlopen  # For Python 3
except ImportError:
    from urllib2 import urlopen  # For Python 2

__all__ = ["HairerSoftUpdateInfoProvider"]

BASE_URL = "http://www.hairersoft.com/Downloads/"
VALID_PRODUCTS = ['AmadeusPro2', 'AmadeusLite']

class HairerSoftUpdateInfoProvider(Processor):
    """Downloads a URL and performs a regular expression match on the text."""

    input_variables = {
        "product_name": {
            "description": "Valid app names are: %s." % ", ".join(VALID_PRODUCTS),
            "required": True,
        },
    }
    output_variables = {
        "url": {
            "description": "Download URL."
        }
    }

    description = __doc__

    def get_meta_plist(self, product_name):
        url = BASE_URL + product_name + ".plist"
        try:
            urlfd = urlopen(url)
            plist_data = urlfd.read()
            urlfd.close()
        except BaseException as e:
            raise ProcessorError("Could not download HairerSoft metadata plist, error: %s" % e)

        httpcode = urlfd.getcode()
        if httpcode != 200:
            raise ProcessorError("Got HTTP error %s trying to download URL %s" % (
                httpcode, url))

        try:
            plist = plistlib.readPlistFromString(plist_data)
        except BaseException as e:
            raise ProcessorError("Error parsing metadata plist! Error: %s" % e)

        return plist

    def main(self):
        product = self.env.get("product_name")
        if product not in VALID_PRODUCTS:
            raise ProcessorError("Invalid product name '%s'! Must be one of: %s" %
                (product, ", ".join(VALID_PRODUCTS)))
        plist = self.get_meta_plist(product)

        if "productURL" in plist.keys():
            self.env["url"] = plist["productURL"]
            self.output("Got URL %s from metadata plist." % self.env["url"])
        else:
            raise ProcessorError("Expected 'productURL' key in metadata plist, but not found!")


if __name__ == '__main__':
    processor = HairerSoftUpdateInfoProvider()
    processor.execute_shell()
