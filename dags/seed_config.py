from datetime import datetime

from airflow.decorators import dag, task


@dag(
    description="Inicialização manual das configurações da integração Autonox",
    start_date=datetime(2026, 4, 14),
    schedule=None,
    catchup=False,
)
def pipeline_00_seed_config():
    @task(task_id="seed_config")
    def task_seed_config():
        from include.data.seeds.seed_config import seed_config

        return seed_config()

    task_seed_config()


pipeline_00_seed_config()
