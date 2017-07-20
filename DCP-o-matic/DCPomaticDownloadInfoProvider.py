#!/usr/bin/env python
#
# Copyright 2017 Timothy Sutton
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

from autopkglib import Processor, ProcessorError
from urllib import quote

__all__ = ["DCPomaticDownloadInfoProvider"]

VALID_PRODUCTS = ['Batch Converter', 'DCP-o-matic', 'Encode Server', 'KDM Creator']
VALID_CHANNELS = ['stable', 'test']

class DCPomaticDownloadInfoProvider(Processor):
    """Given a channel and product, output a download URL and regex string
    usable by URLTextSearcher to find the download."""
    input_variables = {
        "app": {
            "description": "Valid names are: %s." % ", ".join(VALID_PRODUCTS),
            "required": True,
        },
        "channel": {
            "description": ("One of %s. Defaults to 'stable'" %
                            ", ".join(VALID_CHANNELS)),
            "default": "stable",
            "required": True,
        }
    }
    output_variables = {
        "dcp_download_regex": {
            "description": "Regex to be passed to URLTextSearcher."
        },
        "dcp_download_url": {
            "description": "Download URL to be passed to URLTextSearcher."
        },
    }

    description = __doc__

    def main(self):
        self.env["dcp_download_url"] = "https://dcpomatic.com/download"
        if self.env["channel"] == "test":
            self.env["dcp_download_url"] = "https://dcpomatic.com/test-download"

        # Need to url-quote any spaces and add a trailing space if we're doing
        # anything besides the DCP-o-matic app
        product_re_component = ""
        if self.env["app"] != "DCP-o-matic":
            product_re_component = quote(self.env["app"] + " ")

        self.env["dcp_download_regex"] = \
            "Mac OS X.*?(downloads/[0-9.]+?/DCP-o-matic%20{0}[0-9.]+?.dmg)".format(product_re_component)


if __name__ == '__main__':
    processor = DCPomaticDownloadInfoProvider()
    processor.execute_shell()
