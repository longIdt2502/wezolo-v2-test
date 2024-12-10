from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from utils.convert_response import convert_response

from bank.models import Banks


class BanksApi(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = request.GET.copy()
        banks = Banks.objects.filter(name__icontains=data.get('search')).values()

        return convert_response('success', 200, data=banks)
