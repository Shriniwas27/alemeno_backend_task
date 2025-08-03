from django.core.management.base import BaseCommand
from api.tasks import ingest_customer_data, ingest_loan_data
from celery import chain

class Command(BaseCommand):

    def handle(self, *args, **options):
        
        task_chain = chain(ingest_customer_data.s(), ingest_loan_data.s())
        task_chain.delay()
        self.stdout.write(self.style.SUCCESS('Sequential data ingestion tasks have been queued.'))