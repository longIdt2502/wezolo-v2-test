from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, OuterRef, Count

from common.core.subquery import *
from utils.convert_response import convert_response

from zalo.models import ZaloOA, UserZalo
from workspace.models import Workspace


class ZaloAdminList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = request.GET.copy()
        page_size = int(data.get('page_size', 20))
        offset = (int(data.get('page', 1)) - 1) * page_size
        user = request.user
        if not user.is_superuser:
            return convert_response('Truy cập bị từ chối', 403)

        oa = ZaloOA.objects.filter()
        total = oa.count()

        search = data.get('search')
        if search:
            oa = oa.filter(Q(oa_name__icontains=search))

        oa = oa[offset: offset + page_size].values().annotate(
            customer_contact=Subquery(
                UserZalo.objects.filter(oa_id=OuterRef('id')).values('id').annotate(
                    total=Count('id')
                ).values('total')
            ),
            workspace=SubqueryJson(
                Workspace.objects.filter(id=OuterRef('company_id')).values()[:1]
            )
        )

        return convert_response('success', 200, data={
            "data": oa,
            "total": total
        })
