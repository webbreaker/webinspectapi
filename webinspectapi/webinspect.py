#!/usr/bin/env python

__author__ = "Brandon Spruth (brandon@webbreaker.io)"
__copyright__ = "(C) 2018 Target Brands, Inc."
__contributors__ = ["Brandon Spruth"]
__status__ = "Production"
__license__ = "MIT"

import json
import ntpath
import requests
import urllib3
import requests.exceptions
import requests.packages.urllib3
from . import __version__ as version


class WebInspectApi(object):
    def __init__(self, host, username=None, password=None, verify_ssl=True, user_agent=None, cert=None, timeout=None):

        self.host = host
        self.username = username
        self.password = password
        self.cert = cert
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        if not user_agent:
            self.user_agent = 'webinspectapi/' + version
        else:
            self.user_agent = user_agent

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Set auth_type based on what's been provided
        if username is not None:
            self.auth_type = 'basic'
        elif cert is not None:
            self.auth_type = 'certificate'
        else:
            self.auth_type = 'unauthenticated'

    def create_scan(self, overrides):
        """
        :param overrides:
        :return: Creates a scan with the given settings.
        """
        return self._request('POST', '/webinspect/scanner/scans/', data=overrides)

    def create_wiswag(self, swagger_url, wiswag_name):
        """
        Pass in the swagger swagger url to create a settings file on the server.
        :param swagger_url: a swagger json url: example: http://petstore.swagger.io/v2/swagger.json
        :param wiswag_name: the desired wiswag name:

        :return: Creates a setting file on the remote WebInspect Server
        """

        json_data = """
        {{
            \"config\":
            {{
                \"apiDefinition\"  : \"{0}\",
            }},
                \"outputType\"     : \"settings\",
                \"outputName\"     : \"{1}\"
        }}
        """
        data = json_data.format(swagger_url, wiswag_name)
        headers = {
            'Accept': 'application/json'
        }
        headers.update({'Content-Type': 'application/json'})

        return self._request('PUT', '/webinspect/scanner/wiswag/', data=data, headers=headers)

    def delete_policy(self, policy_guid):
        """
        :param policy_guid:
        :return: Delete the policy identified by the provided guid
        """
        return self._request('DELETE', '/webinspect/securebase/policy/' + policy_guid)

    def download_settings(self, settings_name):
        """
        returns a xml of a settings file off of the webinspect server.
        :param settings_name: name of the settings file you would like to download
        :return: Downloads the xml setting file from the remote WebInspect server
        """

        return self._request('GET', '/webinspect/scanner/settings/' + str(settings_name))

    def export_scan_format(self, scan_id, extension, detail_type=None):
        """
        :param scan_id:
        :param extension: supported extensions are xml, scan, settings, fpr, crawl, issue, all
        :param detail_type: supported if extension is xml
        :return: Export scan data to one of several formats.
        """
        if extension == '.xml' and detail_type:
            url = '/webinspect/scanner/scans/' + str(scan_id) + '.' + str(extension) + "?detailType=" + detail_type
        else:
            url = '/webinspect/scanner/scans/' + str(scan_id) + '.' + str(extension)

        return self._request('GET', url)

    def get_current_status(self, scan_id):
        """
        :param scan_id:
        :return: Retrieves status of scanId valid operations are: Running, Complete, Incomplete
        """
        return self._request('GET', '/webinspect/scanner/scans/' + str(scan_id) + '?action=getcurrentstatus')

    def get_policy_by_guid(self, policy_guid):
        """
        :param policy_id:
        :return: Policy specified by id
        """
        return self._request('GET', '/webinspect/securebase/policy/' + str(policy_guid))

    def get_policy_by_name(self, name):
        """
        :param name:
        :return: Retrieves policy having the given name. If no matching policy, return None
        """
        response = self.list_policies()
        if response.success:
            for policy in response.data:
                if policy['name'] == name:
                    return WebInspectResponse(success=True, message=None, data=policy, response_code=200)
        return WebInspectResponse(success=True, message=None, data=None, response_code=404)

    def get_scan_by_name(self, scan_name):
        """
        :param scan_name: Default takes the name of the settings.xml which will not be unique,
        recommendation: If running webinspect scans in a Continuous Delivery (CD), use CD environment variables.
        :return: Fetches only a listing of the scan_name specified
        """
        return self._request('GET', '/webinspect/scanner/scans?Name=' + str(scan_name))

    def get_scan_issues_detail(self, scan_guid):
        """
        :param scan_guid:
        :return: Return issues identified by scan
        """
        return self._request('GET', '/webinspect/scanner/scans/' + str(scan_guid) + '.issue?detailType=full')

    def get_scan_log(self, scan_guid):
        """
        :param scan_guid:
        :return: Return log of the scan identified by the provided GUID
        """
        return self._request('GET', '/webinspect/scanner/scans/' + str(scan_guid) + '/log')

    def list_policies(self):
        """
        :return: Fetches a listing of policies
        """
        return self._request('GET', '/webinspect/securebase/policy')

    def list_running_scans(self):
        """
        :return: returns a list of running scans
        """
        return self._request('GET', '/webinspect/scanner/scans?Status=running')

    def list_scans(self):
        """
        :return: Fetches a listing of current and past scans from the WebInspect scanner.
        """
        return self._request('GET', '/webinspect/scanner/scans')

    def list_settings(self):
        """
        :return: Fetches a listing of settings.
        """
        return self._request('GET', '/webinspect/scanner/settings')

    def list_webmacros(self):
        """
        :return: Fetches a listing of webmacros
        """
        return self._request('GET', '/webinspect/scanner/macro')

    def stop_scan(self, scan_guid):
        """
        :param scan_guid:
        :return: WebInpsect response with success indicator and message
        """
        return self._request('POST', '/webinspect/scanner/scans/' + str(scan_guid) + '?action=stop')

    def continue_scan(self, scan_guid):
        """
        :param scan_guid:
        :return: WebInpsect response with success indicator and message
        """
        return self._request('POST', '/webinspect/scanner/scans/' + str(scan_guid) + '?action=continue')

    def delete_scan(self, scan_guid):
        """
        :param scan_guid:
        :return: Delete the scan identified by the provided guid
        """
        return self._request('DELETE', '/webinspect/scanner/scans/' + str(scan_guid))

    def upload_policy(self, policy_file_path):
        try:
            data = {"policy": ""}
            files = {'file': (ntpath.basename(policy_file_path), open(policy_file_path, 'rb'),)}

        except IOError as e:
            return WebInspectResponse(success=False,
                                      message="There was an error while handling the request{}.".format(e))

        # hack. doing this avoids us later specifying a content-type of application/json. needs a refactor
        headers = {
            'Accept': 'application/json'
        }
        return self._request('POST', '/webinspect/securebase/policy', data=data, files=files, headers=headers)

    def upload_settings(self, settings_file_path):

        try:
            data = {"scanSettings": ""}
            files = {'file': (ntpath.basename(settings_file_path), open(settings_file_path, 'rb'),)}

        except IOError as e:
            return WebInspectResponse(success=False,
                                      message="There was an error while handling the request{}.".format(e))

        return self._request('PUT', '/webinspect/scanner/settings', data=data, files=files)

    def upload_webmacro(self, macro_file_path):
        try:
            files = {'macro': (ntpath.basename(macro_file_path), open(macro_file_path, 'rb'))}

        except IOError as e:
            return WebInspectResponse(success=False, message="Could not read file to upload {}.".format(e))

        return self._request('PUT', '/webinspect/scanner/macro', files=files)

    def wait_for_status_change(self, scan_id):
        """
        :param scan_id: Assigned GUID for scan running.
        :return: Polls scanId with a Running status
        """
        return self._request('GET', '/webinspect/scanner/scans/' + str(scan_id) + '?action=waitforstatuschange')

    def cert_proxy(self):
        """
        :return: WebInspect Certificate to import to browser
        """
        return self._request('GET', '/webinspect/proxy/rootcert', )

    def start_proxy(self, id, port, address):
        """
        :param id: Arbitrary user controlled ID for WI proxy .
        :param port: Assigned port to initialize proxy traffic.
        :param address: Address to be used to proxy traffic, typically the WI instance public addr.
        :return: creates socket listener with proxy port and address
        """
        json_data = """
        {{
            \"instanceId\"  : \"{0}\",
            \"address\"     : \"{1}\",
            \"port\"        : \"{2}\"
        }}
        """
        data = json_data.format(id, address, port)
        return self._request('POST', '/webinspect/proxy/', data=data)

    def delete_proxy(self, instance_id):
        """
        Stop proxy is not supported by WebInspect, use delete
        :param instance_id: Arbitrary user controlled ID for WI webmacro
        :return: Stop and delete proxy with specified instance_id
        """
        return self._request('DELETE', '/webinspect/proxy/' + str(instance_id))

    def upload_webmacro_proxy(self, instance_id, macro_file_path):
        """
        :param instance_id: Arbitrary user controlled ID for WI webmacro
        :param macro_file_path: Path to webmacro to upload
        :return: Saves a webmacro onto WebInspect Server
        """
        try:
            files = {'macro': open(macro_file_path, 'rb')}
        except IOError as e:
            return WebInspectResponse(success=False, message="Could not read file to upload {}.".format(e))

        return self._request('PUT', '/webinspect/proxy/' + str(instance_id) + '.webmacro' + '?action=save', files=files)

    def download_proxy_setting(self, instance_id):
        """
        :param instance_id: Arbitrary user controlled ID for WI webmacro
        :return: Get setting '<name>.xml' from WebInspect Server
        """
        return self._request('GET', '/webinspect/proxy/' + str(instance_id) + '.xml')

    def download_proxy_webmacro(self, instance_id):
        """
        :param instance_id: Arbitrary user controlled ID for WI webmacro
        :return: Get webmacro '<name>.webmacro' from WebInspect Server
        """
        return self._request('GET', '/webinspect/proxy/' + str(instance_id) + '.webmacro')

    def list_proxies(self):
        """
        :return: List all proxies in json format from server
        """
        return self._request('GET', '/webinspect/proxy', )

    def get_proxy_information(self, instance_id):
        """
        :param instance_id: Arbitrary user controlled ID for WI webmacro
        :return: Get information on proxy from WebInspect Server
        """
        return self._request('GET', '/webinspect/proxy/' + str(instance_id))

    def get_scan_crawl_json(self, scan_guid):
        """
        :param scan_guid:
        :return: WebInpsect response with success indicator and message
        """
        return self._request('POST', '/webinspect/scanner/scans/' + str(scan_guid) + '/data/sitetree/json')

    @staticmethod
    def _build_list_params(param_name, key, values):
        """Builds a list of POST parameters from a list or single value."""
        params = {}
        if hasattr(values, '__iter__'):
            index = 0
            for value in values:
                params[str(param_name) + '[' + str(index) + '].' + str(key)] = str(value)
                index += 1
        else:
            params[str(param_name) + '[0].' + str(key)] = str(values)
        return params

    def _request(self, method, url, params=None, files=None, data=None, headers=None):
        """Common handler for all HTTP requests."""
        if not params:
            params = {}

        # set some reasonable default headers, unsure if necessary - requests import may have some logic
        if not headers:
            headers = {
                'Accept': 'application/json'
            }
            if method == 'GET' or method == 'POST':
                headers.update({'Content-Type': 'application/json'})
        headers.update({'User-Agent': self.user_agent})

        try:

            if self.auth_type == 'basic':
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            verify=self.verify_ssl,
                                            timeout=self.timeout,
                                            auth=(self.username, self.password))
            elif self.auth_type == 'certificate':
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            verify=self.verify_ssl,
                                            timeout=self.timeout,
                                            cert=self.cert)
            else:
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            timeout=self.timeout,
                                            verify=self.verify_ssl)

            try:
                response.raise_for_status()

                # two flavors of response are successful, GETs return 200, PUTs return 204 with empty response text
                response_code = response.status_code
                success = True if response_code // 100 == 2 else False
                if response.text:
                    try:
                        data = response.json()
                    except ValueError:  # Sometimes the returned data isn't JSON (e.g. GetScanFormat) so return raw
                        data = response.content
                else:
                    data = ''

                return WebInspectResponse(success=success, response_code=response_code, data=data)
            except ValueError as e:
                return WebInspectResponse(success=False, message="JSON response could not be decoded {}.".format(e))
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    return WebInspectResponse(success=False, response_code=401, message=e)
                else:
                    return WebInspectResponse(
                        message='There was an error while handling the request. {}'.format(response.content), success=False)
        except requests.exceptions.SSLError:
            return WebInspectResponse(message='An SSL error occurred.', success=False)
        except requests.exceptions.ConnectionError:
            return WebInspectResponse(message='A connection error occurred.', success=False)
        except requests.exceptions.Timeout:
            return WebInspectResponse(message='The request timed out after ', success=False)
        except requests.exceptions.RequestException:
            return WebInspectResponse(
                message='There was an error while handling the request. {}'.format(response.content), success=False)


class WebInspectResponse(object):
    """Container for all WebInspect API responses, even errors."""

    def __init__(self, success, message='OK', response_code=-1, data=None):
        self.message = message
        self.success = success
        self.response_code = response_code
        self.data = data

    def __str__(self):
        if self.data:
            return str(self.data)
        else:
            return self.message

    def data_json(self, pretty=False):
        """Returns the data as a valid JSON string."""
        if pretty:
            return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.data)
