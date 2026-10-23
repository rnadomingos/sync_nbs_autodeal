import logging
from include.extract_stages import run as run_extract_stages
from include.services.sync_service import SyncService
from include.data.seeds.seed_config import seed_config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_full_pipeline():
    logger.info("Carregando configuração inicial da integração...")
    seed_config()

    logger.info("Iniciando extração do Oracle NBS para PostgreSQL Staging...")
    run_extract_stages()

    logger.info("Iniciando sincronização via Outbox para API Autonox...")
    sync_service = SyncService()
    sync_service.enqueue_updated_orders()
    results = sync_service.process_outbox()
    logger.info(f"Pipeline concluído com sucesso: {results}")


if __name__ == "__main__":
    run_full_pipeline()
