import json
import random
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from utils.convert_response import convert_response
from common.s3 import AwsS3

from .models import Campaign, CampaignMessage, CampaignZns, StatusMessage

# Create your views here.
class CampaignApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user
        data = json.loads(request.POST.get('data'))
        image = request.FILES.get('image')
        if image:
            r = random.randint(100000, 999999)
            file_name = f"{r}.png"
            file = ContentFile(image.read(), name=file_name)
            url_file = AwsS3.upload_file(file, 'campaign/')
            data['message_file'] = {
                "type": "template",
                "payload": {
                    "template_type": "media",
                    "elements": [{
                        "media_type": "image",
                        "url": url_file
                    }]
                }
            }
        token_file = data.get('token_file')
        if token_file:
            data['message_file'] = {
                "type": "file",
                "payload": {
                    "token": token_file
                }
            }
        data['created_by'] = user.id
        campaign = Campaign().from_json(data=data)
        
        if campaign.type == Campaign.Type.MESSAGE:
            user_zalos = data.get('user_zalos', [])
            for id in user_zalos: 
                CampaignMessage.objects.create(
                    campaign=campaign,
                    user_zalo_id=id,
                    status=StatusMessage.PENDING
                )
        if campaign.type == Campaign.Type.ZNS:
            customers = data.get('customers', [])
            for id in customers: 
                CampaignZns.objects.create(
                    campaign=campaign,
                    customer_id=id,
                    status=StatusMessage.PENDING,
                    zns_id=data.get('zns')
                )

        return convert_response('success', 200, data=campaign.id)
