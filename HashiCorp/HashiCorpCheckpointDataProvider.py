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

import json
import urllib2

from autopkglib import Processor, ProcessorError

__all__ = ["HashiCorpCheckpointDataProvider"]

KNOWN_PRODUCTS = [
    "consul",
    "packer",
    "serf",
    "terraform",
    ]

class HashiCorpCheckpointDataProvider(Processor):
    description = ("Check the HashiCorp Checkpoint API for information "
                   "about its various products, returning download page "
                   "URLs and versions.")
    input_variables = {
        "product": {
            "description": "Product name to query.",
			"required": True,
        }
    }
    output_variables = {
        "hashicorp_product_download_page": {
            "description": ("Download page for the product (not the 'final' "
                            "download url.")
        },
        "version": {
            "description": "Current version of the product."
        }
    }

    __doc__ = description

    def return_content_or_error(self, url, req_headers={}, resp_headers=[]):
        '''Returns a tuple of response data, and dictionary of optional
        response headers {name: value} for a given URL. 

        req_headers is a dictionary of HTTP headers to include in the request,
        resp_headers is a list of headers to return from the response.

        Any headers returned in the second element of the tuple which did
        not exist from the server's response will be set to None.'''

        req = urllib2.Request(url=url, headers=req_headers)
        try:
            url_data = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            raise ProcessorError(
                "HTTP Error %s on opening URL %s" % (e, url))

        return_headers = {}
        if resp_headers:
            for header in resp_headers:
                return_headers[header] = url_data.headers.getheader(header)
        return (url_data.read(), return_headers)


    def main(self):
        base_url = "https://checkpoint-api.hashicorp.com/v1/check"
        product = self.env["product"]
        if product not in KNOWN_PRODUCTS:
            raise ProcessorError(
                "'product' input variable must be one of: %s"
                % ", ".join(KNOWN_PRODUCTS))
        check_url = "%s/%s" % (base_url, product)
        headers = {"Accept": "application/json",
                   "User-Agent": "autopkg/autopkg"}
        (content, _) = self.return_content_or_error(
            check_url,
            req_headers=headers)
        try:
            product_data = json.loads(content)
        except ValueError:
            raise ProcessorError(
                "Error decoding JSON response from URL: %s" % check_url)
        for expected_key in ["current_download_url", "current_version"]:
            if expected_key not in product_data:
                raise ProcessorError(
                    "Missing at least one expected key in JSON response.")


        self.env["hashicorp_product_download_page"] = \
            product_data["current_download_url"]
        self.env["version"] = product_data["current_version"]


if __name__ == "__main__":
    processor = HashiCorpCheckpointDataProvider()
    processor.execute_shell()
