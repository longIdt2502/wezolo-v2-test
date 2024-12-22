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

        chatbot = Chatbot.objects.filter(oa__company_id__in=ws)
        oa = data.get('oa')
        if oa:
            chatbot = chatbot.filter(oa_id=oa)

        search = data.get('search')
        if search:
            chatbot = chatbot.filter(name__icontains=search)

        total = chatbot.count()

        question_subquery = SubqueryJsonAgg(
            ChatbotQuestion.objects.filter(answer_id=OuterRef('id')).values()
        )

        answer_subquery = SubqueryJsonAgg(
            ChatbotAnswer.objects.filter(chatbot_id=OuterRef('id')).values().annotate(
                question=question_subquery
            )
        )

        chatbot = chatbot[offset: offset + page_size].values().annotate(
            scrips=answer_subquery
        )

        return convert_response('success', 200, data=chatbot, total=total)

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

                    if item.get('type_question') == ChatbotQuestion.Type.KEYWORD:
                        for key in item.get('question', []):
                            ChatbotQuestion.objects.create(
                                content=key,
                                type=ChatbotQuestion.Type.KEYWORD,
                                answer=answer,
                                created_by=user,
                            )
                    else:
                        ChatbotQuestion.objects.create(
                            content=item.get('question'),
                            type=ChatbotQuestion.Type.QUESTION,
                            answer=answer,
                            created_by=user,
                        )

                return convert_response('success', 200, data=chatbot.id)
        except Exception as e:
            return convert_response(str(e), 400)


class ChatbotDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question_subquery = SubqueryJsonAgg(
            ChatbotQuestion.objects.filter(answer_id=OuterRef('id')).values()
        )

        answer_subquery = SubqueryJsonAgg(
            ChatbotAnswer.objects.filter(chatbot_id=OuterRef('id')).values().annotate(
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
                    questions = item.get('questions', [])
                    if item.get('id_answer'):
                        answer = ChatbotAnswer.objects.get(id=item.get('id_answer'), chatbot=chatbot)
                        is_delete = item.get('is_delete')
                        if is_delete:
                            for ques in questions:
                                if ques.get('id'):
                                    question = ChatbotQuestion.objects.get(id=ques.get('id'))
                                    question.delete()
                            answer.delete()
                            continue
                        else:
                            answer.answer = item.get('answer', answer.answer)
                            answer.type = item.get('type_answer', answer.type)
                            answer.updated_by = user
                            answer.updated_at = datetime.datetime.now()
                            answer.save()

                            for ques in questions:
                                if ques.get('id'):
                                    try:
                                        question = ChatbotQuestion.objects.get(id=ques.get('id'))
                                        if ques.get('is_delete'):
                                            question.delete()
                                        question.content = ques.get('content', question.content)
                                        question.save()
                                    except:
                                        continue
                                else:
                                    ChatbotQuestion.objects.create(
                                        content=ques.get('content'),
                                        type=ChatbotQuestion.Type.QUESTION,
                                        answer=answer,
                                        created_by=user,
                                    )
                    else:
                        answer = ChatbotAnswer.objects.create(
                            answer=item.get('answer'),
                            chatbot=chatbot,
                            type=item.get('type_answer'),
                            created_by=user,
                        )

                        for ques in questions:
                            ChatbotQuestion.objects.create(
                                content=ques.get('content'),
                                type=ChatbotQuestion.Type.QUESTION,
                                answer=answer,
                                created_by=user,
                            )
                chatbot.save()
                return convert_response('success', 200, data=chatbot.id)
        except Exception as e:
            return convert_response(str(e), 400)


class ChatbotOffApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            with transaction.atomic():
                user = request.user

                employee = Employee.objects.filter(account=user)
                ws = employee.values_list('workspace_id', flat=True)

                chatbot = Chatbot.objects.get(id=pk)

                oa = chatbot.oa
                if oa.company_id not in ws:
                    raise Exception('Bạn không có quyền truy cập OA đã chọn')
                
                if not chatbot.is_active:
                    chatbots = Chatbot.objects.filter(oa=chatbot.oa)
                    for item in chatbots:
                        item.is_active = False
                        item.save()
                chatbot.is_active = False if chatbot.is_active else True
                chatbot.save()
                return convert_response('success', 200)

        except Exception as e:
            return convert_response(str(e), 400)
