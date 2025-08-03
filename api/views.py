from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from datetime import date
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanDetailSerializer


def calculate_credit_score(customer):
    """
    Calculates a credit score for a customer based on historical loan data.
    """
    loans = Loan.objects.filter(customer=customer)
    
    sum_current_loans = loans.aggregate(total=Sum('loan_amount'))['total'] or 0
    if sum_current_loans > customer.approved_limit:
        return 0

    score = 100

    if loans.count() > 10:
        score -= 15

    current_year_loans = loans.filter(start_date__year=date.today().year).count()
    score -= (current_year_loans * 10)

    past_loans_due = loans.filter(end_date__lt=date.today())
    for loan in past_loans_due:
        if loan.emis_paid_on_time < loan.tenure:
            score -= 20 
    
    return max(0, score)



class RegisterView(APIView):
    def post(self, request):
        data = request.data
        monthly_salary = data.get('monthly_income')

        if not monthly_salary:
            return Response({"error": "monthly_income is required"}, status=status.HTTP_400_BAD_REQUEST)

        
        approved_limit = round(36 * monthly_salary / 100000) * 100000

        customer = Customer.objects.create(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            age=data.get('age'),
            monthly_salary=monthly_salary,
            approved_limit=approved_limit,
            phone_number=data.get('phone_number')
        )
        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CheckEligibilityView(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        if not all([customer_id, loan_amount, interest_rate, tenure]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        credit_score = calculate_credit_score(customer)
        
        sum_current_emis = Loan.objects.filter(customer=customer).aggregate(total=Sum('monthly_repayment'))['total'] or 0
        if sum_current_emis > customer.monthly_salary / 2:
            return Response({
                "approval": False,
                "message": "High EMI burden: Sum of current EMIs exceeds 50% of monthly salary."
            }, status=status.HTTP_200_OK)

        approval = False
        corrected_interest_rate = interest_rate

        if credit_score > 50:
            approval = True
        elif 30 < credit_score <= 50:
            approval = True
            if interest_rate <= 12.0:
                corrected_interest_rate = 12.0
        elif 10 < credit_score <= 30:
            approval = True
            if interest_rate <= 16.0:
                corrected_interest_rate = 16.0
        
       
        monthly_installment = 0
        if approval:
            monthly_interest_rate = corrected_interest_rate / 12 / 100
            if monthly_interest_rate == 0:
                monthly_installment = loan_amount / tenure if tenure > 0 else 0
            else:
                monthly_installment = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate)**tenure) / ((1 + monthly_interest_rate)**tenure - 1)

        return Response({
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate if approval else None,
            "tenure": tenure,
            "monthly_installment": round(monthly_installment, 2) if approval else None
        }, status=status.HTTP_200_OK)


class CreateLoanView(APIView):
    def post(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        if not all([customer_id, loan_amount, interest_rate, tenure]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        credit_score = calculate_credit_score(customer)
        sum_current_emis = Loan.objects.filter(customer=customer).aggregate(total=Sum('monthly_repayment'))['total'] or 0

        approval = True
        message = ""

        if sum_current_emis > customer.monthly_salary / 2:
            approval = False
            message = "High EMI burden."
        elif credit_score <= 10:
            approval = False
            message = "Credit score is too low."
        
       
        corrected_interest_rate = interest_rate
        if approval:
            if 30 < credit_score <= 50 and interest_rate < 12.0:
                approval = False
                message = f"Interest rate must be > 12% for your credit score ({credit_score})."
            elif 10 < credit_score <= 30 and interest_rate < 16.0:
                approval = False
                message = f"Interest rate must be > 16% for your credit score ({credit_score})."
        
        if not approval:
            return Response({
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": message,
                "monthly_installment": None
            }, status=status.HTTP_200_OK)

    
        monthly_interest_rate = corrected_interest_rate / 12 / 100
        if monthly_interest_rate == 0:
            monthly_installment = loan_amount / tenure if tenure > 0 else 0
        else:
            monthly_installment = (loan_amount * monthly_interest_rate * (1 + monthly_interest_rate)**tenure) / ((1 + monthly_interest_rate)**tenure - 1)
        
        new_loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=corrected_interest_rate,
            monthly_repayment=monthly_installment,
            emis_paid_on_time=0,
            start_date=date.today(),
            end_date=date.today() 
        )

        return Response({
            "loan_id": new_loan.loan_id,
            "customer_id": customer_id,
            "loan_approved": True,
            "message": "Loan approved successfully!",
            "monthly_installment": round(monthly_installment, 2)
        }, status=status.HTTP_201_CREATED)



class ViewLoanView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(pk=loan_id)
            serializer = LoanDetailSerializer(loan)
            return Response(serializer.data)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)



class ViewCustomerLoansView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        
        loans = Loan.objects.filter(customer=customer)
        response_data = []
        for loan in loans:
            repayments_left = loan.tenure - loan.emis_paid_on_time
            response_data.append({
                "loan_id": loan.loan_id,
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "repayments_left": repayments_left
            })
        return Response(response_data)
