from airflow.decorators import dag, task

from datetime import datetime
from include.extract_stages.customer_service_orders import build_customer_service_orders
from include.extract_stages.related_service_orders import build_related_service_orders
from include.extract_stages.items_service_orders import build_items_service_orders
from include.extract_stages.service_order_complaint import build_service_order_complaint
from include.extract_stages.service_order_services import build_service_order_services
from include.extract_stages.service_order_invoices import build_service_order_invoices
from include.extract_stages.service_orders_cover import build_service_orders_cover


@dag(
    description="pipeline_extracao_nbs_postgres",
    start_date=datetime(2026,4,14),
    schedule="0 * * * 1-6",
    catchup=False
    )

def pipeline_01_nbs_to_postgres():
    
    @task(task_id='customer_service_order')
    def task_build_customer_service_orders():
        return build_customer_service_orders().execute()
    
    @task(task_id='related_service_order')
    def taskbuild_related_service_orders():
        return build_related_service_orders().execute()
    
    @task(task_id='items_service_order')
    def task_build_items_service_orders():
        return build_items_service_orders().execute()
    
    @task(task_id='service_order_services')
    def task_build_service_order_services():
        return build_service_order_services().execute()
    
    @task(task_id='service_order_complaint')
    def task_build_service_order_complaint():
        return build_service_order_complaint().execute()
    
    @task(task_id='service_order_invoice')
    def task_service_order_invoices():
        return build_service_order_invoices().execute()

    @task(task_id='service_order_cover')
    def task_service_order_cover():
        return build_service_orders_cover().execute()

    t1 = task_build_customer_service_orders()

    t2 = taskbuild_related_service_orders()
    t3 = task_build_items_service_orders()
    t4 = task_build_service_order_services()
    t5 = task_build_service_order_complaint()
    t6 = task_service_order_invoices()
    t7 = task_service_order_cover()

    t1 >> t2 >> t3 >> t4 >> t5 >> t6 >> t7

pipeline_01_nbs_to_postgres()

