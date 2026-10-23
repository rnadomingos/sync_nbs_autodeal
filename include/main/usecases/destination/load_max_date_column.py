from include.infra.postgres_database import PostgresSessionLocal, inspector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, text
from typing import Any
import logging
from datetime import date

logger = logging.getLogger(__name__)

class TableTools:
    
    def loadMaxDateColumn(self, date_column: Any) -> dict[str, str | None]:
        """
        Get the maximum date from the given model column and format as 'yyyy-MM-dd'.

        Args:
            date_column (Any): A SQLAlchemy model column (e.g., OSCapaModel.data_cadastro).
            
        Returns:
            dict: The maximum date, or the globally configured integration start date.
        """
        with PostgresSessionLocal() as db:
            try:
                max_date = db.query(func.max(date_column)).scalar()
                if max_date:
                    return {"max_date": max_date.strftime("%Y-%m-%d")}

                initial_date = db.execute(
                    text(
                        """
                        SELECT data_inicial_integracao
                        FROM autonox_sync_config
                        WHERE config_id = 1
                        """
                    )
                ).scalar_one_or_none()
                if initial_date:
                    return {
                        "max_date": date.fromisoformat(str(initial_date)[:10]).isoformat()
                    }
                return {"max_date": None}
            except SQLAlchemyError:
                db.rollback()
                logger.exception("Error loading maximum integration date")
                raise

    def table_inspector(self, table_name: str) -> Any:
        try:
            if table_name in inspector.get_table_names():
                return True
        except SQLAlchemyError as e:
                print("Error inspect table:")
                print(e.__class__.__name__, "-", str(e._message))
                raise

                
