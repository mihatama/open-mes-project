from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Machine
from .serializers import MachineSerializer, MachineCreateUpdateSerializer
from master.rest_views import CustomSuccessMessageMixin

class MachineViewSet(CustomSuccessMessageMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing machines.
    """
    queryset = Machine.objects.all().order_by('machine_number')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list']:
            return MachineSerializer
        return MachineCreateUpdateSerializer