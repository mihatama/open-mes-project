from .views import PurchaseOrderCSVTemplateView, PurchaseOrderImportCSVView
# If other views from views.py or other modules within inventory/views/
# need to be accessible via `inventory.views.something`, import them here.
# For example, if menu.py views are accessed as inventory.views.menu.SpecificView,
# then `from . import menu` might be here, or urls.py would import from .views.menu directly.