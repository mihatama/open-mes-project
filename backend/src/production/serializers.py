from rest_framework import serializers
from .models import ProductionPlan, PartsUsed # PartsUsed をインポート

class ProductionPlanSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True) # 表示名用
    # status フィールドはモデルの定義に従い、内部キーを返します。

    class Meta:
        model = ProductionPlan
        fields = [
            'id',
            'plan_name',
            'product_code',
            'production_plan', # FK to another ProductionPlan (referenced plan)
            'planned_quantity',
            'planned_start_datetime',
            'planned_end_datetime',
            'actual_start_datetime',
            'actual_end_datetime',
            'status', # ステータスの内部キー (例: 'PENDING', 'IN_PROGRESS')
            'status_display', # ステータスの表示名 (例: '未着手', '進行中')
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display']

    def validate(self, data):
        """
        Check that planned_start_datetime is before planned_end_datetime.
        Handles both create (POST) and partial update (PATCH) scenarios.
        """
        # On updates (PATCH), self.instance will be populated.
        # On creates (POST), self.instance will be None.

        # Determine the start and end datetimes to validate.
        # Use the incoming data if present, otherwise fall back to the existing instance's value (for PATCH).
        if self.instance:  # This is an update
            planned_start = data.get('planned_start_datetime', self.instance.planned_start_datetime)
            planned_end = data.get('planned_end_datetime', self.instance.planned_end_datetime)
        else:  # This is a create
            # For create, model fields planned_start_datetime and planned_end_datetime are required.
            # DRF would have raised a "this field is required" error already if not present.
            planned_start = data.get('planned_start_datetime')
            planned_end = data.get('planned_end_datetime')

        # Only proceed with validation if both dates are available.
        # This check is mostly for safety; for create, they are required by the model,
        # and for update, we've fetched them from data or instance.
        if planned_start is not None and planned_end is not None:
            if planned_start >= planned_end:
                # The error message points to 'planned_end_datetime'.
                # A more general message could be:
                # "Planned start datetime must be before planned end datetime."
                raise serializers.ValidationError({
                    "planned_end_datetime": "Planned end datetime must be after planned start datetime."
                })
        return data

class PartsUsedSerializer(serializers.ModelSerializer):
    """
    使用部品モデルのためのシリアライザ
    """
    class Meta:
        model = PartsUsed
        fields = [
            'id',
            'production_plan', # 生産計画へのForeignKey
            'part_code',
            'warehouse', # 追加
            'quantity_used',
            'used_datetime',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RequiredPartSerializer(serializers.Serializer):
    """
    必要部品情報を表現するためのシリアライザ。
    特定のモデルに直接紐づかないため、serializers.Serializerを継承します。
    """
    part_code = serializers.CharField(max_length=100)
    part_name = serializers.CharField(max_length=255, help_text="部品名")
    # required_quantity の型 (DecimalField, IntegerField など) は、
    # PartsUsed.quantity_used is PositiveIntegerField, MaterialAllocation.allocated_quantity is PositiveIntegerField.
    required_quantity = serializers.IntegerField(help_text="必要数量")
    unit = serializers.CharField(max_length=50, help_text="単位")
    inventory_quantity = serializers.IntegerField(help_text="現在の在庫数量")
    already_allocated_quantity = serializers.IntegerField(help_text="既にこの生産計画に引当済の数量", default=0)
    warehouse = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, help_text="部品が使用される倉庫")

    # このシリアライザは読み取り専用のデータを想定しています。
    # ビュー側で `data_for_serializer` を構築する際に、これらのフィールドに合致するデータを提供します。