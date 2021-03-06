""" Tests on API methods. """

from flask import Flask, json
import requests
from nose.tools import nottest

from dagobah.core import Dagobah
from dagobah.daemon import daemon
from dagobah.backend.base import BaseBackend

class TestAPI(object):

    @classmethod
    def setup_class(self):
        self.dagobah = daemon.dagobah
        self.app = daemon.app.test_client()
        self.app.testing = True

        if type(self.dagobah.backend) != BaseBackend:
            raise TypeError('API tests should be run with the Base backend, ' +
                            'change your daemon conf')

        self.base_url = 'http://localhost:9000'


    @classmethod
    def teardown_class(self):
        self.dagobah.delete()


    @nottest
    def reset_dagobah(self):
        self.dagobah.delete()

        self.dagobah.add_job('Test Job')
        self.dagobah.add_task_to_job('Test Job', 'echo "grep"; sleep 5', 'grep')
        self.dagobah.add_task_to_job('Test Job', 'echo "list"; sleep 5', 'list')
        j = self.dagobah.get_job('Test Job')
        j.add_dependency('grep', 'list')
        j.schedule('0 0 3 0 0')



    @nottest
    def validate_api_call(self, request):
        print request.status_code
        assert request.status_code == 200
        d = json.loads(request.data)
        print d
        assert d['status'] == request.status_code
        assert 'result' in d
        return d


    def test_jobs(self):
        self.reset_dagobah()
        r = self.app.get('/api/jobs')
        d = self.validate_api_call(r)
        assert len(d.get('result', [])) == 1
        assert len(d['result'][0].get('tasks', [])) == 2


    def test_job(self):
        self.reset_dagobah()
        r = self.app.get('/api/job?job_name=Test Job')
        d = self.validate_api_call(r)


    def test_add_and_delete_job(self):
        self.reset_dagobah()
        r = self.app.post('/api/add_job', data={'job_name': 'Test Added Job'})
        d = self.validate_api_call(r)

        r = self.app.get('/api/jobs')
        d = self.validate_api_call(r)
        assert len(d.get('result', [])) == 2

        r = self.app.post('/api/delete_job', data={'job_name': 'Test Added Job'})
        d = self.validate_api_call(r)


    def test_start_job(self):
        self.reset_dagobah()
        r = self.app.post('/api/start_job', data={'job_name': 'Test Job'})
        self.validate_api_call(r)

        r = self.app.get('/api/job?job_name=Test Job')
        d = self.validate_api_call(r)
        assert d['result']['status'] == 'running'


    def test_add_task_to_job(self):
        self.reset_dagobah()
        p_args = {'job_name': 'Test Job',
                  'task_command': 'echo "testing"; sleep 5',
                  'task_name': 'test'}
        r = self.app.post('/api/add_task_to_job', data=p_args)
        self.validate_api_call(r)

        r = self.app.get('/api/jobs')
        d = self.validate_api_call(r)
        assert len(d['result']) == 1
        assert len(d['result'][0]['tasks']) == 3


    def test_add_dependency(self):
        self.reset_dagobah()
        self.dagobah.add_task_to_job('Test Job', 'from node')
        p_args = {'job_name': 'Test Job',
                  'from_task_name': 'from node',
                  'to_task_name': 'grep'}
        r = self.app.post('/api/add_dependency', data=p_args)
        self.validate_api_call(r)

        r = self.app.get('/api/jobs')
        d = self.validate_api_call(r)
        assert len(d['result']) == 1
        assert len(d['result'][0]['tasks']) == 3
        assert d['result'][0]['dependencies']['from node'] == ['grep']
