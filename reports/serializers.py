from rest_framework import serializers


class DailySalesQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


class DateRangeQuerySerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)


class MonthlySalesQuerySerializer(serializers.Serializer):
    year = serializers.IntegerField(required=False)
    month = serializers.IntegerField(required=False)


class ProductMixQuerySerializer(DateRangeQuerySerializer):
    category = serializers.IntegerField(required=False, allow_null=True)


class PurchaseReportQuerySerializer(DateRangeQuerySerializer):
    supplier = serializers.IntegerField(required=False, allow_null=True)