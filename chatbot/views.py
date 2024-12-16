import datetime

from django.db import transaction
from django.db.models import OuterRef
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.core.subquery import *

from utils.convert_response import convert_response

from chatbot.models import Chatbot, ChatbotAnswer, ChatbotQuestion
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
        campaign = Chatbot.objects.filter(oa__company_id__in=ws)

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

                chatbot = Chatbot.objects.create(
                    name=data.get('name'),
                    oa=oa,
                    index=data.get('index'),
                    created_by=user
                )

                for item in data.get('scripts', []):
                    answer = ChatbotAnswer.objects.create(
                        answer=item.get('answer'),
                        chatbot=chatbot,
                        type=item.get('type_answer'),
                        created_by=user,
                    )

                    question = ChatbotQuestion.objects.create(
                        content=item.get('question'),
                        type=item.get('type_question'),
                        answer=answer,
                        created_by=user,
                    )

                return convert_response('success', 200, data=chatbot.id)
        except Exception as e:
            return convert_response(str(e), 400)


class ChatbotDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question_subquery = SubqueryJson(
            ChatbotQuestion.objects.filter(answer_id=OuterRef('id')).values()[:1]
        )

        answer_subquery = SubqueryJsonAgg(
            ChatbotAnswer.objects.filter(campaign_id=OuterRef('id')).values().annotate(
                question=question_subquery
            )
        )
        chatbot = Chatbot.objects.filter(id=pk).values().annotate(
            scrips=answer_subquery
        )[:1]

        return convert_response('success', 200, data=chatbot)

    def put(self, request, pk):
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

                chatbot = Chatbot.objects.get(id=pk)
                chatbot.updated_by = user
                chatbot.name = data.get('name', chatbot.name)
                chatbot.index = data.get('index', chatbot.index)

                for item in data.get('scripts', []):
                    if item.get('id_answer'):
                        answer = ChatbotAnswer.objects.get(id=item.get('id_answer'))
                        answer.answer = item.get('answer', answer.answer)
                        answer.type = item.get('type_answer', answer.type)
                        answer.updated_by = user
                        answer.updated_at = datetime.datetime.now()
                        answer.save()
                    else:
                        answer = ChatbotAnswer.objects.create(
                            answer=item.get('answer'),
                            chatbot=chatbot,
                            type=item.get('type_answer'),
                            created_by=user,
                        )

                    if item.get('id_question'):
                        question = ChatbotQuestion.objects.get(id=item.get('id_answer'))
                        question.content = item.get('question', question.content)
                        question.type = item.get('type_question', question.type)
                        question.updated_by = user
                        question.updated_at = datetime.datetime.now()
                        question.save()
                    else:
                        question = ChatbotQuestion.objects.create(
                            content=item.get('question'),
                            type=item.get('type_question'),
                            answer=answer,
                            created_by=user,
                        )

                return convert_response('success', 200, data=chatbot.id)
        except Exception as e:
            return convert_response(str(e), 400)
