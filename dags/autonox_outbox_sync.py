from airflow.decorators import dag, task
from datetime import datetime, timedelta
from include.services.sync_service import SyncService

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


@dag(
    description="pipeline_sincronizacao_outbox_api_autonox",
    start_date=datetime(2026, 4, 14),
    schedule="*/15 * * * *",
    catchup=False,
    default_args=default_args,
)
def pipeline_02_autonox_outbox_sync():

    @task(task_id="enqueue_autonox_outbox")
    def task_enqueue_autonox_outbox():
        service = SyncService()
        return service.enqueue_updated_orders()

    @task(task_id="process_autonox_outbox")
    def task_process_autonox_outbox():
        service = SyncService()
        return service.process_outbox()

    t1 = task_enqueue_autonox_outbox()
    t2 = task_process_autonox_outbox()
    t1 >> t2


pipeline_02_autonox_outbox_sync()
