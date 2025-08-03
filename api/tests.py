from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Customer, Loan
from datetime import date

class APITests(APITestCase):

    def setUp(self):
      
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            age=30,
            monthly_salary=50000,
            approved_limit=200000,
            phone_number=1234567890
        )
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=50000,
            tenure=12,
            interest_rate=10.0,
            monthly_repayment=4629.5,
            emis_paid_on_time=5,
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 1)
        )

   
    def test_register_customer_success(self):
        url = reverse('register')
        data = {
            "first_name": "New",
            "last_name": "Customer",
            "age": 25,
            "monthly_income": 60000,
            "phone_number": 9876543210
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 2)

    def test_register_customer_missing_data(self):
        url = reverse('register')
        data = {"first_name": "Incomplete"} 
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_check_eligibility_approved(self):
        url = reverse('check-eligibility')
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 10000,
            "interest_rate": 12.0,
            "tenure": 6
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['approval'])

    def test_check_eligibility_rejected_low_score(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=300000,
            tenure=24,
            interest_rate=15.0,
            monthly_repayment=15000,
            emis_paid_on_time=1,
            start_date=date(2023, 1, 1),
            end_date=date(2025, 1, 1)
        )
        url = reverse('check-eligibility')
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 10000,
            "interest_rate": 12.0,
            "tenure": 6
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['approval'])


    def test_create_loan_success(self):
        url = reverse('create-loan')
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 25000,
            "interest_rate": 15.0,
            "tenure": 12
        }
        initial_loan_count = Loan.objects.count()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['loan_approved'])
        self.assertIsNotNone(response.data['loan_id'])
        self.assertEqual(Loan.objects.count(), initial_loan_count + 1)

    def test_create_loan_rejected(self):
       
        Loan.objects.create(customer=self.customer, loan_amount=300000, tenure=12, interest_rate=10, monthly_repayment=26000, emis_paid_on_time=0, start_date=date.today(), end_date=date.today())
        url = reverse('create-loan')
        data = {"customer_id": self.customer.customer_id, "loan_amount": 10000, "interest_rate": 12.0, "tenure": 6}
        initial_loan_count = Loan.objects.count()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['loan_approved'])
        self.assertEqual(Loan.objects.count(), initial_loan_count) 

    
    def test_view_single_loan_success(self):
        url = reverse('view-loan', kwargs={'loan_id': self.loan.loan_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['loan_id'], self.loan.loan_id)

    def test_view_single_loan_not_found(self):
        url = reverse('view-loan', kwargs={'loan_id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_view_customer_loans_success(self):
        url = reverse('view-loans', kwargs={'customer_id': self.customer.customer_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) 
        self.assertEqual(response.data[0]['loan_id'], self.loan.loan_id)
        self.assertEqual(response.data[0]['repayments_left'], 7)
