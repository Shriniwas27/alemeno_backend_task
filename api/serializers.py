from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'age', 'monthly_salary', 'approved_limit', 'phone_number']


class CustomerNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'phone_number', 'age']


class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerNestedSerializer(read_only=True)
    monthly_installment = serializers.FloatField(source='monthly_repayment')

    class Meta:
        model = Loan
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure']



class CustomerLoanSerializer(serializers.ModelSerializer):

    monthly_installment = serializers.FloatField(source='monthly_repayment')
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left']

    def get_repayments_left(self, obj):
        """
        Calculates the number of EMIs left to be paid.
        """
        return obj.tenure - obj.emis_paid_on_time