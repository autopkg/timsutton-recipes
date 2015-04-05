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

import re
import urllib2

from autopkglib import Processor, ProcessorError

__all__ = ["Max7DownloadURLProvider"]


class Max7DownloadURLProvider(Processor):
    description = ("Scrape multiple redirected C74 webpages to get the "
                   "download URL for Max 7. This also captures a cookie and "
                   "sets 'request_headers' for use by URLDownloader in a "
                   "later recipe step.")
    input_variables = {
    }
    output_variables = {
        "url": {
            "description": "Download URL for the Max 7 release."
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
        base_url = "http://cycling74.com"
        # This is used by the application to find out about new versions,
        # but there seems to be an issue retrieving this with urllib2.
        # meta_response = self.return_content_or_error(
        #     "https://auth.cyling74.com/maxversion")
        # try:
        #     version_meta = json.loads(meta_response)
        # except:
        #     do stuff
        # print version_meta

        (website_content, _) = self.return_content_or_error(
            "http://cycling74.com/downloads")

        website_data = re.search(r"(/.*dmg)\"", website_content)
        if not website_data:
            raise ProcessorError(
                "Could not locate first download link on Max 7 download page.")
        url_one = website_data.groups()[0]
        if url_one.startswith("/"):
            url_one = base_url + url_one

        (thanks_content, _) = self.return_content_or_error(url_one)
        thanks_data = re.search(r"(http://filepivot.+?dmg)", thanks_content)
        if not thanks_data:
            raise ProcessorError(
                ("Could not locate second download link on Max 7 'thanks "
                 "for downloading' page."))
        url_two = thanks_data.groups()[0]

        self.env["url"] = url_two


if __name__ == "__main__":
    processor = Max7DownloadURLProvider()
    processor.execute_shell()
