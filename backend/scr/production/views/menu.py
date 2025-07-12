from django.views import generic
from ..models import ProductionPlan # Import the ProductionPlan model

    
# 生産計画
class ProductionPlanView(generic.TemplateView):
    template_name = 'production/production_plan.html'


# 使用部品
class PartsUsedView(generic.TemplateView):
    template_name = 'production/parts_used.html'


# 材料引当
class MaterialAllocationView(generic.TemplateView):
    template_name = 'production/material_allocation.html'

# 作業進捗 (生産計画一覧をAPI経由で表示)
class WorkProgressView(generic.TemplateView):
    template_name = 'production/work_progress.html'
