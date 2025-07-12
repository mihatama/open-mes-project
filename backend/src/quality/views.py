from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
from django.db import transaction # For atomic transactions with formsets
from django.db.models import ProtectedError
from django.forms.models import ModelChoiceIteratorValue
from .models import InspectionItem, MeasurementDetail, InspectionResult, InspectionResultDetail
from .forms import (
    InspectionItemForm, MeasurementDetailFormSet,
    InspectionResultForm, InspectionResultDetailForm
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import json

class QualityMenuView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/menu.html')

@method_decorator(login_required, name='dispatch')
class ProcessInspectionView(View):
    template_name = 'quality/process_inspection.html'

    def get(self, request, *args, **kwargs):
        inspection_items = InspectionItem.objects.filter(is_active=True).order_by('code')
        context = {'inspection_items': inspection_items, 'page_title': '工程内検査 登録'}
        return render(request, self.template_name, context)

class AcceptanceInspectionView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'quality/acceptance_inspection.html')

class InspectionItemMasterView(View):
    template_name = 'quality/master_creation.html'
    # form_class is not directly used by this view for rendering the main page's form anymore
    # as the form is now in a modal loaded via iframe.

    def get(self, request, *args, **kwargs):
        items = InspectionItem.objects.all().order_by('code')
        # The main page doesn't need the form instance directly if it's always in a modal.
        return render(request, self.template_name, {'items': items, 'page_title': '検査項目マスター管理'})


def _serialize_bound_field(bound_field):
    """Helper to convert BoundField data to a JSON-serializable format."""
    current_val = bound_field.value()
    processed_value = current_val.value if isinstance(current_val, ModelChoiceIteratorValue) else current_val

    processed_choices = []
    if hasattr(bound_field.field, 'choices'):
        for choice_val, choice_label in bound_field.field.choices:
            actual_choice_val = choice_val.value if isinstance(choice_val, ModelChoiceIteratorValue) else choice_val
            processed_choices.append((actual_choice_val, str(choice_label))) # Ensure label is string

    return {
        'label': str(bound_field.label), # Ensure label is string
        'html_name': bound_field.html_name,
        'value': processed_value,
        'errors': bound_field.errors, # ErrorList is usually fine
        'widget_type': bound_field.field.widget.__class__.__name__,
        'is_required': bound_field.field.required,
        'choices': processed_choices
    }



def inspection_item_create(request):
    if request.method == 'POST':
        form = InspectionItemForm(request.POST)
        # Initialize formset with POST data, but no instance yet for create
        formset = MeasurementDetailFormSet(request.POST, prefix='measurement_details')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    inspection_item = form.save()
                    formset.instance = inspection_item # Associate formset with the saved item
                    formset.save()
                return JsonResponse({'success': True, 'message': '検査項目を登録しました。'})
            except Exception as e:
                # Log the exception e
                return JsonResponse({'success': False, 'message': f'保存中にエラーが発生しました: {str(e)}'}, status=500)
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            for i, fs_err in enumerate(formset.errors):
                if fs_err: # fs_err is a dict of errors for that form in the formset
                    for field, error_list in fs_err.items():
                        errors[f'measurement_details-{i}-{field}'] = error_list[0]
            if formset.non_form_errors():
                 errors['formset_non_form_errors'] = formset.non_form_errors()

            return JsonResponse({'success': False, 'errors': errors, 'message': '入力内容を確認してください。'}, status=400)
            
    elif request.method == 'GET':
        # GETリクエスト時には、フォームとフォームセットの構造と初期値をJSONで返す
        form = InspectionItemForm()
        formset = MeasurementDetailFormSet(prefix='measurement_details', instance=InspectionItem())

        form_fields_data = {
            field_name: _serialize_bound_field(form[field_name])
            for field_name in form.fields
        }

        # フォームセットの情報を準備
        formset_data = {
            'prefix': formset.prefix,
            'management_form': {key: formset.management_form[key].value() for key in formset.management_form.fields},
            'forms': [] # 新規作成時は空
        }
        empty_form_fields_data = {
            field_name: _serialize_bound_field(formset.empty_form[field_name])
            for field_name in formset.empty_form.fields
        }

        return JsonResponse({
            'form_data': form_fields_data,
            'formset_data': formset_data,
            'empty_form_fields_data': empty_form_fields_data,
            'page_title': '新規検査項目登録'
        })
    return JsonResponse({'success': False, 'message': '無効なリクエストメソッドです。'}, status=405)


def inspection_item_update(request, pk):
    item = get_object_or_404(InspectionItem, pk=pk)
    if request.method == 'POST':
        form = InspectionItemForm(request.POST, instance=item)
        formset = MeasurementDetailFormSet(request.POST, instance=item, prefix='measurement_details')
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                return JsonResponse({'success': True, 'message': '検査項目を更新しました。'})
            except Exception as e:
                # Log the exception e
                return JsonResponse({'success': False, 'message': f'更新中にエラーが発生しました: {str(e)}'}, status=500)
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            for i, fs_err in enumerate(formset.errors):
                if fs_err:
                    for field, error_list in fs_err.items():
                        errors[f'measurement_details-{i}-{field}'] = error_list[0]
            if formset.non_form_errors():
                 errors['formset_non_form_errors'] = formset.non_form_errors()
            return JsonResponse({'success': False, 'errors': errors, 'message': '入力内容を確認してください。'}, status=400)

    elif request.method == 'GET':
        # GETリクエスト時には、フォームとフォームセットの構造と初期値をJSONで返す
        form = InspectionItemForm(instance=item)
        formset = MeasurementDetailFormSet(instance=item, prefix='measurement_details')

        form_fields_data = {
            field_name: _serialize_bound_field(form[field_name])
            for field_name in form.fields
        }

        formset_data = {
            'prefix': formset.prefix,
            'management_form': {
                key: formset.management_form[key].value() for key in formset.management_form.fields
            },
            'forms': []
        }
        for sub_form in formset.forms:
            serialized_sub_form_fields = {
                field_name: _serialize_bound_field(sub_form[field_name])
                for field_name in sub_form.fields
            }
            formset_data['forms'].append({
                'id': sub_form.instance.pk if sub_form.instance.pk else None,
                'fields': serialized_sub_form_fields,
                'can_delete': bool(sub_form.instance.pk)
            })

        return JsonResponse({
            'form_data': form_fields_data,
            'formset_data': formset_data,
            'empty_form_fields_data': {field_name: _serialize_bound_field(formset.empty_form[field_name]) for field_name in formset.empty_form.fields}, # For adding new rows dynamically
            'page_title': f'検査項目変更: {item.name}'
        })
    return JsonResponse({'success': False, 'message': '無効なリクエストメソッドです。'}, status=405)


def inspection_item_delete(request, pk):
    item = get_object_or_404(InspectionItem, pk=pk)
    if request.method == 'POST':
        try:
            item_code = item.code
            item.delete()
            return JsonResponse({'success': True, 'message': f'検査項目「{item_code}」を削除しました。'})
        except ProtectedError:
            return JsonResponse({
                'success': False,
                'message': f'検査項目「{item.code}」は実績データが関連付けられているため削除できません。'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'削除中にエラーが発生しました: {str(e)}'
            }, status=400)
    return JsonResponse({'success': False, 'message': '無効なリクエストです。'}, status=405)

@login_required
def get_inspection_item_form_data(request, item_pk):
    inspection_item = get_object_or_404(InspectionItem, pk=item_pk)
    measurement_details = inspection_item.measurement_details.all().order_by('order', 'name')

    item_data = {
        'id': str(inspection_item.id),
        'code': inspection_item.code,
        'name': inspection_item.name,
        'description': inspection_item.description,
    }

    measurement_details_data = []
    for md in measurement_details:
        measurement_details_data.append({
            'id': str(md.id),
            'name': md.name,
            'measurement_type': md.measurement_type,
            'specification_nominal': md.specification_nominal,
            'specification_upper_limit': md.specification_upper_limit,
            'specification_lower_limit': md.specification_lower_limit,
            'specification_unit': md.specification_unit,
            'expected_qualitative_result': md.expected_qualitative_result,
            'order': md.order,
        })

    result_form_fields = [
        {'name': 'part_number', 'label': '品番', 'type': 'text', 'class': 'col-md-6'},
        {'name': 'lot_number', 'label': 'ロット番号', 'type': 'text', 'class': 'col-md-6'},
        {'name': 'serial_number', 'label': 'シリアル番号', 'type': 'text', 'class': 'col-md-6'},
        {'name': 'quantity_inspected', 'label': '検査数量', 'type': 'number', 'class': 'col-md-6'},
        {'name': 'related_order_type', 'label': '関連オーダータイプ', 'type': 'text', 'class': 'col-md-6'},
        {'name': 'related_order_number', 'label': '関連オーダー番号', 'type': 'text', 'class': 'col-md-6'},
        {'name': 'equipment_used', 'label': '使用設備/測定器', 'type': 'text', 'class': 'col-md-12'},
        {'name': 'judgment', 'label': '総合判定', 'type': 'select', 'choices': InspectionResult.JUDGMENT_CHOICES, 'class': 'col-md-6'},
        {'name': 'attachment', 'label': '添付ファイル', 'type': 'file', 'class': 'col-md-6'},
        {'name': 'remarks', 'label': '備考', 'type': 'textarea', 'class': 'col-md-12'},
    ]

    return JsonResponse({
        'success': True,
        'inspection_item': item_data,
        'measurement_details': measurement_details_data,
        'result_form_fields': result_form_fields
    })

@login_required
@transaction.atomic
def record_inspection_result_view(request, item_pk):
    inspection_item = get_object_or_404(InspectionItem, pk=item_pk)

    if request.method == 'POST':
        result_form_data = request.POST.copy()
        result_form_data['inspection_item'] = inspection_item.pk
        result_form = InspectionResultForm(result_form_data, request.FILES)

        try:
            measurement_details_payload = json.loads(request.POST.get('measurement_details_payload', '[]'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '検査詳細の形式が無効です。'}, status=400)

        valid_detail_forms = []
        all_details_data_valid = True
        detail_errors = {}

        if result_form.is_valid():
            inspection_result = result_form.save(commit=False)
            inspection_result.inspected_by = request.user
            inspection_result.inspected_at = timezone.now()

            for idx, detail_data in enumerate(measurement_details_payload):
                md_pk = detail_data.get('measurement_detail_id')
                if not md_pk:
                    all_details_data_valid = False; detail_errors[f'detail_{idx}'] = '測定項目IDがありません。'; break
                
                try:
                    measurement_detail_instance = MeasurementDetail.objects.get(pk=md_pk, inspection_item=inspection_item)
                except MeasurementDetail.DoesNotExist:
                    all_details_data_valid = False; detail_errors[f'detail_{idx}'] = '無効な測定項目です。'; break

                form_data_for_detail = {'measurement_detail': measurement_detail_instance.pk}
                if measurement_detail_instance.measurement_type == 'quantitative':
                    form_data_for_detail['measured_value_numeric'] = detail_data.get('value')
                else:
                    form_data_for_detail['result_qualitative'] = detail_data.get('value')
                
                detail_form = InspectionResultDetailForm(form_data_for_detail, measurement_detail_instance=measurement_detail_instance)
                if detail_form.is_valid():
                    valid_detail_forms.append(detail_form)
                else:
                    all_details_data_valid = False
                    detail_errors[f'detail_{idx}_{measurement_detail_instance.name}'] = detail_form.errors.as_text()
            
            if all_details_data_valid:
                inspection_result.save()
                for detail_form_instance in valid_detail_forms:
                    result_detail = detail_form_instance.save(commit=False)
                    result_detail.inspection_result = inspection_result
                    result_detail.save()
                return JsonResponse({'success': True, 'message': '検査結果を登録しました。'})
            else:
                errors = {f: e[0] for f, e in result_form.errors.items()}
                errors.update(detail_errors)
                return JsonResponse({'success': False, 'message': '入力内容に誤りがあります（詳細）。', 'errors': errors}, status=400)
        else:
            errors = {f: e[0] for f, e in result_form.errors.items()}
            errors.update(detail_errors) # Include any parsing errors for details if they occurred before form validation
            return JsonResponse({'success': False, 'message': '入力内容に誤りがあります。', 'errors': errors}, status=400)

    return JsonResponse({'success': False, 'message': 'POSTリクエストが必要です。'}, status=405)
