from django.db import transaction
from django.db.models import OuterRef
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.core.subquery import *

from utils.convert_response import convert_response

from chatbot.models import ChatbotCampaign, ChatbotAnswer, ChatbotQuestion
from employee.models import Employee
from zalo.models import ZaloOA


class ChatbotApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size

        employee = Employee.objects.filter(account=user)
        ws = employee.values_list('workspace_id', flat=True)
        campaign = ChatbotCampaign.objects.filter(oa__company_id__in=ws)

        search = data.get('search')
        if search:
            campaign = campaign.filter(name__icontains=search)

        total = campaign.count()

        question_subquery = SubqueryJson(
            ChatbotQuestion.objects.filter(answer_id=OuterRef('id')).values()[:1]
        )

        answer_subquery = SubqueryJsonAgg(
            ChatbotAnswer.objects.filter(campaign_id=OuterRef('id')).values().annotate(
                question=question_subquery
            )
        )

        campaign = campaign[offset: offset + page_size].values().annotate(
            scrips=answer_subquery
        )

        return convert_response('success', 200, data=campaign, total=total)

    def post(self, request):
        try:
            with transaction.atomic():
                user = request.user
                data = request.data.copy()

                employee = Employee.objects.filter(account=user)
                ws = employee.values_list('workspace_id', flat=True)

                oa_id = data.get('oa')
                oa = ZaloOA.objects.get(id=oa_id)
                if oa.company_id not in ws:
                    raise Exception('Bạn không có quyền truy cập OA đã chọn')

                campaign = ChatbotCampaign.objects.create(
                    name=data.get('name'),
                    oa=oa,
                    index=data.get('index'),
                    created_by=user
                )

                for item in data.get('scripts', []):
                    answer = ChatbotAnswer.objects.create(
                        answer=item.get('answer'),
                        campaign=campaign,
                        type=item.get('type_answer'),
                        created_by=user,
                    )

                    question = ChatbotQuestion.objects.create(
                        content=item.get('question'),
                        type=item.get('type_question'),
                        answer=answer,
                        created_by=user,
                    )

                return convert_response('success', 200, data=campaign.id)
        except Exception as e:
            return convert_response(str(e), 400)
