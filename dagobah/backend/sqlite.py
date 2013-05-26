""" SQLite Backend class built on top of base Backend """

import os
from datetime import datetime

import sqlalchemy

from dagobah.backend.base import BaseBackend
from dagobah.backend.sqlite_models import (Base, Dagobah, DagobahJob,
                                           DagobahTask, DagobahDependency,
                                           DagobahLog, DagobahLogTask)


class SQLiteBackend(BaseBackend):
    """ SQLite Backend implementation """

    def __init__(self, filepath):
        super(SQLiteBackend, self).__init__()

        self.filepath = filepath
        if self.filepath == 'default':
            location = os.path.realpath(os.path.join(os.getcwd(),
                                                     os.path.dirname(__file__)))
            self.filepath = os.path.join(location, 'dagobah.db')

        self.engine = sqlalchemy.create_engine('sqlite:///' + self.filepath)
        self.Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = self.Session()

        Base.metadata.create_all(self.engine)


    def __repr__(self):
        return '<SQLiteBackend (path: %s)>' % (self.filepath)


    def get_known_dagobah_ids(self):
        results = []
        for rec in self.session.query(Dagobah).all():
            results.append(rec.id)
        return results


    def get_new_dagobah_id(self):
        return max(self.session.query(sqlalchemy.func.max(Dagobah.id)) + 1, 1)


    def get_new_job_id(self):
        return max(self.session.query(sqlalchemy.func.max(DagobahJob.id)) + 1,
                   1)


    def get_new_log_id(self):
        return max(self.session.query(sqlalchemy.func.max(DagobahLog.id)) + 1,
                   1)


    def get_dagobah_json(self, dagobah_id):
        self.session.query(Dagobah).\
            filter_by(id=dagobah_id).\
            one().json


    def commit_dagobah(self, dagobah_json):
        dagobah_json['_id'] = dagobah_json['dagobah_id']
        append = {'save_date': datetime.utcnow()}
        self.dagobah_coll.save(dict(dagobah_json.items() + append.items()))


    def delete_dagobah(self, dagobah_id):
        """ Deletes the Dagobah and all child Jobs from the database.

        Run logs are not deleted.
        """

        rec = self.dagobah_coll.find_one({'_id': dagobah_id})
        for job in rec.get('jobs', []):
            if 'job_id' in job:
                self.delete_job(job['job_id'])
        self.dagobah_coll.remove({'_id': dagobah_id})


    def commit_job(self, job_json):
        job_json['_id'] = job_json['job_id']
        append = {'save_date': datetime.utcnow()}
        self.job_coll.save(dict(job_json.items() + append.items()))


    def delete_job(self, job_id):
        self.job_coll.remove({'_id': job_id})


    def commit_log(self, log_json):
        """ Commits a run log to the Mongo backend.

        Due to limitations of maximum document size in Mongo,
        stdout and stderr logs are truncated to a maximum size for
        each task.
        """

        log_json['_id'] = log_json['log_id']
        append = {'save_date': datetime.utcnow()}

        for task_name, values in log_json.get('tasks', {}).items():
            for key, size in TRUNCATE_LOG_SIZES_CHAR.iteritems():
                if isinstance(values.get(key, None), str):
                    if len(values[key]) > size:
                        values[key] = '\n'.join([values[key][:size/2],
                                                 'DAGOBAH STREAM SPLIT',
                                                 values[key][-1 * (size/2):]])
        self.log_coll.save(dict(log_json.items() + append.items()))


    def get_latest_run_log(self, job_id, task_name):
        q = {'job_id': ObjectId(job_id),
             'tasks.%s' % task_name: {'$exists': True}}
        cur = self.log_coll.find(q).sort([('save_date', pymongo.DESCENDING)])
        for rec in cur:
            return rec
        return {}
