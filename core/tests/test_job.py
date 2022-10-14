import json
import time
import env  # noqa
import threading
from mock import patch
from nose import tools
import patches

from densefog.model.job import job as job_model
from densefog.model.job import run_job

from densefog.model import base

import fixtures

project_id_1 = 'prjct-1234'

worker = fixtures.worker


def mock_nope(*args, **kwargs):
    return True


def mock_heavy_sync(*args, **kwargs):
    time.sleep(4)


class TestModel:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_create(self):
        with patch('model.job.action.sync') as mock:
            mock.return_value = None

            job_id = job_model.create(action='Sync')

            tools.eq_(job_model.get(job_id)['status'],
                      job_model.JOB_STATUS_PENDING)

            run_job(job_id, worker)
            tools.eq_(job_model.get(job_id)['status'],
                      job_model.JOB_STATUS_FINISHED)

            mock.side_effect = Exception()

            job_id = job_model.create(action='Sync')
            run_job(job_id, worker)
            tools.eq_(job_model.get(job_id)['status'],
                      job_model.JOB_STATUS_PENDING)

            run_job(job_id, worker)
            tools.eq_(job_model.get(job_id)['status'],
                      job_model.JOB_STATUS_PENDING)

            run_job(job_id, worker)
            tools.eq_(job_model.get(job_id)['status'],
                      job_model.JOB_STATUS_ERROR)

    @patch('model.job.action.sync', mock_heavy_sync)
    def test_fetch_job(self):
        from densefog import db

        job_id = job_model.create(action='Sync')

        def exec_a_job(job_id):
            with base.open_transaction(db.DB):
                job = job_model.fetch(job_id)
                job_model.prepare(job)
                job_model.execute(job, worker)

        # let's fetch a job in a transaction.
        def fetch_a_job(job_id):
            with base.open_transaction(db.DB):
                t1 = time.time()
                job_model.fetch(job_id)
                t2 = time.time()

            # wait for exec_a_job finish and release lock.
            tools.assert_greater_equal(int(t2 - t1), 3)

        p1 = threading.Thread(target=exec_a_job, args=(job_id, ))
        p1.start()
        time.sleep(1)
        p2 = threading.Thread(target=fetch_a_job, args=(job_id, ))
        p3 = threading.Thread(target=fetch_a_job, args=(job_id, ))

        p2.start()
        p3.start()

        p1.join()
        p2.join()
        p3.join()


@patches.check_access_key(project_id_1)
class TestAPI:

    def setup(self):
        env.reset_db()
        fixtures.insert_project(project_id_1)

    def test_describe_jobs(self):
        job_model.create(
            project_id=project_id_1,
            action='Sync')
        job_model.create(
            project_id=project_id_1,
            action='Sync')
        job_model.create(
            project_id=project_id_1,
            action='Sync')

        result = fixtures.public.post('/', data=json.dumps({
            'action': 'DescribeJobs'
        }))

        data = json.loads(result.data)
        tools.eq_(len(data['data']['jobSet']), 3)
