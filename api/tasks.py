from celery import shared_task
import pandas as pd
from .models import Customer, Loan

@shared_task
def ingest_customer_data():
    
    df = pd.read_excel('customer_data.xlsx')
    for _, row in df.iterrows():
        Customer.objects.update_or_create(
            customer_id=int(row['Customer ID']),
            defaults={
                'first_name': row['First Name'],
                'last_name': row['Last Name'],
                'phone_number': row['Phone Number'],
                'monthly_salary': row['Monthly Salary'],
                'approved_limit': row['Approved Limit']
            }
        )
    return Customer.objects.count()

@shared_task
def ingest_loan_data(previous_task_result=None):
    
    df = pd.read_excel('loan_data.xlsx')
    for _, row in df.iterrows():
        customer_id_from_excel = int(row['Customer ID'])
        
        try:
            customer = Customer.objects.get(customer_id=customer_id_from_excel)
            Loan.objects.update_or_create(
                loan_id=row['Loan ID'],
                defaults={
                    'customer': customer,
                    'loan_amount': float(row['Loan Amount']),
                    'tenure': row['Tenure'],
                    'interest_rate': row['Interest Rate'],
                    'monthly_repayment': row['Monthly payment'],
                    'emis_paid_on_time': row['EMIs paid on Time'],
                    'start_date': row['Date of Approval'],
                    'end_date': row['End Date']
                }
            )
        except Customer.DoesNotExist:
            print(f"Skipping loan for non-existent customer ID: {customer_id_from_excel}")
    return Loan.objects.count()