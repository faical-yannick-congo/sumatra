"""
Handles storage of simulation/analysis records on a remote server using HTTP.

The server should support the following URL structure and HTTP methods:

/                                            GET
/<project_name>/[?tags=<tag1>,<tag2>,...]    GET
/<project_name>/tag/<tag>/                   GET, DELETE
/<project_name>/<record_label>/              GET, PUT, DELETE

and should both accept and return JSON-encoded data when the Accept header is
"application/json".

The required JSON structure can be seen in recordstore.serialization.


:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""

from warnings import warn
from urlparse import urlparse, urlunparse
try:
    import httplib2
    import urllib2
    import requests
    have_http = True
except ImportError:
    have_http = False

from sumatra.recordstore.base import RecordStore, RecordStoreAccessError
from sumatra.recordstore import serialization
from ..core import registry
import json


API_VERSION = 3

sub_stores = ["http://10.200.95.215/"]


def domain(url):
    return urlparse(url).netloc


def process_url(url):
    """Strip out username and password if included in URL"""
    username = None
    password = None
    if '@' in url:  # allow encoding username and password in URL - deprecated in RFC 3986, but useful on the command-line
        parts = urlparse(url)
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        if parts.port:
            hostname += ":%s" % parts.port
        url = urlunparse((parts.scheme, hostname, parts.path, parts.params, parts.query, parts.fragment))
    return url, username, password


class HttpRecordStore(RecordStore):
    """
    Handles storage of simulation/analysis records on a remote server using HTTP.

    The server should support the following URL structure and HTTP methods:

    =========================================    ================
    /                                            GET
    /<project_name>/[?tags=<tag1>,<tag2>,...]    GET
    /<project_name>/tag/<tag>/                   GET, DELETE
    /<project_name>/<record_label>/              GET, PUT, DELETE
    =========================================    ================

    and should both accept and return JSON-encoded data when the Accept header is
    "application/json".

    The required JSON structure can be seen in :mod:`recordstore.serialization`.
    """

    def __init__(self, server_url, username=None, password=None,
                 disable_ssl_certificate_validation=True):
        self.server_url, _username, _password = process_url(server_url)
        username = username or _username
        password = password or _password
        if self.server_url[-1] != "/":
            self.server_url += "/"
        self.client = httplib2.Http('.cache',
                                    disable_ssl_certificate_validation=disable_ssl_certificate_validation)
        if username:
            self.client.add_credentials(username, password, domain(self.server_url))

    def __str__(self):
        return "Interface to remote record store at %s using HTTP" % self.server_url

    def __getstate__(self):
        username = password = None
        if self.client.credentials.credentials:
            username = self.client.credentials.credentials[0][1]
            password = self.client.credentials.credentials[0][2]
        return {
            'server_url': self.server_url,
            'username': username,
            'password': password,
        }

    def __setstate__(self, state):
        self.__init__(state['server_url'], state['username'], state['password'])

    def _get(self, url, media_type):
        headers = {'Accept': 'application/vnd.sumatra.%s-v%d+json, application/json' % (media_type, API_VERSION)}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def list_projects(self):
        response, content = self._get(self.server_url, 'project-list')
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (self.server_url, response.status, content))
        return [entry['id'] for entry in serialization.decode_project_list(content)]

    def _put_project(self, project_name, long_name='', description=''):
        url = "%s%s/" % (self.server_url, project_name)
        data = serialization.encode_project_info(long_name, description)
        headers = {'Content-Type': 'application/vnd.sumatra.project-v%d+json' % API_VERSION}
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        return response, content

    def create_project(self, project_name, long_name='', description=''):
        """Create an empty project in the record store."""
        response, content = self._put_project(project_name, long_name, description)
        if response.status != 201:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def update_project_info(self, project_name, long_name='', description=''):
        """Update a project's long name and description."""
        response, content = self._put_project(project_name, long_name, description)
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def has_project(self, project_name):
        project_url = "%s%s/" % (self.server_url, project_name)
        response, content = self._get(project_url, 'project')
        if response.status == 200:
            return True
        elif response.status in (401, 404):
            return False
        else:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def project_info(self, project_name):
        """Return a project's long name and description."""
        project_url = "%s%s/" % (self.server_url, project_name)
        response, content = self._get(project_url, 'project')
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (project_url, response.status, content))
        data = serialization.decode_project_data(content)
        return dict((k, data[k]) for k in ("name", "description"))

    def save(self, project_name, record):
        if not self.has_project(project_name):
            self.create_project(project_name)
        url = "%s%s/%s/" % (self.server_url, project_name, record.label)
        headers = {'Content-Type': 'application/vnd.sumatra.record-v%d+json' % API_VERSION}
        data = serialization.encode_record(record)
        response, content = self.client.request(url, 'PUT', data,
                                                headers=headers)
        if response.status not in (200, 201):
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def _get_record(self, url):
        response, content = self._get(url, 'record')
        if response.status != 200:
            if response.status == 404:
                raise KeyError("No record was found at %s" % url)
            else:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        return serialization.decode_record(content)

    def get(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        return self._get_record(url)

    def list(self, project_name, tags=None):
        project_url = "%s%s/" % (self.server_url, project_name)
        if tags:
            if not hasattr(tags, "__iter__"):
                tags = [tags]
            project_url += "?tags=%s" % ",".join(tags)
        response, content = self._get(project_url, 'project')
        if response.status != 200:
            raise RecordStoreAccessError("Could not access %s\n%s: %s" % (project_url, response.status, content))
        record_urls = serialization.decode_project_data(content)["records"]
        records = []
        for record_url in record_urls:
            records.append(self._get_record(record_url))
        return records

    def labels(self, project_name):
        return [record.label for record in self.list(project_name)]  # probably inefficient

    def delete(self, project_name, label):
        url = "%s%s/%s/" % (self.server_url, project_name, label)
        response, deleted_content = self.client.request(url, 'DELETE')
        if response.status != 204:
            raise RecordStoreAccessError("%d\n%s" % (response.status, deleted_content))

    def delete_by_tag(self, project_name, tag):
        url = "%s%s/tag/%s/" % (self.server_url, project_name, tag)
        response, n_records = self.client.request(url, 'DELETE')
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, n_records))
        return int(n_records)

    def most_recent(self, project_name):
        url = "%s%s/last/" % (self.server_url, project_name)
        return self._get_record(url).label

    def sync(self, other, project_name):
        if not self.has_project(project_name):
            self.create_project(project_name)
        super(HttpRecordStore, self).sync(other, project_name)

    def clear(self):
        warn("Cannot clear a remote record store directly. Contact the record store administrator")

    @classmethod
    def accepts_uri(cls, uri):
        return uri[:4] == "http" and not any(store in uri for store in sub_stores)


class HttpCoRRStore(RecordStore):
    """
    Handles storage of simulation/analysis records on the CoRR backend.

    The server should support the following URL structure and HTTP methods:

    This store implements CoRR's API for sumatra.
    With corr configure as the following: 
    smt init -s http://10.200.95.215/api/v0.1/private/<api-key> <project-name>
    """

    def __init__(self, server_url, disable_ssl_certificate_validation=True):
        self.server_url = server_url
        self.sumatra_token = "no-app"
        if self.server_url[-1] != "/":
            self.server_url += "/"
        if self.sumatra_token not in self.server_url:
            self.server_url = "{0}{1}/".format(self.server_url, self.sumatra_token)
        self.client = httplib2.Http('.cache', disable_ssl_certificate_validation=disable_ssl_certificate_validation)

    def __str__(self):
        return "Interface to the CoRR backend API store at %s using HTTP" % self.server_url

    def __getstate__(self):
        return {
            'server_url': self.server_url
        }

    def __setstate__(self, state):
        self.__init__(state['server_url'])

    def _get(self, url):
        headers = {'Accept': 'application/json'}
        response, content = self.client.request(url, headers=headers)
        return response, content

    def list_projects(self):
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        return [entry['id'] for entry in serialization.decode_project_list(content)['content']['projects']]

    def _put_project(self, project_name, long_name='', description=''):
        url = "%sproject/create" % (self.server_url)
        content = {'name':project_name, 'goals':long_name, 'description':description}
        headers = {'Content-Type': 'application/json'}
        response, content = self.client.request(url, 'POST', json.dumps(content),
                                                headers=headers)
        return response, content

    def _upload_file(self, record_id, file_path, group):
        url = "%sfile/upload/%s/%s" % (self.server_url, group, record_id)
        files = {'file':open(file_path)}
        response = requests.post(url, files=files)
        return response

    def create_project(self, project_name, long_name='', description=''):
        """Create an empty project in the record store."""
        response, content = self._put_project(project_name, long_name, description)
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 201:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
            return response, content

    def update_project_info(self, project_name, long_name='', description=''):
        """Update a project's long name and description."""
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project:
            url = "%sproject/update/%s" % (self.server_url, project['id'])
            data = serialization.encode_project_info(long_name, description)
            content = {'goals':long_name, 'description':description}
            headers = {'Content-Type': 'application/json'}
            response, content = self.client.request(url, 'POST', json.dumps(content),
                                                    headers=headers)
            if response.status != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))

    def has_project(self, project_name):
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project:
            return True
        else:
            return False

    def project_info(self, project_name):
        """Return a project's long name and description."""
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project:
            return {'name':project['name'], 'description':project['description']}
        else:
            raise RecordStoreAccessError("No project named %s\n" % (project_name))

    def save(self, project_name, record):
        record_id = None
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project is None:
            response, content = self.create_project(project_name)
            project = serialization.decode_project_data(content)['content']

        url = "%sproject/record/create/%s" % (self.server_url, project['id'])
        headers = {'Content-Type': 'application/json'}
        data = json.loads(serialization.encode_record(record))
        _content = {}
        _content['label'] = data['label']
        _content['tags'] = data['tags']
        _content['system'] = data['platforms'][0]
        _content['inputs'] = data['input_data']
        _content['outputs'] = data['output_data']
        _content['dependencies'] = data['dependencies']
        _content['execution'] = data['launch_mode']
        _content['status'] = 'finished'
        _content['timestamp'] = data['timestamp']
        _content['reason'] = data['reason']
        _content['duration'] = data['duration']
        _content['executable'] = data['executable']
        _content['repository'] = data['repository']
        _content['main_file'] = data['main_file']
        _content['version'] = data['version']
        _content['parameters'] = data['parameters']
        _content['script_arguments'] = data['script_arguments']
        _content['datastore'] = data['datastore']
        _content['input_datastore'] = data['input_datastore']
        _content['outcome'] = data['outcome']
        _content['stdout_stderr'] = data['stdout_stderr']
        _content['diff'] = data['diff']
        _content['user'] = data['user']
        response, content = self.client.request(url, 'POST', json.dumps(_content),
                                                headers=headers)
        if response.status != 200:
            raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 201:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
            else:
                record = serialization.decode_project_list(content)['content']
                for _input in _content['inputs']:
                    self._upload_file(record['head']['id'],'{0}/{1}'.format(_content['input_datastore']['parameters']['root'], _input['path']),'input')
                for _output in _content['outputs']:
                    self._upload_file(record['head']['id'],'{0}/{1}'.format(_content['datastore']['parameters']['root'], _output['path']),'output')

    def _get_record(self, project_id, label):
        records = []
        url = "%sproject/records/%s" % (self.server_url, project_id)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        if label == None:
            for r in serialization.decode_project_list(content)['content']['records']:
                records.append(r)
        else:
            for r in serialization.decode_project_list(content)['content']['records']:
                if r['label'] == label:
                    records.append(r)
                    break

        if len(records) == 1:
            content = {}
            content['label'] = record['head']['label']
            content['tags'] = record['head']['tags']
            content['platforms'] = [record['head']['system']]
            content['input_data'] = record['head']['inputs']
            content['output_data'] = record['head']['outputs']
            content['dependencies'] = record['head']['dependencies']
            content['launch_mode'] = record['head']['execution']
            content['timestamp'] = record['body']['content']['timestamp']
            content['reason'] = record['body']['content']['reason']
            content['duration'] = record['body']['content']['duration']
            content['executable'] = record['body']['content']['executable']
            content['repository'] = record['body']['content']['repository']
            content['main_file'] = record['body']['content']['main_file']
            content['version'] = record['body']['content']['version']
            content['parameters'] = record['body']['content']['parameters']
            content['script_arguments'] = record['body']['content']['script_arguments']
            content['datastore'] = record['body']['content']['datastore']
            content['input_datastore'] = record['body']['content']['input_datastore']
            content['outcome'] = record['body']['content']['outcome']
            content['stdout_stderr'] = record['body']['content']['stdout_stderr']
            content['diff'] = record['body']['content']['diff']
            content['user'] = record['body']['content']['user']
            return serialization.build_record(content)
        elif len(records) > 1:
            contents = []
            for record in records:
                content = {}
                content['label'] = record['head']['label']
                content['tags'] = record['head']['tags']
                content['platforms'] = [record['head']['system']]
                content['input_data'] = record['head']['inputs']
                content['output_data'] = record['head']['outputs']
                content['dependencies'] = record['head']['dependencies']
                content['launch_mode'] = record['head']['execution']
                content['timestamp'] = record['body']['body']['content']['timestamp']
                content['reason'] = record['body']['body']['content']['reason']
                content['duration'] = record['body']['body']['content']['duration']
                content['executable'] = record['body']['body']['content']['executable']
                content['repository'] = record['body']['body']['content']['repository']
                content['main_file'] = record['body']['body']['content']['main_file']
                content['version'] = record['body']['body']['content']['version']
                content['parameters'] = record['body']['body']['content']['parameters']
                content['script_arguments'] = record['body']['body']['content']['script_arguments']
                content['datastore'] = record['body']['body']['content']['datastore']
                content['input_datastore'] = record['body']['body']['content']['input_datastore']
                content['outcome'] = record['body']['body']['content']['outcome']
                content['stdout_stderr'] = record['body']['body']['content']['stdout_stderr']
                content['diff'] = record['body']['body']['content']['diff']
                content['user'] = record['body']['body']['content']['user']
                contents.append(serialization.build_record(content))
            return contents
        else:
            raise RecordStoreAccessError("No record with these label %s\n" % (label))

    def get(self, project_name, label):
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project:
            return self._get_record(project['id'], label)
        else:
            raise RecordStoreAccessError("No project named %s\n" % (project_name))


    def list(self, project_name, tags=None):
        project = None
        url = "%sprojects" % (self.server_url)
        response, content = self._get(url)
        if response.status != 200:
            raise RecordStoreAccessError("Error in accessing %s\n%s: %s" % (url, response.status, content))
        else:
            code = json.loads(content)['code']
            if code != 200:
                raise RecordStoreAccessError("%d\n%s" % (response.status, content))
        for p in serialization.decode_project_list(content)['content']['projects']:
            if p['name'] == project_name:
                project = p
                break
        if project:
            return self._get_record(project['id'], None)
        else:
            raise RecordStoreAccessError("No project named %s\n" % (project_name))

    def labels(self, project_name):
        return [record['label'] for record in self.list(project_name)]

    def delete(self, project_name, label):
        warn("Deleting is not allowed by CoRR from the Command line tool for now.")


    def delete_by_tag(self, project_name, tag):
        warn("Deleting a record store is not allowed by CoRR from the Command line tool for now.")
        return 0

    def most_recent(self, project_name):
        latest = None
        records = self.list(project_name)
        for record in records:
            if latest is None:
                latest = record
            else:
                latest_stamp = datetime.strptime(timestamp1, "%Y-%m-%d %H:%M:%S")
                record_stamp = datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S")
                if max((latest_stamp, record_stamp)) == record_stamp:
                    latest = record
        return latest['label']

    def sync(self, other, project_name):
        if not self.has_project(project_name):
            self.create_project(project_name)
        super(HttpRecordStore, self).sync(other, project_name)

    def clear(self):
        warn("Clearing a record store is not allowed by CoRR from the Command line tool for now.")

    @classmethod
    def accepts_uri(cls, uri):
        return (sub_stores[0] in uri)

if have_http:
    registry.register(HttpRecordStore)
    registry.register(HttpCoRRStore)
