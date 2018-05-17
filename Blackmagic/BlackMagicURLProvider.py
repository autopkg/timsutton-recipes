#!/usr/bin/python
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
"""See docstring for BlackMagicURLProvider class"""

import json
import re
import urllib2

from distutils.version import LooseVersion, StrictVersion
from operator import itemgetter
from pprint import pprint

from autopkglib import Processor, ProcessorError

__all__ = ["BlackMagicURLProvider"]

DOWNLOADS_URL = "https://www.blackmagicdesign.com/api/support/us/downloads.json"
REQUIRED_REG_KEYS = [
    "firstname",
    "lastname",
    "email",
    "phone",
    "city",
    "state",
    "country",
]

class BlackMagicURLProvider(Processor):
    """Provides a version and dmg download for the Barebones product given."""
    description = __doc__
    input_variables = {
        "version_pattern": {
            "required": False,
            "description":
                "Regex pattern that will applied to all 'name' elements in, "
                "the downloads JSON metadata. Only downloads matching this "
                "pattern will be considered. This pattern _must_ contain "
                "at least a named group 'version', which will be used to "
                "sort the results by evaluating this using distutils' "
                "LooseVersion."
        },
        "product_name": {
            "required": True,
            "description":
                "Product to fetch URL for. See the list of names "
                "given in the metadata file at %s. For example, 'DaVinci "
                "Resolve Lite'" % DOWNLOADS_URL
        },
        "product_name_pattern": {
            "required": True,
            "description":
                "Regex pattern that will applied to all 'name' elements in, "
                "the downloads JSON metadata. Only downloads matching this "
                "pattern will be considered. This pattern _must_ contain "
                "at least a named group 'version', which will be used to "
                "sort the results by evaluating this using distutils' "
                "LooseVersion."
        },
        "registration_info": {
            "required": False,
            "description":
                "A dictionary containing registration information. This "
                "is only required for downloads that require registration, "
                "such as DaVinci Resolve Lite. This can otherwise be "
                "omitted. It must contain the following keys: %s."
                % ", ".join(REQUIRED_REG_KEYS)
        },
    }
    output_variables = {
        "description": {
            "description:" "Description of the product."
        },
        "version": {
            "description": "Version of the product.",
        },
        "url": {
            "description": "Download URL.",
        },
    }


    def get_downloads_metadata(self):
        '''Return a deserialized json object from the BM downloads metadata.'''
        try:
            metadata = urllib2.urlopen(DOWNLOADS_URL).read()
            json_data = json.loads(metadata)
        except urllib2.HTTPError, ValueError:
            raise ProcessorError("Could not parse downloads metadata.")
        return json_data

    def main(self):
        '''Find the download URL'''

        def compare_version(this, that):
            '''compare LooseVersions'''
            return cmp(LooseVersion(this), LooseVersion(that))

        metadata = self.get_downloads_metadata()

        # build our own list of matching products, filtering on criteria:
        # - relatedProductOverride element must contain our 'product_name'
        #   (this name gets POSTed back to request the download URL)
        # - name element must match our 'product_name_pattern' regex

        self.output("Filtering json 'name' attributes with regex %s" %
                        self.env["product_name_pattern"])
        prods = []
        for m_prod in metadata["downloads"]:

            match = re.match(self.env["product_name_pattern"], m_prod["name"])
            if match:
                if not match.group("version"):
                    self.output("WARNING: Regex matched but no "
                                "named group 'version' matched!")
                p = m_prod.copy()
                # recording the version extracted by our named group in
                # 'product_name_pattern'
                p["version"] = match.group("version")
                prods.append(p)
        # sort by version and grab the highest one
        latest_prod = sorted(
            prods,
            key=itemgetter("version"),
            cmp=compare_version)[-1]

        # ensure our product contains info we need
        try:
            download_id = latest_prod["urls"]["Mac OS X"][0]["downloadId"]
            desc = latest_prod["desc"]
        except KeyError:
            raise ProcessorError("Metadata for product is missing at the "
                                 "expected location in feed.")

        # if this download needs registration, ensure we've set everything
        if latest_prod["requiresRegistration"]:
            errormsg = ("This product requires registration. Please set all "
                        "registration information in this processor using "
                        "the 'registration_info' input variable.")
            if not self.env.get("registration_info"):
                raise ProcessorError(errormsg)
            else:
                for key in REQUIRED_REG_KEYS:
                    if key not in self.env["registration_info"] or \
                       not self.env["registration_info"][key]:
                        raise ProcessorError(errormsg)

        # now build a request JSON to finally ask for the download URL
        req_data = {
            "country": "us",
            "platform": "Mac OS X",
            "product": {
                "name": self.env["product_name"]
            }
        }
        for k in self.env["registration_info"]:
            req_data[k] = self.env["registration_info"][k]
        req_data = json.dumps(req_data)

        url = "https://www.blackmagicdesign.com/api/register/us/download/"
        url += str(download_id)

        request = urllib2.Request(url, req_data)
        request.add_header("Content-Type", "application/json;charset=UTF-8")
        request.add_header("User-Agent", "Mozilla/5.0")
        try:
            result = urllib2.urlopen(request)
            download_url = result.read()
        except urllib2.HTTPError as exc:
            raise ProcessorError(
                "Could not get a download URL: %s" % exc)

        self.env["version"] = latest_prod["version"]
        self.env["url"] = download_url
        self.env["description"] = desc
        self.output("Found download URL for %s, version %s: %s" %
                    (self.env["product_name"],
                    self.env["version"],
                    self.env["url"]))


if __name__ == "__main__":
    PROCESSOR = BlackMagicURLProvider()
    PROCESSOR.execute_shell()
