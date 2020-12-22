# encoding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict
from djenga.db import TimestampField
from djenga.mixins.jsonmixin import JsonMixin


class ActiveSalesReportAggregated(models.Model):
    store_id = models.IntegerField()
    period = models.IntegerField()
    orders = models.IntegerField()
    revenue = models.DecimalField(max_digits=12, decimal_places=2)
    aov = models.DecimalField(max_digits=12, decimal_places=2)
    cogs = models.DecimalField(max_digits=12, decimal_places=2)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2)
    gross_margin = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'active_sales_report_aggregated'


class Adjreminder(models.Model):
    reminder_id = models.AutoField(primary_key=True)
    store_id = models.SmallIntegerField()
    customer_id = models.IntegerField()
    order_id = models.IntegerField()
    status = models.CharField(max_length=12)
    created_at = TimestampField(blank=True, null=True)
    sheduled_at = models.DateTimeField(blank=True, null=True)
    customer_email = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    products = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'adjreminder'


class AdjreminderHistory(models.Model):
    order_id = models.IntegerField()
    customer_id = models.IntegerField()
    sent_at = models.DateTimeField()
    visited_from = models.CharField(max_length=32)
    visited_at = models.DateTimeField(blank=True, null=True)
    customer_name = models.CharField(max_length=255)
    customer_email = models.CharField(max_length=255)
    txt = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'adjreminder_history'


class AdjreminderProduct(models.Model):
    product_id = models.IntegerField()
    store_id = models.SmallIntegerField()
    email = models.CharField(max_length=128)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'adjreminder_product'


class AdjreminderStoplist(models.Model):
    stoplist_id = models.AutoField(primary_key=True)
    store_id = models.SmallIntegerField()
    email = models.CharField(max_length=128)
    date = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'adjreminder_stoplist'


class AdminAssert(models.Model):
    assert_id = models.AutoField(primary_key=True)
    assert_type = models.CharField(max_length=20, blank=True, null=True)
    assert_data = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'admin_assert'


class AdminRole(models.Model):
    role_id = models.AutoField(primary_key=True)
    parent_id = models.IntegerField()
    tree_level = models.SmallIntegerField()
    sort_order = models.SmallIntegerField()
    role_type = models.CharField(max_length=1)
    user_id = models.IntegerField()
    role_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'admin_role'


class AdminRule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(AdminRole, models.DO_NOTHING, related_name='+')
    resource_id = models.CharField(max_length=255, blank=True, null=True)
    privileges = models.CharField(max_length=20, blank=True, null=True)
    assert_id = models.IntegerField()
    role_type = models.CharField(max_length=1, blank=True, null=True)
    permission = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'admin_rule'


class AdminUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=32, blank=True, null=True)
    lastname = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(unique=True, max_length=40, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField()
    modified = models.DateTimeField(blank=True, null=True)
    logdate = models.DateTimeField(blank=True, null=True)
    lognum = models.SmallIntegerField()
    reload_acl_flag = models.SmallIntegerField()
    is_active = models.SmallIntegerField()
    extra = models.TextField(blank=True, null=True)
    rp_token = models.TextField(blank=True, null=True)
    rp_token_created_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'admin_user'


class AdminnotificationInbox(models.Model):
    notification_id = models.AutoField(primary_key=True)
    severity = models.SmallIntegerField()
    date_added = models.DateTimeField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.SmallIntegerField()
    is_remove = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'adminnotification_inbox'


class AitsysNews(models.Model):
    entity_id = models.AutoField(primary_key=True)
    date_added = models.DateTimeField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=9)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aitsys_news'


class AitsysStatus(models.Model):
    module = models.CharField(max_length=50)
    status = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aitsys_status'


class AmNotfoundAttempt(models.Model):
    attempt_id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    user = models.CharField(max_length=255)
    client_ip = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'am_notfound_attempt'


class AmNotfoundError(models.Model):
    error_id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    type = models.IntegerField()
    error = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'am_notfound_error'


class AmNotfoundLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    store_id = models.SmallIntegerField()
    date = models.DateTimeField()
    url = models.CharField(max_length=255)
    referer = models.TextField()
    client_ip = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'am_notfound_log'


class Api2AclAttribute(models.Model):
    entity_id = models.AutoField(primary_key=True)
    user_type = models.CharField(max_length=20)
    resource_id = models.CharField(max_length=255)
    operation = models.CharField(max_length=20)
    allowed_attributes = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api2_acl_attribute'
        unique_together = (('user_type', 'resource_id', 'operation'),)


class Api2AclRole(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_at = TimestampField()
    updated_at = TimestampField(blank=True, null=True)
    role_name = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api2_acl_role'


class Api2AclRule(models.Model):
    entity_id = models.AutoField(primary_key=True)
    role = models.OneToOneField(Api2AclRole, models.DO_NOTHING, related_name='+')
    resource_id = models.CharField(max_length=255)
    privilege = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api2_acl_rule'
        unique_together = (('role', 'resource_id', 'privilege'),)


class Api2AclUser(models.Model):
    admin = models.OneToOneField(AdminUser, models.DO_NOTHING, unique=True, related_name='+')
    role = models.ForeignKey(Api2AclRole, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api2_acl_user'


class ApiAssert(models.Model):
    assert_id = models.AutoField(primary_key=True)
    assert_type = models.CharField(max_length=20, blank=True, null=True)
    assert_data = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api_assert'


class ApiRole(models.Model):
    role_id = models.AutoField(primary_key=True)
    parent_id = models.IntegerField()
    tree_level = models.SmallIntegerField()
    sort_order = models.SmallIntegerField()
    role_type = models.CharField(max_length=1)
    user_id = models.IntegerField()
    role_name = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api_role'


class ApiRule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    role = models.ForeignKey(ApiRole, models.DO_NOTHING, related_name='+')
    resource_id = models.CharField(max_length=255, blank=True, null=True)
    api_privileges = models.CharField(max_length=20, blank=True, null=True)
    assert_id = models.IntegerField()
    role_type = models.CharField(max_length=1, blank=True, null=True)
    api_permission = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api_rule'


class ApiSession(models.Model):
    user = models.ForeignKey('ApiUser', models.DO_NOTHING, related_name='+')
    logdate = models.DateTimeField()
    sessid = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api_session'


class ApiUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    firstname = models.CharField(max_length=32, blank=True, null=True)
    lastname = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=40, blank=True, null=True)
    api_key = models.CharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField()
    modified = models.DateTimeField(blank=True, null=True)
    lognum = models.SmallIntegerField()
    reload_acl_flag = models.SmallIntegerField()
    is_active = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'api_user'


class AwPquestion2Answer(models.Model):
    entity_id = models.AutoField(primary_key=True)
    question = models.ForeignKey('AwPquestion2Question', models.DO_NOTHING, related_name='+')
    author_name = models.CharField(max_length=255)
    author_email = models.CharField(max_length=255)
    customer_id = models.IntegerField(blank=True, null=True)
    status = models.SmallIntegerField()
    created_at = TimestampField()
    content = models.TextField()
    helpfulness = models.IntegerField()
    is_admin = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_answer'


class AwPquestion2NotificationQueue(models.Model):
    entity_id = models.AutoField(primary_key=True)
    notification_type = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=255)
    sender_email = models.CharField(max_length=255)
    sender_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = TimestampField()
    sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_notification_queue'


class AwPquestion2NotificationSubscriber(models.Model):
    entity_id = models.AutoField(primary_key=True)
    customer_id = models.IntegerField()
    customer_email = models.CharField(max_length=255)
    website_id = models.SmallIntegerField()
    notification_type = models.CharField(max_length=255)
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_notification_subscriber'
        unique_together = (('customer_email', 'website_id', 'notification_type'),)


class AwPquestion2Question(models.Model):
    entity_id = models.AutoField(primary_key=True)
    author_name = models.CharField(max_length=255)
    author_email = models.CharField(max_length=255)
    customer_id = models.IntegerField()
    created_at = TimestampField()
    content = models.TextField()
    product_id = models.IntegerField()
    store_id = models.SmallIntegerField()
    show_in_store_ids = models.CharField(max_length=255)
    status = models.SmallIntegerField()
    visibility = models.SmallIntegerField()
    sharing_type = models.SmallIntegerField()
    sharing_value = models.TextField(blank=True, null=True)
    helpfulness = models.IntegerField()
    added_from_category_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_question'


class AwPquestion2SummaryAnswer(models.Model):
    entity_id = models.AutoField(primary_key=True)
    answer = models.ForeignKey(AwPquestion2Answer, models.DO_NOTHING, related_name='+')
    customer_id = models.IntegerField(blank=True, null=True)
    visitor_id = models.IntegerField(blank=True, null=True)
    helpful = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_summary_answer'


class AwPquestion2SummaryQuestion(models.Model):
    entity_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(AwPquestion2Question, models.DO_NOTHING, related_name='+')
    customer_id = models.IntegerField()
    visitor_id = models.IntegerField(blank=True, null=True)
    helpful = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'aw_pquestion2_summary_question'


class CaptchaLog(models.Model):
    type = models.CharField(max_length=32)
    value = models.CharField(max_length=32)
    count = models.IntegerField()
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'captcha_log'
        unique_together = (('type', 'value'),)


class CatalogCategoryAncCategsIndexIdx(models.Model):
    category_id = models.IntegerField()
    path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_anc_categs_index_idx'


class CatalogCategoryAncCategsIndexTmp(models.Model):
    category_id = models.IntegerField()
    path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_anc_categs_index_tmp'


class CatalogCategoryAncProductsIndexIdx(models.Model):
    category_id = models.IntegerField()
    product_id = models.IntegerField()
    position = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_anc_products_index_idx'


class CatalogCategoryAncProductsIndexTmp(models.Model):
    category_id = models.IntegerField()
    product_id = models.IntegerField()
    position = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_anc_products_index_tmp'


class CatalogCategoryEntity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute_set_id = models.SmallIntegerField()
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity'


class CatalogCategoryEntityDatetime(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    value = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity_datetime'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogCategoryEntityDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity_decimal'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogCategoryEntityInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    value = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity_int'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogCategoryEntityText(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity_text'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogCategoryEntityVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_entity_varchar'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogCategoryFlatStore1(models.Model):
    entity = models.OneToOneField(CatalogCategoryEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    all_children = models.TextField(blank=True, null=True)
    available_sort_by = models.TextField(blank=True, null=True)
    bottom_block_content = models.TextField(blank=True, null=True)
    children = models.TextField(blank=True, null=True)
    custom_apply_to_products = models.IntegerField(blank=True, null=True)
    custom_design = models.CharField(max_length=255, blank=True, null=True)
    custom_design_from = models.DateTimeField(blank=True, null=True)
    custom_design_to = models.DateTimeField(blank=True, null=True)
    custom_layout_update = models.TextField(blank=True, null=True)
    custom_use_parent_settings = models.IntegerField(blank=True, null=True)
    default_sort_by = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_mode = models.CharField(max_length=255, blank=True, null=True)
    filter_price_range = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    include_in_menu = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_anchor = models.IntegerField(blank=True, null=True)
    is_landing = models.IntegerField(blank=True, null=True)
    is_top_subcategory = models.IntegerField(blank=True, null=True)
    landing_page = models.IntegerField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    page_layout = models.CharField(max_length=255, blank=True, null=True)
    path_in_store = models.TextField(blank=True, null=True)
    searchindex_weight = models.TextField(blank=True, null=True)
    sw_cat_block_bottom = models.TextField(blank=True, null=True)
    sw_cat_block_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_left = models.TextField(blank=True, null=True)
    sw_cat_block_position = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_right = models.TextField(blank=True, null=True)
    sw_cat_block_top = models.TextField(blank=True, null=True)
    sw_cat_block_type = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_icon = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_label = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_left_block_width = models.TextField(blank=True, null=True)
    sw_cat_right_block_width = models.TextField(blank=True, null=True)
    sw_cat_static_width = models.TextField(blank=True, null=True)
    sw_gr_cat_alt_img_col = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_alt_img_col_val = models.TextField(blank=True, null=True)
    sw_gr_cat_aspect_ratio = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_banner = models.TextField(blank=True, null=True)
    sw_gr_cat_banner_style = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_custom_left = models.TextField(blank=True, null=True)
    sw_gr_cat_custom_right = models.TextField(blank=True, null=True)
    sw_gr_cat_hover_effect = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_position = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_ratio_height = models.TextField(blank=True, null=True)
    sw_gr_cat_ratio_width = models.TextField(blank=True, null=True)
    sw_gr_filter_position = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    top_block_content = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_flat_store_1'


class CatalogCategoryFlatStore2(models.Model):
    entity = models.OneToOneField(CatalogCategoryEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    all_children = models.TextField(blank=True, null=True)
    available_sort_by = models.TextField(blank=True, null=True)
    bottom_block_content = models.TextField(blank=True, null=True)
    children = models.TextField(blank=True, null=True)
    custom_apply_to_products = models.IntegerField(blank=True, null=True)
    custom_design = models.CharField(max_length=255, blank=True, null=True)
    custom_design_from = models.DateTimeField(blank=True, null=True)
    custom_design_to = models.DateTimeField(blank=True, null=True)
    custom_layout_update = models.TextField(blank=True, null=True)
    custom_use_parent_settings = models.IntegerField(blank=True, null=True)
    default_sort_by = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_mode = models.CharField(max_length=255, blank=True, null=True)
    filter_price_range = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    include_in_menu = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_anchor = models.IntegerField(blank=True, null=True)
    is_landing = models.IntegerField(blank=True, null=True)
    is_top_subcategory = models.IntegerField(blank=True, null=True)
    landing_page = models.IntegerField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    page_layout = models.CharField(max_length=255, blank=True, null=True)
    path_in_store = models.TextField(blank=True, null=True)
    searchindex_weight = models.TextField(blank=True, null=True)
    sw_cat_block_bottom = models.TextField(blank=True, null=True)
    sw_cat_block_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_left = models.TextField(blank=True, null=True)
    sw_cat_block_position = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_right = models.TextField(blank=True, null=True)
    sw_cat_block_top = models.TextField(blank=True, null=True)
    sw_cat_block_type = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_icon = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_label = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_left_block_width = models.TextField(blank=True, null=True)
    sw_cat_right_block_width = models.TextField(blank=True, null=True)
    sw_cat_static_width = models.TextField(blank=True, null=True)
    sw_gr_cat_alt_img_col = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_alt_img_col_val = models.TextField(blank=True, null=True)
    sw_gr_cat_aspect_ratio = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_banner = models.TextField(blank=True, null=True)
    sw_gr_cat_banner_style = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_custom_left = models.TextField(blank=True, null=True)
    sw_gr_cat_custom_right = models.TextField(blank=True, null=True)
    sw_gr_cat_hover_effect = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_position = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_ratio_height = models.TextField(blank=True, null=True)
    sw_gr_cat_ratio_width = models.TextField(blank=True, null=True)
    sw_gr_filter_position = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    top_block_content = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_flat_store_2'


class CatalogCategoryFlatStore3(models.Model):
    entity = models.OneToOneField(CatalogCategoryEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    all_children = models.TextField(blank=True, null=True)
    available_sort_by = models.TextField(blank=True, null=True)
    bottom_block_content = models.TextField(blank=True, null=True)
    children = models.TextField(blank=True, null=True)
    custom_apply_to_products = models.IntegerField(blank=True, null=True)
    custom_design = models.CharField(max_length=255, blank=True, null=True)
    custom_design_from = models.DateTimeField(blank=True, null=True)
    custom_design_to = models.DateTimeField(blank=True, null=True)
    custom_layout_update = models.TextField(blank=True, null=True)
    custom_use_parent_settings = models.IntegerField(blank=True, null=True)
    default_sort_by = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_mode = models.CharField(max_length=255, blank=True, null=True)
    filter_price_range = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    include_in_menu = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_anchor = models.IntegerField(blank=True, null=True)
    is_landing = models.IntegerField(blank=True, null=True)
    is_top_subcategory = models.IntegerField(blank=True, null=True)
    landing_page = models.IntegerField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    page_layout = models.CharField(max_length=255, blank=True, null=True)
    path_in_store = models.TextField(blank=True, null=True)
    searchindex_weight = models.TextField(blank=True, null=True)
    sw_cat_block_bottom = models.TextField(blank=True, null=True)
    sw_cat_block_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_left = models.TextField(blank=True, null=True)
    sw_cat_block_position = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_right = models.TextField(blank=True, null=True)
    sw_cat_block_top = models.TextField(blank=True, null=True)
    sw_cat_block_type = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_icon = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_label = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_left_block_width = models.TextField(blank=True, null=True)
    sw_cat_right_block_width = models.TextField(blank=True, null=True)
    sw_cat_static_width = models.TextField(blank=True, null=True)
    sw_gr_cat_alt_img_col = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_alt_img_col_val = models.TextField(blank=True, null=True)
    sw_gr_cat_aspect_ratio = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_banner = models.TextField(blank=True, null=True)
    sw_gr_cat_banner_style = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_custom_left = models.TextField(blank=True, null=True)
    sw_gr_cat_custom_right = models.TextField(blank=True, null=True)
    sw_gr_cat_hover_effect = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_position = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_ratio_height = models.TextField(blank=True, null=True)
    sw_gr_cat_ratio_width = models.TextField(blank=True, null=True)
    sw_gr_filter_position = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    top_block_content = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_flat_store_3'


class CatalogCategoryFlatStore4(models.Model):
    entity = models.OneToOneField(CatalogCategoryEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    all_children = models.TextField(blank=True, null=True)
    available_sort_by = models.TextField(blank=True, null=True)
    bottom_block_content = models.TextField(blank=True, null=True)
    children = models.TextField(blank=True, null=True)
    custom_apply_to_products = models.IntegerField(blank=True, null=True)
    custom_design = models.CharField(max_length=255, blank=True, null=True)
    custom_design_from = models.DateTimeField(blank=True, null=True)
    custom_design_to = models.DateTimeField(blank=True, null=True)
    custom_layout_update = models.TextField(blank=True, null=True)
    custom_use_parent_settings = models.IntegerField(blank=True, null=True)
    default_sort_by = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_mode = models.CharField(max_length=255, blank=True, null=True)
    filter_price_range = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    include_in_menu = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_anchor = models.IntegerField(blank=True, null=True)
    is_landing = models.IntegerField(blank=True, null=True)
    is_top_subcategory = models.IntegerField(blank=True, null=True)
    landing_page = models.IntegerField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    page_layout = models.CharField(max_length=255, blank=True, null=True)
    path_in_store = models.TextField(blank=True, null=True)
    searchindex_weight = models.TextField(blank=True, null=True)
    sw_cat_block_bottom = models.TextField(blank=True, null=True)
    sw_cat_block_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_left = models.TextField(blank=True, null=True)
    sw_cat_block_position = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_right = models.TextField(blank=True, null=True)
    sw_cat_block_top = models.TextField(blank=True, null=True)
    sw_cat_block_type = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_icon = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_label = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_left_block_width = models.TextField(blank=True, null=True)
    sw_cat_right_block_width = models.TextField(blank=True, null=True)
    sw_cat_static_width = models.TextField(blank=True, null=True)
    sw_gr_cat_alt_img_col = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_alt_img_col_val = models.TextField(blank=True, null=True)
    sw_gr_cat_aspect_ratio = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_banner = models.TextField(blank=True, null=True)
    sw_gr_cat_banner_style = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_custom_left = models.TextField(blank=True, null=True)
    sw_gr_cat_custom_right = models.TextField(blank=True, null=True)
    sw_gr_cat_hover_effect = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_position = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_ratio_height = models.TextField(blank=True, null=True)
    sw_gr_cat_ratio_width = models.TextField(blank=True, null=True)
    sw_gr_filter_position = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    top_block_content = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_flat_store_4'


class CatalogCategoryFlatStore5(models.Model):
    entity = models.OneToOneField(CatalogCategoryEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    parent_id = models.IntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    path = models.CharField(max_length=255)
    position = models.IntegerField()
    level = models.IntegerField()
    children_count = models.IntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    all_children = models.TextField(blank=True, null=True)
    available_sort_by = models.TextField(blank=True, null=True)
    bottom_block_content = models.TextField(blank=True, null=True)
    children = models.TextField(blank=True, null=True)
    custom_apply_to_products = models.IntegerField(blank=True, null=True)
    custom_design = models.CharField(max_length=255, blank=True, null=True)
    custom_design_from = models.DateTimeField(blank=True, null=True)
    custom_design_to = models.DateTimeField(blank=True, null=True)
    custom_layout_update = models.TextField(blank=True, null=True)
    custom_use_parent_settings = models.IntegerField(blank=True, null=True)
    default_sort_by = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    display_mode = models.CharField(max_length=255, blank=True, null=True)
    filter_price_range = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    include_in_menu = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    is_anchor = models.IntegerField(blank=True, null=True)
    is_landing = models.IntegerField(blank=True, null=True)
    is_top_subcategory = models.IntegerField(blank=True, null=True)
    landing_page = models.IntegerField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    page_layout = models.CharField(max_length=255, blank=True, null=True)
    path_in_store = models.TextField(blank=True, null=True)
    searchindex_weight = models.TextField(blank=True, null=True)
    sw_cat_block_bottom = models.TextField(blank=True, null=True)
    sw_cat_block_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_left = models.TextField(blank=True, null=True)
    sw_cat_block_position = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_block_right = models.TextField(blank=True, null=True)
    sw_cat_block_top = models.TextField(blank=True, null=True)
    sw_cat_block_type = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_icon = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_label = models.CharField(max_length=255, blank=True, null=True)
    sw_cat_left_block_width = models.TextField(blank=True, null=True)
    sw_cat_right_block_width = models.TextField(blank=True, null=True)
    sw_cat_static_width = models.TextField(blank=True, null=True)
    sw_gr_cat_alt_img_col = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_alt_img_col_val = models.TextField(blank=True, null=True)
    sw_gr_cat_aspect_ratio = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_banner = models.TextField(blank=True, null=True)
    sw_gr_cat_banner_style = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_columns = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_custom_left = models.TextField(blank=True, null=True)
    sw_gr_cat_custom_right = models.TextField(blank=True, null=True)
    sw_gr_cat_hover_effect = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_position = models.CharField(max_length=255, blank=True, null=True)
    sw_gr_cat_ratio_height = models.TextField(blank=True, null=True)
    sw_gr_cat_ratio_width = models.TextField(blank=True, null=True)
    sw_gr_filter_position = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    top_block_content = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_flat_store_5'


class CatalogCategoryProduct(models.Model):
    category = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product'
        unique_together = (('category', 'product'),)


class CatalogCategoryProductIndex(models.Model):
    category = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    position = models.IntegerField(blank=True, null=True)
    is_parent = models.SmallIntegerField()
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    visibility = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product_index'
        unique_together = (('category', 'product', 'store'),)


class CatalogCategoryProductIndexEnblIdx(models.Model):
    product_id = models.IntegerField()
    visibility = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product_index_enbl_idx'


class CatalogCategoryProductIndexEnblTmp(models.Model):
    product_id = models.IntegerField()
    visibility = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product_index_enbl_tmp'


class CatalogCategoryProductIndexIdx(models.Model):
    category_id = models.IntegerField()
    product_id = models.IntegerField()
    position = models.IntegerField()
    is_parent = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    visibility = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product_index_idx'


class CatalogCategoryProductIndexTmp(models.Model):
    category_id = models.IntegerField()
    product_id = models.IntegerField()
    position = models.IntegerField()
    is_parent = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    visibility = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_category_product_index_tmp'


class CatalogCompareItem(models.Model):
    catalog_compare_item_id = models.AutoField(primary_key=True)
    visitor_id = models.IntegerField()
    customer = models.ForeignKey('CustomerEntity', models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, blank=True, null=True, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_compare_item'


class CatalogEavAttribute(models.Model):
    attribute = models.OneToOneField('EavAttribute', models.DO_NOTHING, primary_key=True, related_name='+')
    frontend_input_renderer = models.CharField(max_length=255, blank=True, null=True)
    is_global = models.SmallIntegerField()
    is_visible = models.SmallIntegerField()
    is_searchable = models.SmallIntegerField()
    is_filterable = models.SmallIntegerField()
    is_comparable = models.SmallIntegerField()
    is_visible_on_front = models.SmallIntegerField()
    is_html_allowed_on_front = models.SmallIntegerField()
    is_used_for_price_rules = models.SmallIntegerField()
    is_filterable_in_search = models.SmallIntegerField()
    used_in_product_listing = models.SmallIntegerField()
    used_for_sort_by = models.SmallIntegerField()
    is_configurable = models.SmallIntegerField()
    apply_to = models.CharField(max_length=255, blank=True, null=True)
    is_visible_in_advanced_search = models.SmallIntegerField()
    position = models.IntegerField()
    is_wysiwyg_enabled = models.SmallIntegerField()
    is_used_for_promo_rules = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_eav_attribute'


class CatalogProductBundleOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    required = models.SmallIntegerField()
    position = models.IntegerField()
    type = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_option'


class CatalogProductBundleOptionValue(models.Model):
    value_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(CatalogProductBundleOption, models.DO_NOTHING, related_name='+')
    store_id = models.SmallIntegerField()
    title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_option_value'
        unique_together = (('option', 'store_id'),)


class CatalogProductBundlePriceIndex(models.Model):
    entity = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    min_price = models.DecimalField(max_digits=12, decimal_places=4)
    max_price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_price_index'
        unique_together = (('entity', 'website', 'customer_group'),)


class CatalogProductBundleSelection(models.Model):
    selection_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(CatalogProductBundleOption, models.DO_NOTHING, related_name='+')
    parent_product_id = models.IntegerField()
    product = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    position = models.IntegerField()
    is_default = models.SmallIntegerField()
    selection_price_type = models.SmallIntegerField()
    selection_price_value = models.DecimalField(max_digits=12, decimal_places=4)
    selection_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    selection_can_change_qty = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_selection'


class CatalogProductBundleSelectionPrice(models.Model):
    selection = models.ForeignKey(CatalogProductBundleSelection, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    selection_price_type = models.SmallIntegerField()
    selection_price_value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_selection_price'
        unique_together = (('selection', 'website'),)


class CatalogProductBundleStockIndex(models.Model):
    entity_id = models.IntegerField()
    website_id = models.SmallIntegerField()
    stock_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    stock_status = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_bundle_stock_index'
        unique_together = (('entity_id', 'website_id', 'stock_id', 'option_id'),)


class CatalogProductEnabledIndex(models.Model):
    product = models.ForeignKey('CatalogProductEntity', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    visibility = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_enabled_index'
        unique_together = (('product', 'store'),)


class CatalogProductEntity(JsonMixin, models.Model):
    entity_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_set = models.ForeignKey('EavAttributeSet', models.DO_NOTHING, related_name='+')
    type_id = models.CharField(max_length=32)
    sku = models.CharField(max_length=64, blank=True, null=True)
    has_options = models.SmallIntegerField()
    required_options = models.SmallIntegerField()
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity'


class CatalogProductEntityDatetime(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_datetime'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductEntityDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_decimal'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductEntityGallery(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    position = models.IntegerField()
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_gallery'
        unique_together = (('entity_type_id', 'entity', 'attribute', 'store'),)


class CatalogProductEntityGroupPrice(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    all_groups = models.SmallIntegerField()
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_group_price'
        unique_together = (('entity', 'all_groups', 'customer_group', 'website'),)


class CatalogProductEntityInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.IntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_int'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductEntityMediaGallery(models.Model):
    value_id = models.AutoField(primary_key=True)
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_media_gallery'


class CatalogProductEntityMediaGalleryValue(models.Model):
    value = models.ForeignKey(CatalogProductEntityMediaGallery, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    label = models.CharField(max_length=255, blank=True, null=True)
    position = models.IntegerField(blank=True, null=True)
    disabled = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_media_gallery_value'
        unique_together = (('value', 'store'),)


class CatalogProductEntityText(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.IntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_text'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductEntityTierPrice(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    all_groups = models.SmallIntegerField()
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_tier_price'
        unique_together = (('entity', 'all_groups', 'customer_group', 'qty', 'website'),)


class CatalogProductEntityVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type_id = models.IntegerField()
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_entity_varchar'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductFlat1(models.Model):
    entity = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    type_id = models.CharField(max_length=32)
    cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    gift_message_available = models.SmallIntegerField(blank=True, null=True)
    has_options = models.SmallIntegerField()
    image_label = models.CharField(max_length=255, blank=True, null=True)
    is_recurring = models.SmallIntegerField(blank=True, null=True)
    links_exist = models.IntegerField(blank=True, null=True)
    links_purchased_separately = models.IntegerField(blank=True, null=True)
    links_title = models.CharField(max_length=255, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    msrp_display_actual_price_type = models.CharField(max_length=255, blank=True, null=True)
    msrp_enabled = models.SmallIntegerField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    news_from_date = models.DateTimeField(blank=True, null=True)
    news_to_date = models.DateTimeField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price_type = models.IntegerField(blank=True, null=True)
    price_view = models.IntegerField(blank=True, null=True)
    recurring_profile = models.TextField(blank=True, null=True)
    required_options = models.SmallIntegerField()
    shipment_type = models.IntegerField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=64, blank=True, null=True)
    sku_type = models.IntegerField(blank=True, null=True)
    small_image = models.CharField(max_length=255, blank=True, null=True)
    small_image_label = models.CharField(max_length=255, blank=True, null=True)
    special_from_date = models.DateTimeField(blank=True, null=True)
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_to_date = models.DateTimeField(blank=True, null=True)
    tax_class_id = models.IntegerField(blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    thumbnail_label = models.CharField(max_length=255, blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    visibility = models.SmallIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight_type = models.IntegerField(blank=True, null=True)
    depth = models.CharField(max_length=255, blank=True, null=True)
    device_brand = models.IntegerField(blank=True, null=True)
    device_brand_value = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(blank=True, null=True)
    device_type_value = models.CharField(max_length=255, blank=True, null=True)
    display_technology = models.IntegerField(blank=True, null=True)
    display_technology_value = models.CharField(max_length=255, blank=True, null=True)
    form_factor = models.IntegerField(blank=True, null=True)
    form_factor_value = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    gallery = models.CharField(max_length=255, blank=True, null=True)
    os = models.IntegerField(blank=True, null=True)
    os_value = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    pixel_density = models.CharField(max_length=255, blank=True, null=True)
    touchscreen = models.SmallIntegerField(blank=True, null=True)
    touchscreen_type = models.IntegerField(blank=True, null=True)
    touchscreen_type_value = models.CharField(max_length=255, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    event = models.IntegerField(blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)
    lithium_ion_type = models.IntegerField(blank=True, null=True)
    lithium_ion_type_value = models.CharField(max_length=255, blank=True, null=True)
    sku_location = models.CharField(max_length=255, blank=True, null=True)
    adapter_type = models.IntegerField(blank=True, null=True)
    adapter_type_value = models.CharField(max_length=255, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_flat_1'


class CatalogProductFlat2(models.Model):
    entity = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    type_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=64, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_from_date = models.DateTimeField(blank=True, null=True)
    special_to_date = models.DateTimeField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    small_image = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    news_from_date = models.DateTimeField(blank=True, null=True)
    news_to_date = models.DateTimeField(blank=True, null=True)
    gallery = models.CharField(max_length=255, blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    is_recurring = models.SmallIntegerField(blank=True, null=True)
    recurring_profile = models.TextField(blank=True, null=True)
    visibility = models.SmallIntegerField(blank=True, null=True)
    required_options = models.SmallIntegerField()
    has_options = models.SmallIntegerField()
    image_label = models.CharField(max_length=255, blank=True, null=True)
    small_image_label = models.CharField(max_length=255, blank=True, null=True)
    thumbnail_label = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    msrp_enabled = models.SmallIntegerField(blank=True, null=True)
    msrp_display_actual_price_type = models.CharField(max_length=255, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_class_id = models.IntegerField(blank=True, null=True)
    gift_message_available = models.SmallIntegerField(blank=True, null=True)
    price_type = models.IntegerField(blank=True, null=True)
    sku_type = models.IntegerField(blank=True, null=True)
    weight_type = models.IntegerField(blank=True, null=True)
    price_view = models.IntegerField(blank=True, null=True)
    shipment_type = models.IntegerField(blank=True, null=True)
    links_purchased_separately = models.IntegerField(blank=True, null=True)
    links_title = models.CharField(max_length=255, blank=True, null=True)
    links_exist = models.IntegerField(blank=True, null=True)
    device_brand = models.IntegerField(blank=True, null=True)
    device_brand_value = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(blank=True, null=True)
    device_type_value = models.CharField(max_length=255, blank=True, null=True)
    form_factor = models.IntegerField(blank=True, null=True)
    form_factor_value = models.CharField(max_length=255, blank=True, null=True)
    os = models.IntegerField(blank=True, null=True)
    os_value = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    depth = models.CharField(max_length=255, blank=True, null=True)
    pixel_density = models.CharField(max_length=255, blank=True, null=True)
    display_technology = models.IntegerField(blank=True, null=True)
    display_technology_value = models.CharField(max_length=255, blank=True, null=True)
    touchscreen = models.SmallIntegerField(blank=True, null=True)
    touchscreen_type = models.IntegerField(blank=True, null=True)
    touchscreen_type_value = models.CharField(max_length=255, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)
    event = models.IntegerField(blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)
    lithium_ion_type = models.IntegerField(blank=True, null=True)
    lithium_ion_type_value = models.CharField(max_length=255, blank=True, null=True)
    sku_location = models.CharField(max_length=255, blank=True, null=True)
    adapter_type = models.IntegerField(blank=True, null=True)
    adapter_type_value = models.CharField(max_length=255, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_flat_2'


class CatalogProductFlat3(models.Model):
    entity = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    type_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=64, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_from_date = models.DateTimeField(blank=True, null=True)
    special_to_date = models.DateTimeField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    small_image = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    news_from_date = models.DateTimeField(blank=True, null=True)
    news_to_date = models.DateTimeField(blank=True, null=True)
    gallery = models.CharField(max_length=255, blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    is_recurring = models.SmallIntegerField(blank=True, null=True)
    recurring_profile = models.TextField(blank=True, null=True)
    visibility = models.SmallIntegerField(blank=True, null=True)
    required_options = models.SmallIntegerField()
    has_options = models.SmallIntegerField()
    image_label = models.CharField(max_length=255, blank=True, null=True)
    small_image_label = models.CharField(max_length=255, blank=True, null=True)
    thumbnail_label = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    msrp_enabled = models.SmallIntegerField(blank=True, null=True)
    msrp_display_actual_price_type = models.CharField(max_length=255, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_class_id = models.IntegerField(blank=True, null=True)
    gift_message_available = models.SmallIntegerField(blank=True, null=True)
    price_type = models.IntegerField(blank=True, null=True)
    sku_type = models.IntegerField(blank=True, null=True)
    weight_type = models.IntegerField(blank=True, null=True)
    price_view = models.IntegerField(blank=True, null=True)
    shipment_type = models.IntegerField(blank=True, null=True)
    links_purchased_separately = models.IntegerField(blank=True, null=True)
    links_title = models.CharField(max_length=255, blank=True, null=True)
    links_exist = models.IntegerField(blank=True, null=True)
    device_brand = models.IntegerField(blank=True, null=True)
    device_brand_value = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(blank=True, null=True)
    device_type_value = models.CharField(max_length=255, blank=True, null=True)
    form_factor = models.IntegerField(blank=True, null=True)
    form_factor_value = models.CharField(max_length=255, blank=True, null=True)
    os = models.IntegerField(blank=True, null=True)
    os_value = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    depth = models.CharField(max_length=255, blank=True, null=True)
    pixel_density = models.CharField(max_length=255, blank=True, null=True)
    display_technology = models.IntegerField(blank=True, null=True)
    display_technology_value = models.CharField(max_length=255, blank=True, null=True)
    touchscreen = models.SmallIntegerField(blank=True, null=True)
    touchscreen_type = models.IntegerField(blank=True, null=True)
    touchscreen_type_value = models.CharField(max_length=255, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)
    event = models.IntegerField(blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)
    lithium_ion_type = models.IntegerField(blank=True, null=True)
    lithium_ion_type_value = models.CharField(max_length=255, blank=True, null=True)
    sku_location = models.CharField(max_length=255, blank=True, null=True)
    adapter_type = models.IntegerField(blank=True, null=True)
    adapter_type_value = models.CharField(max_length=255, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_flat_3'


class CatalogProductFlat4(models.Model):
    entity = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    type_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=64, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_from_date = models.DateTimeField(blank=True, null=True)
    special_to_date = models.DateTimeField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    small_image = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    news_from_date = models.DateTimeField(blank=True, null=True)
    news_to_date = models.DateTimeField(blank=True, null=True)
    gallery = models.CharField(max_length=255, blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    is_recurring = models.SmallIntegerField(blank=True, null=True)
    recurring_profile = models.TextField(blank=True, null=True)
    visibility = models.SmallIntegerField(blank=True, null=True)
    required_options = models.SmallIntegerField()
    has_options = models.SmallIntegerField()
    image_label = models.CharField(max_length=255, blank=True, null=True)
    small_image_label = models.CharField(max_length=255, blank=True, null=True)
    thumbnail_label = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    msrp_enabled = models.SmallIntegerField(blank=True, null=True)
    msrp_display_actual_price_type = models.CharField(max_length=255, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_class_id = models.IntegerField(blank=True, null=True)
    gift_message_available = models.SmallIntegerField(blank=True, null=True)
    price_type = models.IntegerField(blank=True, null=True)
    sku_type = models.IntegerField(blank=True, null=True)
    weight_type = models.IntegerField(blank=True, null=True)
    price_view = models.IntegerField(blank=True, null=True)
    shipment_type = models.IntegerField(blank=True, null=True)
    links_purchased_separately = models.IntegerField(blank=True, null=True)
    links_title = models.CharField(max_length=255, blank=True, null=True)
    links_exist = models.IntegerField(blank=True, null=True)
    device_brand = models.IntegerField(blank=True, null=True)
    device_brand_value = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(blank=True, null=True)
    device_type_value = models.CharField(max_length=255, blank=True, null=True)
    form_factor = models.IntegerField(blank=True, null=True)
    form_factor_value = models.CharField(max_length=255, blank=True, null=True)
    os = models.IntegerField(blank=True, null=True)
    os_value = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    depth = models.CharField(max_length=255, blank=True, null=True)
    pixel_density = models.CharField(max_length=255, blank=True, null=True)
    display_technology = models.IntegerField(blank=True, null=True)
    display_technology_value = models.CharField(max_length=255, blank=True, null=True)
    touchscreen = models.SmallIntegerField(blank=True, null=True)
    touchscreen_type = models.IntegerField(blank=True, null=True)
    touchscreen_type_value = models.CharField(max_length=255, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)
    event = models.IntegerField(blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)
    lithium_ion_type = models.IntegerField(blank=True, null=True)
    lithium_ion_type_value = models.CharField(max_length=255, blank=True, null=True)
    sku_location = models.CharField(max_length=255, blank=True, null=True)
    adapter_type = models.IntegerField(blank=True, null=True)
    adapter_type_value = models.CharField(max_length=255, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_flat_4'


class CatalogProductFlat5(models.Model):
    entity = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, primary_key=True, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    type_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=64, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    special_from_date = models.DateTimeField(blank=True, null=True)
    special_to_date = models.DateTimeField(blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    small_image = models.CharField(max_length=255, blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    news_from_date = models.DateTimeField(blank=True, null=True)
    news_to_date = models.DateTimeField(blank=True, null=True)
    gallery = models.CharField(max_length=255, blank=True, null=True)
    url_key = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    is_recurring = models.SmallIntegerField(blank=True, null=True)
    recurring_profile = models.TextField(blank=True, null=True)
    visibility = models.SmallIntegerField(blank=True, null=True)
    required_options = models.SmallIntegerField()
    has_options = models.SmallIntegerField()
    image_label = models.CharField(max_length=255, blank=True, null=True)
    small_image_label = models.CharField(max_length=255, blank=True, null=True)
    thumbnail_label = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    msrp_enabled = models.SmallIntegerField(blank=True, null=True)
    msrp_display_actual_price_type = models.CharField(max_length=255, blank=True, null=True)
    msrp = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_class_id = models.IntegerField(blank=True, null=True)
    gift_message_available = models.SmallIntegerField(blank=True, null=True)
    price_type = models.IntegerField(blank=True, null=True)
    sku_type = models.IntegerField(blank=True, null=True)
    weight_type = models.IntegerField(blank=True, null=True)
    price_view = models.IntegerField(blank=True, null=True)
    shipment_type = models.IntegerField(blank=True, null=True)
    links_purchased_separately = models.IntegerField(blank=True, null=True)
    links_title = models.CharField(max_length=255, blank=True, null=True)
    links_exist = models.IntegerField(blank=True, null=True)
    device_brand = models.IntegerField(blank=True, null=True)
    device_brand_value = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.IntegerField(blank=True, null=True)
    device_type_value = models.CharField(max_length=255, blank=True, null=True)
    form_factor = models.IntegerField(blank=True, null=True)
    form_factor_value = models.CharField(max_length=255, blank=True, null=True)
    os = models.IntegerField(blank=True, null=True)
    os_value = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    width = models.CharField(max_length=255, blank=True, null=True)
    depth = models.CharField(max_length=255, blank=True, null=True)
    pixel_density = models.CharField(max_length=255, blank=True, null=True)
    display_technology = models.IntegerField(blank=True, null=True)
    display_technology_value = models.CharField(max_length=255, blank=True, null=True)
    touchscreen = models.SmallIntegerField(blank=True, null=True)
    touchscreen_type = models.IntegerField(blank=True, null=True)
    touchscreen_type_value = models.CharField(max_length=255, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)
    event = models.IntegerField(blank=True, null=True)
    event_value = models.CharField(max_length=255, blank=True, null=True)
    lithium_ion_type = models.IntegerField(blank=True, null=True)
    lithium_ion_type_value = models.CharField(max_length=255, blank=True, null=True)
    sku_location = models.CharField(max_length=255, blank=True, null=True)
    adapter_type = models.IntegerField(blank=True, null=True)
    adapter_type_value = models.CharField(max_length=255, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_flat_5'


class CatalogProductIndexEav(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav'
        unique_together = (('entity', 'attribute', 'store', 'value'),)


class CatalogProductIndexEavDecimal(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav_decimal'
        unique_together = (('entity', 'attribute', 'store'),)


class CatalogProductIndexEavDecimalIdx(models.Model):
    entity_id = models.IntegerField()
    attribute_id = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav_decimal_idx'
        unique_together = (('entity_id', 'attribute_id', 'store_id', 'value'),)


class CatalogProductIndexEavDecimalTmp(models.Model):
    entity_id = models.IntegerField()
    attribute_id = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav_decimal_tmp'
        unique_together = (('entity_id', 'attribute_id', 'store_id'),)


class CatalogProductIndexEavIdx(models.Model):
    entity_id = models.IntegerField()
    attribute_id = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav_idx'
        unique_together = (('entity_id', 'attribute_id', 'store_id', 'value'),)


class CatalogProductIndexEavTmp(models.Model):
    entity_id = models.IntegerField()
    attribute_id = models.SmallIntegerField()
    store_id = models.SmallIntegerField()
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_eav_tmp'
        unique_together = (('entity_id', 'attribute_id', 'store_id', 'value'),)


class CatalogProductIndexGroupPrice(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_group_price'
        unique_together = (('entity', 'customer_group', 'website'),)


class CatalogProductIndexPrice(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    final_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price'
        unique_together = (('entity', 'customer_group', 'website'),)


class CatalogProductIndexPriceBundleIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    price_type = models.SmallIntegerField()
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    orig_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tier = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceBundleOptIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_opt_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id'),)


class CatalogProductIndexPriceBundleOptTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    alt_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_opt_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id'),)


class CatalogProductIndexPriceBundleSelIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    selection_id = models.IntegerField()
    group_type = models.SmallIntegerField(blank=True, null=True)
    is_required = models.SmallIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_sel_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id', 'selection_id'),)


class CatalogProductIndexPriceBundleSelTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    selection_id = models.IntegerField()
    group_type = models.SmallIntegerField(blank=True, null=True)
    is_required = models.SmallIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_sel_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id', 'selection_id'),)


class CatalogProductIndexPriceBundleTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    price_type = models.SmallIntegerField()
    special_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    orig_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tier = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_bundle_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceCfgOptAgrIdx(models.Model):
    parent_id = models.IntegerField()
    child_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_cfg_opt_agr_idx'
        unique_together = (('parent_id', 'child_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceCfgOptAgrTmp(models.Model):
    parent_id = models.IntegerField()
    child_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_cfg_opt_agr_tmp'
        unique_together = (('parent_id', 'child_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceCfgOptIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_cfg_opt_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceCfgOptTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_cfg_opt_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceDownlodIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4)
    max_price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_downlod_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceDownlodTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4)
    max_price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_downlod_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceFinalIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    orig_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tier = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_final_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceFinalTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    orig_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tier = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_final_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    final_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceOptAgrIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_opt_agr_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id'),)


class CatalogProductIndexPriceOptAgrTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    option_id = models.IntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_opt_agr_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id', 'option_id'),)


class CatalogProductIndexPriceOptIdx(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_opt_idx'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceOptTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_opt_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexPriceTmp(models.Model):
    entity_id = models.IntegerField()
    customer_group_id = models.SmallIntegerField()
    website_id = models.SmallIntegerField()
    tax_class_id = models.SmallIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    final_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tier_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    group_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_price_tmp'
        unique_together = (('entity_id', 'customer_group_id', 'website_id'),)


class CatalogProductIndexTierPrice(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    min_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_tier_price'
        unique_together = (('entity', 'customer_group', 'website'),)


class CatalogProductIndexWebsite(models.Model):
    website = models.OneToOneField('CoreWebsite', models.DO_NOTHING, primary_key=True, related_name='+')
    website_date = models.DateField(blank=True, null=True)
    rate = models.FloatField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_index_website'


class CatalogProductLink(models.Model):
    link_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    linked_product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    link_type = models.ForeignKey('CatalogProductLinkType', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link'
        unique_together = (('link_type', 'product', 'linked_product'),)


class CatalogProductLinkAttribute(models.Model):
    product_link_attribute_id = models.SmallIntegerField(primary_key=True)
    link_type = models.ForeignKey('CatalogProductLinkType', models.DO_NOTHING, related_name='+')
    product_link_attribute_code = models.CharField(max_length=32, blank=True, null=True)
    data_type = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link_attribute'


class CatalogProductLinkAttributeDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    product_link_attribute = models.ForeignKey(CatalogProductLinkAttribute, models.DO_NOTHING, blank=True, null=True, related_name='+')
    link = models.ForeignKey(CatalogProductLink, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link_attribute_decimal'
        unique_together = (('product_link_attribute', 'link'),)


class CatalogProductLinkAttributeInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    product_link_attribute = models.ForeignKey(CatalogProductLinkAttribute, models.DO_NOTHING, blank=True, null=True, related_name='+')
    link = models.ForeignKey(CatalogProductLink, models.DO_NOTHING, related_name='+')
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link_attribute_int'
        unique_together = (('product_link_attribute', 'link'),)


class CatalogProductLinkAttributeVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    product_link_attribute = models.ForeignKey(CatalogProductLinkAttribute, models.DO_NOTHING, related_name='+')
    link = models.ForeignKey(CatalogProductLink, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link_attribute_varchar'
        unique_together = (('product_link_attribute', 'link'),)


class CatalogProductLinkType(models.Model):
    link_type_id = models.SmallIntegerField(primary_key=True)
    code = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_link_type'


class CatalogProductOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    type = models.CharField(max_length=50, blank=True, null=True)
    is_require = models.SmallIntegerField()
    sku = models.CharField(max_length=64, blank=True, null=True)
    max_characters = models.IntegerField(blank=True, null=True)
    file_extension = models.CharField(max_length=50, blank=True, null=True)
    image_size_x = models.SmallIntegerField(blank=True, null=True)
    image_size_y = models.SmallIntegerField(blank=True, null=True)
    sort_order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option'


class CatalogProductOptionPrice(models.Model):
    option_price_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(CatalogProductOption, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4)
    price_type = models.CharField(max_length=7)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option_price'
        unique_together = (('option', 'store'),)


class CatalogProductOptionTitle(models.Model):
    option_title_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(CatalogProductOption, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option_title'
        unique_together = (('option', 'store'),)


class CatalogProductOptionTypePrice(models.Model):
    option_type_price_id = models.AutoField(primary_key=True)
    option_type = models.ForeignKey('CatalogProductOptionTypeValue', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4)
    price_type = models.CharField(max_length=7)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option_type_price'
        unique_together = (('option_type', 'store'),)


class CatalogProductOptionTypeTitle(models.Model):
    option_type_title_id = models.AutoField(primary_key=True)
    option_type = models.ForeignKey('CatalogProductOptionTypeValue', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option_type_title'
        unique_together = (('option_type', 'store'),)


class CatalogProductOptionTypeValue(models.Model):
    option_type_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(CatalogProductOption, models.DO_NOTHING, related_name='+')
    sku = models.CharField(max_length=64, blank=True, null=True)
    sort_order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_option_type_value'


class CatalogProductRelation(models.Model):
    parent = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    child = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_relation'
        unique_together = (('parent', 'child'),)


class CatalogProductSuperAttribute(models.Model):
    product_super_attribute_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    position = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_super_attribute'
        unique_together = (('product', 'attribute_id'),)


class CatalogProductSuperAttributeLabel(models.Model):
    value_id = models.AutoField(primary_key=True)
    product_super_attribute = models.ForeignKey(CatalogProductSuperAttribute, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    use_default = models.SmallIntegerField(blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_super_attribute_label'
        unique_together = (('product_super_attribute', 'store'),)


class CatalogProductSuperAttributePricing(models.Model):
    value_id = models.AutoField(primary_key=True)
    product_super_attribute = models.ForeignKey(CatalogProductSuperAttribute, models.DO_NOTHING, related_name='+')
    value_index = models.CharField(max_length=255, blank=True, null=True)
    is_percent = models.SmallIntegerField(blank=True, null=True)
    pricing_value = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_super_attribute_pricing'
        unique_together = (('product_super_attribute', 'value_index', 'website'),)


class CatalogProductSuperLink(models.Model):
    link_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    parent = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_super_link'
        unique_together = (('product', 'parent'),)


class CatalogProductWebsite(models.Model):
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalog_product_website'
        unique_together = (('product', 'website'),)


class CataloginventoryStock(models.Model):
    stock_id = models.SmallIntegerField(primary_key=True)
    stock_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cataloginventory_stock'


class CataloginventoryStockItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    stock = models.ForeignKey(CataloginventoryStock, models.DO_NOTHING, related_name='+')
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    min_qty = models.DecimalField(max_digits=12, decimal_places=4)
    use_config_min_qty = models.SmallIntegerField()
    is_qty_decimal = models.SmallIntegerField()
    backorders = models.SmallIntegerField()
    use_config_backorders = models.SmallIntegerField()
    min_sale_qty = models.DecimalField(max_digits=12, decimal_places=4)
    use_config_min_sale_qty = models.SmallIntegerField()
    max_sale_qty = models.DecimalField(max_digits=12, decimal_places=4)
    use_config_max_sale_qty = models.SmallIntegerField()
    is_in_stock = models.SmallIntegerField()
    low_stock_date = models.DateTimeField(blank=True, null=True)
    notify_stock_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    use_config_notify_stock_qty = models.SmallIntegerField()
    manage_stock = models.SmallIntegerField()
    use_config_manage_stock = models.SmallIntegerField()
    stock_status_changed_auto = models.SmallIntegerField()
    use_config_qty_increments = models.SmallIntegerField()
    qty_increments = models.DecimalField(max_digits=12, decimal_places=4)
    use_config_enable_qty_inc = models.SmallIntegerField()
    enable_qty_increments = models.SmallIntegerField()
    is_decimal_divided = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cataloginventory_stock_item'
        unique_together = (('product', 'stock'),)


class CataloginventoryStockStatus(models.Model):
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    stock = models.ForeignKey(CataloginventoryStock, models.DO_NOTHING, related_name='+')
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    stock_status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cataloginventory_stock_status'
        unique_together = (('product', 'website', 'stock'),)


class CataloginventoryStockStatusIdx(models.Model):
    product_id = models.IntegerField()
    website_id = models.SmallIntegerField()
    stock_id = models.SmallIntegerField()
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    stock_status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cataloginventory_stock_status_idx'
        unique_together = (('product_id', 'website_id', 'stock_id'),)


class CataloginventoryStockStatusTmp(models.Model):
    product_id = models.IntegerField()
    website_id = models.SmallIntegerField()
    stock_id = models.SmallIntegerField()
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    stock_status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cataloginventory_stock_status_tmp'
        unique_together = (('product_id', 'website_id', 'stock_id'),)


class Catalogrule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    is_active = models.SmallIntegerField()
    conditions_serialized = models.TextField(blank=True, null=True)
    actions_serialized = models.TextField(blank=True, null=True)
    stop_rules_processing = models.SmallIntegerField()
    sort_order = models.IntegerField()
    simple_action = models.CharField(max_length=32, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    sub_is_enable = models.SmallIntegerField()
    sub_simple_action = models.CharField(max_length=32, blank=True, null=True)
    sub_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule'


class CatalogruleAffectedProduct(models.Model):
    product_id = models.IntegerField(primary_key=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_affected_product'


class CatalogruleCustomerGroup(models.Model):
    rule = models.ForeignKey(Catalogrule, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_customer_group'
        unique_together = (('rule', 'customer_group'),)


class CatalogruleGroupWebsite(models.Model):
    rule = models.ForeignKey(Catalogrule, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_group_website'
        unique_together = (('rule', 'customer_group', 'website'),)


class CatalogruleProduct(models.Model):
    rule_product_id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(Catalogrule, models.DO_NOTHING, related_name='+')
    from_time = models.IntegerField()
    to_time = models.IntegerField()
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    action_operator = models.CharField(max_length=10, blank=True, null=True)
    action_amount = models.DecimalField(max_digits=12, decimal_places=4)
    action_stop = models.SmallIntegerField()
    sort_order = models.IntegerField()
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    sub_simple_action = models.CharField(max_length=32, blank=True, null=True)
    sub_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_product'
        unique_together = (('rule', 'from_time', 'to_time', 'website', 'customer_group', 'product', 'sort_order'),)


class CatalogruleProductPrice(models.Model):
    rule_product_price_id = models.AutoField(primary_key=True)
    rule_date = models.DateField()
    customer_group = models.ForeignKey('CustomerGroup', models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    rule_price = models.DecimalField(max_digits=12, decimal_places=4)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    latest_start_date = models.DateField(blank=True, null=True)
    earliest_end_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_product_price'
        unique_together = (('rule_date', 'website', 'customer_group', 'product'),)


class CatalogruleWebsite(models.Model):
    rule = models.ForeignKey(Catalogrule, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogrule_website'
        unique_together = (('rule', 'website'),)


class CatalogsearchFulltext(models.Model):
    fulltext_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    store_id = models.SmallIntegerField()
    data_index = models.TextField(blank=True, null=True)
    brand_model_path_data = models.TextField(blank=True, null=True)
    updated = models.IntegerField()
    searchindex_weight = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogsearch_fulltext'
        unique_together = (('product_id', 'store_id'),)


class CatalogsearchQuery(models.Model):
    query_id = models.AutoField(primary_key=True)
    query_text = models.CharField(max_length=255, blank=True, null=True)
    num_results = models.IntegerField()
    popularity = models.IntegerField()
    redirect = models.CharField(max_length=255, blank=True, null=True)
    synonym_for = models.CharField(max_length=255, blank=True, null=True)
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    display_in_terms = models.SmallIntegerField()
    is_active = models.SmallIntegerField(blank=True, null=True)
    is_processed = models.SmallIntegerField(blank=True, null=True)
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogsearch_query'


class CatalogsearchResult(models.Model):
    query = models.ForeignKey(CatalogsearchQuery, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    relevance = models.DecimalField(max_digits=20, decimal_places=4)
    category_id = models.IntegerField(blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'catalogsearch_result'
        unique_together = (('query', 'product', 'category_id'),)


class CheckoutAgreement(models.Model):
    agreement_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    content_height = models.CharField(max_length=25, blank=True, null=True)
    checkbox_text = models.TextField(blank=True, null=True)
    is_active = models.SmallIntegerField()
    is_html = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'checkout_agreement'


class CheckoutAgreementStore(models.Model):
    agreement = models.ForeignKey(CheckoutAgreement, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'checkout_agreement_store'
        unique_together = (('agreement', 'store'),)


class CmsBlock(models.Model):
    block_id = models.SmallIntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    is_active = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cms_block'


class CmsBlockStore(models.Model):
    block = models.ForeignKey(CmsBlock, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cms_block_store'
        unique_together = (('block', 'store'),)


class CmsPage(models.Model):
    page_id = models.SmallIntegerField(primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    root_template = models.CharField(max_length=255, blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    identifier = models.CharField(max_length=100, blank=True, null=True)
    content_heading = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    is_active = models.SmallIntegerField()
    sort_order = models.SmallIntegerField()
    layout_update_xml = models.TextField(blank=True, null=True)
    custom_theme = models.CharField(max_length=100, blank=True, null=True)
    custom_root_template = models.CharField(max_length=255, blank=True, null=True)
    custom_layout_update_xml = models.TextField(blank=True, null=True)
    custom_theme_from = models.DateField(blank=True, null=True)
    custom_theme_to = models.DateField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cms_page'


class CmsPageStore(models.Model):
    page = models.ForeignKey(CmsPage, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cms_page_store'
        unique_together = (('page', 'store'),)


class CoreCache(models.Model):
    id = models.CharField(primary_key=True, max_length=200)
    data = models.TextField(blank=True, null=True)
    create_time = models.IntegerField(blank=True, null=True)
    update_time = models.IntegerField(blank=True, null=True)
    expire_time = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_cache'


class CoreCacheOption(models.Model):
    code = models.CharField(primary_key=True, max_length=32)
    value = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_cache_option'


class CoreCacheTag(models.Model):
    tag = models.CharField(max_length=100)
    cache_id = models.CharField(max_length=200)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_cache_tag'
        unique_together = (('tag', 'cache_id'),)


class CoreConfigData(models.Model):
    config_id = models.AutoField(primary_key=True)
    scope = models.CharField(max_length=8)
    scope_id = models.IntegerField()
    path = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_config_data'
        unique_together = (('scope', 'scope_id', 'path'),)


class CoreEmailTemplate(models.Model):
    template_id = models.AutoField(primary_key=True)
    template_code = models.CharField(unique=True, max_length=150)
    template_text = models.TextField()
    template_styles = models.TextField(blank=True, null=True)
    template_type = models.IntegerField(blank=True, null=True)
    template_subject = models.CharField(max_length=200)
    template_sender_name = models.CharField(max_length=200, blank=True, null=True)
    template_sender_email = models.CharField(max_length=200, blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    orig_template_code = models.CharField(max_length=200, blank=True, null=True)
    orig_template_variables = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_email_template'


class CoreFlag(models.Model):
    flag_id = models.AutoField(primary_key=True)
    flag_code = models.CharField(max_length=255)
    state = models.SmallIntegerField()
    flag_data = models.TextField(blank=True, null=True)
    last_update = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_flag'


class CoreLayoutLink(models.Model):
    layout_link_id = models.AutoField(primary_key=True)
    store = models.ForeignKey('CoreStore', models.DO_NOTHING, related_name='+')
    area = models.CharField(max_length=64, blank=True, null=True)
    package = models.CharField(max_length=64, blank=True, null=True)
    theme = models.CharField(max_length=64, blank=True, null=True)
    layout_update = models.ForeignKey('CoreLayoutUpdate', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_layout_link'
        unique_together = (('store', 'package', 'theme', 'layout_update'),)


class CoreLayoutUpdate(models.Model):
    layout_update_id = models.AutoField(primary_key=True)
    handle = models.CharField(max_length=255, blank=True, null=True)
    xml = models.TextField(blank=True, null=True)
    sort_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_layout_update'


class CoreResource(models.Model):
    code = models.CharField(primary_key=True, max_length=50)
    version = models.CharField(max_length=50, blank=True, null=True)
    data_version = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_resource'


class CoreSession(models.Model):
    session_id = models.CharField(primary_key=True, max_length=255)
    session_expires = models.IntegerField()
    session_data = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_session'


class CoreStore(models.Model):
    store_id = models.SmallIntegerField(primary_key=True)
    code = models.CharField(unique=True, max_length=32, blank=True, null=True)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    group = models.ForeignKey('CoreStoreGroup', models.DO_NOTHING, related_name='+')
    name = models.CharField(max_length=255)
    sort_order = models.SmallIntegerField()
    is_active = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_store'


class CoreStoreGroup(models.Model):
    group_id = models.SmallIntegerField(primary_key=True)
    website = models.ForeignKey('CoreWebsite', models.DO_NOTHING, related_name='+')
    name = models.CharField(max_length=255)
    root_category_id = models.IntegerField()
    default_store_id = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_store_group'


class CoreTranslate(models.Model):
    key_id = models.AutoField(primary_key=True)
    string = models.CharField(max_length=255)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    translate = models.CharField(max_length=255, blank=True, null=True)
    locale = models.CharField(max_length=20)
    crc_string = models.BigIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_translate'
        unique_together = (('store', 'locale', 'crc_string', 'string'),)


class CoreUrlRewrite(models.Model):
    url_rewrite_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    id_path = models.CharField(max_length=255, blank=True, null=True)
    request_path = models.CharField(max_length=255, blank=True, null=True)
    target_path = models.CharField(max_length=255, blank=True, null=True)
    is_system = models.SmallIntegerField(blank=True, null=True)
    options = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(CatalogCategoryEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_url_rewrite'
        unique_together = (('id_path', 'is_system', 'store'), ('request_path', 'store'),)


class CoreVariable(models.Model):
    variable_id = models.AutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_variable'


class CoreVariableValue(models.Model):
    value_id = models.AutoField(primary_key=True)
    variable = models.ForeignKey(CoreVariable, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    plain_value = models.TextField(blank=True, null=True)
    html_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_variable_value'
        unique_together = (('variable', 'store'),)


class CoreWebsite(models.Model):
    website_id = models.SmallIntegerField(primary_key=True)
    code = models.CharField(unique=True, max_length=32, blank=True, null=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    sort_order = models.SmallIntegerField()
    default_group_id = models.SmallIntegerField()
    is_default = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'core_website'


class CouponAggregated(models.Model):
    period = models.DateField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_uses = models.IntegerField()
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    rule_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'coupon_aggregated'
        unique_together = (('period', 'store', 'order_status', 'coupon_code'),)


class CouponAggregatedOrder(models.Model):
    period = models.DateField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_uses = models.IntegerField()
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    rule_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'coupon_aggregated_order'
        unique_together = (('period', 'store', 'order_status', 'coupon_code'),)


class CouponAggregatedUpdated(models.Model):
    period = models.DateField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_uses = models.IntegerField()
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    rule_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'coupon_aggregated_updated'
        unique_together = (('period', 'store', 'order_status', 'coupon_code'),)


class CronSchedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    job_code = models.CharField(max_length=255)
    status = models.CharField(max_length=7)
    messages = models.TextField(blank=True, null=True)
    created_at = TimestampField()
    scheduled_at = models.DateTimeField(blank=True, null=True)
    executed_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'cron_schedule'


class CustomerAddressEntity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute_set_id = models.SmallIntegerField()
    increment_id = models.CharField(max_length=50, blank=True, null=True)
    parent = models.ForeignKey('CustomerEntity', models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    is_active = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity'


class CustomerAddressEntityDatetime(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerAddressEntity, models.DO_NOTHING, related_name='+')
    value = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity_datetime'
        unique_together = (('entity', 'attribute'),)


class CustomerAddressEntityDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerAddressEntity, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity_decimal'
        unique_together = (('entity', 'attribute'),)


class CustomerAddressEntityInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerAddressEntity, models.DO_NOTHING, related_name='+')
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity_int'
        unique_together = (('entity', 'attribute'),)


class CustomerAddressEntityText(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerAddressEntity, models.DO_NOTHING, related_name='+')
    value = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity_text'
        unique_together = (('entity', 'attribute'),)


class CustomerAddressEntityVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerAddressEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_address_entity_varchar'
        unique_together = (('entity', 'attribute'),)


class CustomerEavAttribute(models.Model):
    attribute = models.OneToOneField('EavAttribute', models.DO_NOTHING, primary_key=True, related_name='+')
    is_visible = models.SmallIntegerField()
    input_filter = models.CharField(max_length=255, blank=True, null=True)
    multiline_count = models.SmallIntegerField()
    validate_rules = models.TextField(blank=True, null=True)
    is_system = models.SmallIntegerField()
    sort_order = models.IntegerField()
    data_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_eav_attribute'


class CustomerEavAttributeWebsite(models.Model):
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    is_visible = models.SmallIntegerField(blank=True, null=True)
    is_required = models.SmallIntegerField(blank=True, null=True)
    default_value = models.TextField(blank=True, null=True)
    multiline_count = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_eav_attribute_website'
        unique_together = (('attribute', 'website'),)


class CustomerEntity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute_set_id = models.SmallIntegerField()
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, blank=True, null=True, related_name='+')
    email = models.CharField(max_length=255, blank=True, null=True)
    group_id = models.SmallIntegerField()
    increment_id = models.CharField(max_length=50, blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    is_active = models.SmallIntegerField()
    disable_auto_group_change = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity'
        unique_together = (('email', 'website'),)


class CustomerEntityDatetime(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    value = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity_datetime'
        unique_together = (('entity', 'attribute'),)


class CustomerEntityDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity_decimal'
        unique_together = (('entity', 'attribute'),)


class CustomerEntityInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity_int'
        unique_together = (('entity', 'attribute'),)


class CustomerEntityText(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    value = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity_text'
        unique_together = (('entity', 'attribute'),)


class CustomerEntityVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_entity_varchar'
        unique_together = (('entity', 'attribute'),)


class CustomerFormAttribute(models.Model):
    form_code = models.CharField(max_length=32)
    attribute = models.ForeignKey('EavAttribute', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_form_attribute'
        unique_together = (('form_code', 'attribute'),)


class CustomerGroup(models.Model):
    customer_group_id = models.SmallIntegerField(primary_key=True)
    customer_group_code = models.CharField(max_length=32)
    tax_class_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'customer_group'


class DatafeedAttribute(models.Model):
    entity_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    store_id = models.SmallIntegerField()
    color = models.CharField(max_length=50)
    images = models.TextField()
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_attribute'
        unique_together = (('product_id', 'store_id'),)


class DatafeedEntity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store_id = models.SmallIntegerField()
    name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=200)
    exclude_oos = models.SmallIntegerField()
    created_at = TimestampField()
    token_name = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_entity'
        unique_together = (('name', 'store_id'),)


class DatafeedExclude(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store_id = models.SmallIntegerField()
    category_id = models.IntegerField()
    product_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_exclude'
        unique_together = (('product_id', 'category_id', 'store_id'),)


class DatafeedHistory(models.Model):
    entity_id = models.AutoField(primary_key=True)
    feed_id = models.IntegerField()
    create_date = models.DateTimeField()
    record_count = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_history'


class DatafeedMaster(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_out_of_stock_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30, blank=True, null=True)
    weight = models.CharField(max_length=30, blank=True, null=True)
    width = models.CharField(max_length=30, blank=True, null=True)
    length = models.CharField(max_length=30, blank=True, null=True)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master'
        unique_together = (('product_id', 'category_id', 'store_id'),)


class DatafeedMasterStore1(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_store_1'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterStore2(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    @property
    def product_full_id(self):
        if not hasattr(self, '__product_full_id'):
            self.__product_full_id = str(self.product_id) + '_' + '2' + '_' + str(self.category_id)
        return self.__product_full_id

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_store_2'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterStore3(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_store_3'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterStore4(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_store_4'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterStore5(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_date = models.DateTimeField()
    updated_date = models.DateTimeField()
    last_in_stock_date = models.DateTimeField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_store_5'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterTemp(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store_id = models.IntegerField()
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30, blank=True, null=True)
    weight = models.CharField(max_length=30, blank=True, null=True)
    width = models.CharField(max_length=30, blank=True, null=True)
    length = models.CharField(max_length=30, blank=True, null=True)
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.IntegerField(blank=True, null=True)
    do_not_add_brand_model_to_pdp = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp'
        unique_together = (('product_id', 'store_id'),)


class DatafeedMasterTemp1(models.Model):
    entity_id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()
    model_id = models.IntegerField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp_1'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterTemp2(models.Model):
    entity_id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()
    model_id = models.IntegerField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp_2'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterTemp3(models.Model):
    entity_id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()
    model_id = models.IntegerField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp_3'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterTemp4(models.Model):
    entity_id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()
    model_id = models.IntegerField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp_4'
        unique_together = (('product_id', 'category_id'),)


class DatafeedMasterTemp5(models.Model):
    entity_id = models.AutoField(primary_key=True)
    brand_id = models.IntegerField()
    model_id = models.IntegerField()
    category_id = models.IntegerField()
    category_id_path = models.CharField(max_length=100)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=50)
    attribute_set_id = models.IntegerField()
    upc = models.CharField(max_length=50)
    quantity = models.IntegerField()
    is_in_stock = models.SmallIntegerField()
    product_title = models.CharField(max_length=255)
    product_short_description = models.TextField()
    product_long_description = models.TextField()
    brand_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    url = models.TextField()
    images = models.TextField()
    condition = models.CharField(max_length=100)
    color = models.CharField(max_length=255)
    reviews = models.IntegerField()
    reviews_rating = models.DecimalField(max_digits=6, decimal_places=1)
    regular_price = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    msrp = models.DecimalField(max_digits=12, decimal_places=4)
    cogs = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.CharField(max_length=30)
    weight = models.CharField(max_length=30)
    width = models.CharField(max_length=30)
    length = models.CharField(max_length=30)
    sales_velocity = models.CharField(max_length=200)
    recency = models.IntegerField()
    third_party_info = models.TextField()
    oem = models.SmallIntegerField(blank=True, null=True)
    backorders = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_master_temp_5'
        unique_together = (('product_id', 'category_id'),)


class DatafeedStock(models.Model):
    product_id = models.IntegerField(unique=True)
    last_in_stock_date = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'datafeed_stock'


class DataflowBatch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    profile = models.ForeignKey('DataflowProfile', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    adapter = models.CharField(max_length=128, blank=True, null=True)
    params = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_batch'


class DataflowBatchExport(models.Model):
    batch_export_id = models.BigIntegerField(primary_key=True)
    batch = models.ForeignKey(DataflowBatch, models.DO_NOTHING, related_name='+')
    batch_data = models.TextField(blank=True, null=True)
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_batch_export'


class DataflowBatchImport(models.Model):
    batch_import_id = models.BigIntegerField(primary_key=True)
    batch = models.ForeignKey(DataflowBatch, models.DO_NOTHING, related_name='+')
    batch_data = models.TextField(blank=True, null=True)
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_batch_import'


class DataflowImportData(models.Model):
    import_id = models.AutoField(primary_key=True)
    session = models.ForeignKey('DataflowSession', models.DO_NOTHING, blank=True, null=True, related_name='+')
    serial_number = models.IntegerField()
    value = models.TextField(blank=True, null=True)
    status = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_import_data'


class DataflowProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    actions_xml = models.TextField(blank=True, null=True)
    gui_data = models.TextField(blank=True, null=True)
    direction = models.CharField(max_length=6, blank=True, null=True)
    entity_type = models.CharField(max_length=64, blank=True, null=True)
    store_id = models.SmallIntegerField()
    data_transfer = models.CharField(max_length=11, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_profile'


class DataflowProfileHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    profile = models.ForeignKey(DataflowProfile, models.DO_NOTHING, related_name='+')
    action_code = models.CharField(max_length=64, blank=True, null=True)
    user_id = models.IntegerField()
    performed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_profile_history'


class DataflowSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    created_date = models.DateTimeField(blank=True, null=True)
    file = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=32, blank=True, null=True)
    direction = models.CharField(max_length=32, blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'dataflow_session'


class DesignChange(models.Model):
    design_change_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    design = models.CharField(max_length=255, blank=True, null=True)
    date_from = models.DateField(blank=True, null=True)
    date_to = models.DateField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'design_change'


class DirectoryCountry(models.Model):
    country_id = models.CharField(primary_key=True, max_length=2)
    iso2_code = models.CharField(max_length=2, blank=True, null=True)
    iso3_code = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'directory_country'


class DirectoryCountryFormat(models.Model):
    country_format_id = models.AutoField(primary_key=True)
    country_id = models.CharField(max_length=2, blank=True, null=True)
    type = models.CharField(max_length=30, blank=True, null=True)
    format = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'directory_country_format'
        unique_together = (('country_id', 'type'),)


class DirectoryCountryRegion(models.Model):
    region_id = models.AutoField(primary_key=True)
    country_id = models.CharField(max_length=4)
    code = models.CharField(max_length=32, blank=True, null=True)
    default_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'directory_country_region'


class DirectoryCountryRegionName(models.Model):
    locale = models.CharField(max_length=8)
    region = models.ForeignKey(DirectoryCountryRegion, models.DO_NOTHING, related_name='+')
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'directory_country_region_name'
        unique_together = (('locale', 'region'),)


class DirectoryCurrencyRate(models.Model):
    currency_from = models.CharField(max_length=3)
    currency_to = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=24, decimal_places=12)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'directory_currency_rate'
        unique_together = (('currency_from', 'currency_to'),)


class DownloadableLink(models.Model):
    link_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    sort_order = models.IntegerField()
    number_of_downloads = models.IntegerField(blank=True, null=True)
    is_shareable = models.SmallIntegerField()
    link_url = models.CharField(max_length=255, blank=True, null=True)
    link_file = models.CharField(max_length=255, blank=True, null=True)
    link_type = models.CharField(max_length=20, blank=True, null=True)
    sample_url = models.CharField(max_length=255, blank=True, null=True)
    sample_file = models.CharField(max_length=255, blank=True, null=True)
    sample_type = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_link'


class DownloadableLinkPrice(models.Model):
    price_id = models.AutoField(primary_key=True)
    link = models.ForeignKey(DownloadableLink, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_link_price'


class DownloadableLinkPurchased(models.Model):
    purchased_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_increment_id = models.CharField(max_length=50, blank=True, null=True)
    order_item_id = models.IntegerField()
    created_at = TimestampField()
    updated_at = TimestampField()
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    link_section_title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_link_purchased'


class DownloadableLinkPurchasedItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    purchased = models.ForeignKey(DownloadableLinkPurchased, models.DO_NOTHING, related_name='+')
    order_item = models.ForeignKey('SalesFlatOrderItem', models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_id = models.IntegerField(blank=True, null=True)
    link_hash = models.CharField(max_length=255, blank=True, null=True)
    number_of_downloads_bought = models.IntegerField()
    number_of_downloads_used = models.IntegerField()
    link_id = models.IntegerField()
    link_title = models.CharField(max_length=255, blank=True, null=True)
    is_shareable = models.SmallIntegerField()
    link_url = models.CharField(max_length=255, blank=True, null=True)
    link_file = models.CharField(max_length=255, blank=True, null=True)
    link_type = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_link_purchased_item'


class DownloadableLinkTitle(models.Model):
    title_id = models.AutoField(primary_key=True)
    link = models.ForeignKey(DownloadableLink, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_link_title'
        unique_together = (('link', 'store'),)


class DownloadableSample(models.Model):
    sample_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    sample_url = models.CharField(max_length=255, blank=True, null=True)
    sample_file = models.CharField(max_length=255, blank=True, null=True)
    sample_type = models.CharField(max_length=20, blank=True, null=True)
    sort_order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_sample'


class DownloadableSampleTitle(models.Model):
    title_id = models.AutoField(primary_key=True)
    sample = models.ForeignKey(DownloadableSample, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    title = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'downloadable_sample_title'
        unique_together = (('sample', 'store'),)


class EavAttribute(models.Model):
    attribute_id = models.SmallIntegerField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_code = models.CharField(max_length=255, blank=True, null=True)
    attribute_model = models.CharField(max_length=255, blank=True, null=True)
    backend_model = models.CharField(max_length=255, blank=True, null=True)
    backend_type = models.CharField(max_length=8)
    backend_table = models.CharField(max_length=255, blank=True, null=True)
    frontend_model = models.CharField(max_length=255, blank=True, null=True)
    frontend_input = models.CharField(max_length=50, blank=True, null=True)
    frontend_label = models.CharField(max_length=255, blank=True, null=True)
    frontend_class = models.CharField(max_length=255, blank=True, null=True)
    source_model = models.CharField(max_length=255, blank=True, null=True)
    is_required = models.SmallIntegerField()
    is_user_defined = models.SmallIntegerField()
    default_value = models.TextField(blank=True, null=True)
    is_unique = models.SmallIntegerField()
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute'
        unique_together = (('entity_type', 'attribute_code'),)


class EavAttributeGroup(models.Model):
    attribute_group_id = models.SmallIntegerField(primary_key=True)
    attribute_set = models.ForeignKey('EavAttributeSet', models.DO_NOTHING, related_name='+')
    attribute_group_name = models.CharField(max_length=255, blank=True, null=True)
    sort_order = models.SmallIntegerField()
    default_id = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute_group'
        unique_together = (('attribute_set', 'attribute_group_name'),)


class EavAttributeLabel(models.Model):
    attribute_label_id = models.AutoField(primary_key=True)
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute_label'


class EavAttributeOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    sort_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute_option'


class EavAttributeOptionValue(models.Model):
    value_id = models.AutoField(primary_key=True)
    option = models.ForeignKey(EavAttributeOption, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute_option_value'


class EavAttributeSet(models.Model):
    attribute_set_id = models.SmallIntegerField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_set_name = models.CharField(max_length=255, blank=True, null=True)
    sort_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_attribute_set'
        unique_together = (('entity_type', 'attribute_set_name'),)


class EavEntity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_set_id = models.SmallIntegerField()
    increment_id = models.CharField(max_length=50, blank=True, null=True)
    parent_id = models.IntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    is_active = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity'


class EavEntityAttribute(models.Model):
    entity_attribute_id = models.AutoField(primary_key=True)
    entity_type_id = models.SmallIntegerField()
    attribute_set_id = models.SmallIntegerField()
    attribute_group = models.ForeignKey(EavAttributeGroup, models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    sort_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_attribute'
        unique_together = (('attribute_group', 'attribute'), ('attribute_set_id', 'attribute'),)


class EavEntityDatetime(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(EavEntity, models.DO_NOTHING, related_name='+')
    value = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_datetime'
        unique_together = (('entity', 'attribute_id', 'store'),)


class EavEntityDecimal(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(EavEntity, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_decimal'
        unique_together = (('entity', 'attribute_id', 'store'),)


class EavEntityInt(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(EavEntity, models.DO_NOTHING, related_name='+')
    value = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_int'
        unique_together = (('entity', 'attribute_id', 'store'),)


class EavEntityStore(models.Model):
    entity_store_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    increment_prefix = models.CharField(max_length=20, blank=True, null=True)
    increment_last_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_store'


class EavEntityText(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey('EavEntityType', models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(EavEntity, models.DO_NOTHING, related_name='+')
    value = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_text'
        unique_together = (('entity', 'attribute_id', 'store'),)


class EavEntityType(models.Model):
    entity_type_id = models.SmallIntegerField(primary_key=True)
    entity_type_code = models.CharField(max_length=50)
    entity_model = models.CharField(max_length=255)
    attribute_model = models.CharField(max_length=255, blank=True, null=True)
    entity_table = models.CharField(max_length=255, blank=True, null=True)
    value_table_prefix = models.CharField(max_length=255, blank=True, null=True)
    entity_id_field = models.CharField(max_length=255, blank=True, null=True)
    is_data_sharing = models.SmallIntegerField()
    data_sharing_key = models.CharField(max_length=100, blank=True, null=True)
    default_attribute_set_id = models.SmallIntegerField()
    increment_model = models.CharField(max_length=255, blank=True, null=True)
    increment_per_store = models.SmallIntegerField()
    increment_pad_length = models.SmallIntegerField()
    increment_pad_char = models.CharField(max_length=1)
    additional_attribute_table = models.CharField(max_length=255, blank=True, null=True)
    entity_attribute_collection = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_type'


class EavEntityVarchar(models.Model):
    value_id = models.AutoField(primary_key=True)
    entity_type = models.ForeignKey(EavEntityType, models.DO_NOTHING, related_name='+')
    attribute_id = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(EavEntity, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_entity_varchar'
        unique_together = (('entity', 'attribute_id', 'store'),)


class EavFormElement(models.Model):
    element_id = models.AutoField(primary_key=True)
    type = models.ForeignKey('EavFormType', models.DO_NOTHING, related_name='+')
    fieldset = models.ForeignKey('EavFormFieldset', models.DO_NOTHING, blank=True, null=True, related_name='+')
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    sort_order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_form_element'
        unique_together = (('type', 'attribute'),)


class EavFormFieldset(models.Model):
    fieldset_id = models.SmallIntegerField(primary_key=True)
    type = models.ForeignKey('EavFormType', models.DO_NOTHING, related_name='+')
    code = models.CharField(max_length=64)
    sort_order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_form_fieldset'
        unique_together = (('type', 'code'),)


class EavFormFieldsetLabel(models.Model):
    fieldset = models.ForeignKey(EavFormFieldset, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    label = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_form_fieldset_label'
        unique_together = (('fieldset', 'store'),)


class EavFormType(models.Model):
    type_id = models.SmallIntegerField(primary_key=True)
    code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    is_system = models.SmallIntegerField()
    theme = models.CharField(max_length=64, blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_form_type'
        unique_together = (('code', 'theme', 'store'),)


class EavFormTypeEntity(models.Model):
    type = models.ForeignKey(EavFormType, models.DO_NOTHING, related_name='+')
    entity_type = models.ForeignKey(EavEntityType, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'eav_form_type_entity'
        unique_together = (('type', 'entity_type'),)


class ErpInventoryAdjuststock(models.Model):
    adjuststock_id = models.AutoField(primary_key=True)
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)
    created_at = models.DateField(blank=True, null=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_adjuststock'


class ErpInventoryAdjuststockProduct(models.Model):
    adjuststockproduct_id = models.AutoField(primary_key=True)
    adjuststock = models.ForeignKey(ErpInventoryAdjuststock, models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    old_qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    adjust_qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    updated_qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_adjuststock_product'


class ErpInventoryDelivery(models.Model):
    delivery_id = models.AutoField(primary_key=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    qty_delivery = models.DecimalField(max_digits=10, decimal_places=0)
    purchase_order = models.ForeignKey('ErpInventoryPurchaseOrder', models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=255)
    sametime = models.CharField(max_length=255, blank=True, null=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_delivery'


class ErpInventoryDeliveryQueue(models.Model):
    purchase_order_id = models.IntegerField()
    product_id = models.IntegerField()
    sku = models.CharField(max_length=63)
    warehouse_id = models.IntegerField()
    supplier_id = models.IntegerField()
    created_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()
    current_qty = models.DecimalField(max_digits=10, decimal_places=4)
    total_order_qty = models.DecimalField(max_digits=10, decimal_places=4)
    total_received_qty = models.DecimalField(max_digits=10, decimal_places=4)
    delivered_qty = models.DecimalField(max_digits=10, decimal_places=4)
    is_processed = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_delivery_queue'


class ErpInventoryDeliveryWarehouse(models.Model):
    delivery_warehouse_id = models.AutoField(primary_key=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    purchase_order_id = models.IntegerField()
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255, blank=True, null=True)
    qty_delivery = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    sametime = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_delivery_warehouse'


class ErpInventoryDropship(models.Model):
    dropship_id = models.AutoField(primary_key=True)
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255)
    supplier_email = models.CharField(max_length=255)
    shipping_name = models.CharField(max_length=255)
    created_on = models.DateTimeField(blank=True, null=True)
    status = models.SmallIntegerField()
    admin_name = models.CharField(max_length=255)
    admin_email = models.CharField(max_length=255)
    session = models.CharField(max_length=255)
    increment_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_dropship'


class ErpInventoryDropshipProduct(models.Model):
    dropshipproduct_id = models.AutoField(primary_key=True)
    dropship = models.ForeignKey(ErpInventoryDropship, models.DO_NOTHING, related_name='+')
    item_id = models.IntegerField()
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255)
    product_id = models.IntegerField()
    product_sku = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    qty_request = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_offer = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_approve = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_shipped = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_dropship_product'


class ErpInventoryNotice(models.Model):
    notice_id = models.AutoField(primary_key=True)
    notice_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    status = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_notice'


class ErpInventoryPaymentTerm(models.Model):
    payment_term_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    payment_days = models.IntegerField()
    status = models.IntegerField()
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_payment_term'


class ErpInventoryPaymentTermHistory(models.Model):
    payment_term_history_id = models.AutoField(primary_key=True)
    payment_term = models.ForeignKey(ErpInventoryPaymentTerm, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_payment_term_history'


class ErpInventoryPaymentTermHistoryContent(models.Model):
    payment_term_history_content_id = models.AutoField(primary_key=True)
    payment_term_history = models.ForeignKey(ErpInventoryPaymentTermHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_payment_term_history_content'


class ErpInventoryProducts(models.Model):
    inventory_product_id = models.AutoField(primary_key=True)
    product = models.OneToOneField(CatalogProductEntity, models.DO_NOTHING, unique=True, related_name='+')
    cost_price = models.DecimalField(max_digits=12, decimal_places=4)
    last_update = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_products'


class ErpInventoryPurchaseOrder(models.Model):
    purchase_order_id = models.AutoField(primary_key=True)
    purchase_on = models.DateTimeField(blank=True, null=True)
    bill_name = models.CharField(max_length=255, blank=True, null=True)
    warehouse_id = models.CharField(max_length=255, blank=True, null=True)
    warehouse_name = models.CharField(max_length=255, blank=True, null=True)
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    change_rate = models.CharField(max_length=255)
    tax_rate = models.FloatField(blank=True, null=True)
    shipping_cost = models.FloatField(blank=True, null=True)
    delivery_process = models.FloatField(blank=True, null=True)
    status = models.IntegerField()
    paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_products_recieved = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)
    order_placed = models.IntegerField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    cancel_date = models.DateField(blank=True, null=True)
    expected_date = models.DateField(blank=True, null=True)
    payment_date = models.DateField(blank=True, null=True)
    ship_via = models.IntegerField(blank=True, null=True)
    payment_term = models.IntegerField(blank=True, null=True)
    send_mail = models.SmallIntegerField()
    auto_po_status = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_purchase_order'


class ErpInventoryPurchaseOrderHistory(models.Model):
    purchase_order_history_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(ErpInventoryPurchaseOrder, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_purchase_order_history'


class ErpInventoryPurchaseOrderHistoryContent(models.Model):
    purchase_order_history_content_id = models.AutoField(primary_key=True)
    purchase_order_history = models.ForeignKey(ErpInventoryPurchaseOrderHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_purchase_order_history_content'


class ErpInventoryPurchaseOrderProduct(models.Model):
    purchase_order_product_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField(blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    purchase_order = models.ForeignKey(ErpInventoryPurchaseOrder, models.DO_NOTHING, related_name='purchase_order')
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_recieved = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=4)
    discount = models.FloatField()
    tax = models.FloatField()
    qty_returned = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_purchase_order_product'


class ErpInventoryPurchaseOrderProductWarehouse(models.Model):
    purchase_order_product_warehouse_id = models.AutoField(primary_key=True)
    purchase_order_id = models.IntegerField()
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255, blank=True, null=True)
    qty_order = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_received = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_returned = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_purchase_order_product_warehouse'


class ErpInventoryReportProductsMoved(models.Model):
    inventory_report_pm_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    amount_moved = models.DecimalField(max_digits=12, decimal_places=4)
    qty_moved = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    moved_at = models.DateTimeField(blank=True, null=True)
    moved_type = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_report_products_moved'


class ErpInventoryReportProductsReceived(models.Model):
    inventory_report_pr_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    amount_received = models.DecimalField(max_digits=12, decimal_places=4)
    qty_received = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    received_at = models.DateTimeField(blank=True, null=True)
    received_type = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_report_products_received'


class ErpInventoryRequestStock(models.Model):
    request_stock_id = models.AutoField(primary_key=True)
    from_id = models.IntegerField(blank=True, null=True)
    from_name = models.CharField(max_length=255, blank=True, null=True)
    to_id = models.IntegerField(blank=True, null=True)
    to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField()
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_request_stock'


class ErpInventoryRequestStockProduct(models.Model):
    request_stock_product_id = models.AutoField(primary_key=True)
    request_stock = models.ForeignKey(ErpInventoryRequestStock, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_id = models.IntegerField(blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_request_stock_product'


class ErpInventoryReturnProductWarehouse(models.Model):
    return_product_warehouse_id = models.AutoField(primary_key=True)
    returned_on = models.DateTimeField(blank=True, null=True)
    purchase_order_id = models.IntegerField()
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255, blank=True, null=True)
    qty_return = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_return_product_warehouse'


class ErpInventoryReturnedOrder(models.Model):
    returned_order_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(ErpInventoryPurchaseOrder, models.DO_NOTHING, related_name='+')
    total_products = models.DecimalField(max_digits=10, decimal_places=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    returned_on = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField()
    paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    supplier_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_returned_order'


class ErpInventoryReturnedOrderProduct(models.Model):
    returned_order_product_id = models.AutoField(primary_key=True)
    returned_order = models.ForeignKey(ErpInventoryReturnedOrder, models.DO_NOTHING, related_name='+')
    qty_return = models.DecimalField(max_digits=10, decimal_places=0)
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_returned_order_product'


class ErpInventoryRunRateAggregated(models.Model):
    product_id = models.IntegerField()
    run_rate = models.IntegerField()
    metric_30 = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_run_rate_aggregated'


class ErpInventorySendStock(models.Model):
    send_stock_id = models.AutoField(primary_key=True)
    from_id = models.IntegerField(blank=True, null=True)
    from_name = models.CharField(max_length=255, blank=True, null=True)
    to_id = models.IntegerField(blank=True, null=True)
    to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField()
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_send_stock'


class ErpInventorySendStockProduct(models.Model):
    send_stock_product_id = models.AutoField(primary_key=True)
    send_stock = models.ForeignKey(ErpInventorySendStock, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_id = models.IntegerField(blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_send_stock_product'


class ErpInventoryShipment(models.Model):
    inventory_shipment_id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    product_id = models.IntegerField()
    order_id = models.IntegerField()
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255)
    shipment_id = models.IntegerField()
    item_refuned = models.IntegerField()
    item_shiped = models.IntegerField()
    supplier_id = models.IntegerField()
    supplier_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_shipment'


class ErpInventoryShipmentTransfer(models.Model):
    shipment_transfer_id = models.AutoField(primary_key=True)
    item_id = models.IntegerField()
    product_id = models.IntegerField()
    order_id = models.IntegerField()
    warehouse_id = models.IntegerField()
    warehouse_name = models.CharField(max_length=255)
    qty_need_transfer = models.IntegerField(blank=True, null=True)
    transfer_stock_id = models.IntegerField()
    status = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_shipment_transfer'


class ErpInventoryShippingMethod(models.Model):
    shipping_method_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField()
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_shipping_method'


class ErpInventoryShippingMethodHistory(models.Model):
    shipping_method_history_id = models.AutoField(primary_key=True)
    shipping_method = models.ForeignKey(ErpInventoryShippingMethod, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_shipping_method_history'


class ErpInventoryShippingMethodHistoryContent(models.Model):
    shipping_method_history_content_id = models.AutoField(primary_key=True)
    shipping_method_history = models.ForeignKey(ErpInventoryShippingMethodHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_shipping_method_history_content'


class ErpInventoryStockIssuing(models.Model):
    stock_issuing_id = models.AutoField(primary_key=True)
    type = models.SmallIntegerField(blank=True, null=True)
    reference_id = models.IntegerField()
    warehouse_id_from = models.IntegerField(blank=True, null=True)
    warehouse_id_to = models.IntegerField(blank=True, null=True)
    warehouse_from_name = models.CharField(max_length=255, blank=True, null=True)
    warehouse_to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    status = models.IntegerField()
    reference_invoice_number = models.CharField(max_length=255)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_stock_issuing'


class ErpInventoryStockIssuingProduct(models.Model):
    stock_issuing_product_id = models.AutoField(primary_key=True)
    stock_issuing = models.ForeignKey(ErpInventoryStockIssuing, models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_stock_issuing_product'


class ErpInventoryStockReceiving(models.Model):
    stock_receiving_id = models.AutoField(primary_key=True)
    type = models.SmallIntegerField(blank=True, null=True)
    reference_id = models.IntegerField()
    warehouse_id_from = models.IntegerField(blank=True, null=True)
    warehouse_id_to = models.IntegerField(blank=True, null=True)
    warehouse_from_name = models.CharField(max_length=255, blank=True, null=True)
    warehouse_to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    status = models.IntegerField()
    comment = models.CharField(max_length=255, blank=True, null=True)
    reference_invoice_number = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_stock_receiving'


class ErpInventoryStockReceivingProduct(models.Model):
    stock_receiving_product_id = models.AutoField(primary_key=True)
    stock_receiving = models.ForeignKey(ErpInventoryStockReceiving, models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=255)
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_stock_receiving_product'


class ErpInventorySupplier(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255)
    telephone = models.CharField(max_length=50)
    fax = models.CharField(max_length=50, blank=True, null=True)
    street = models.TextField()
    city = models.CharField(max_length=255)
    country_id = models.CharField(max_length=3)
    state = models.CharField(max_length=255)
    postcode = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField()
    total_order = models.DecimalField(max_digits=10, decimal_places=0)
    purchase_order = models.DecimalField(max_digits=12, decimal_places=4)
    return_order = models.DecimalField(max_digits=12, decimal_places=4)
    last_purchase_order = models.DateField(blank=True, null=True)
    create_by = models.CharField(max_length=255, blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_supplier'


class ErpInventorySupplierHistory(models.Model):
    supplier_history_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(ErpInventorySupplier, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_supplier_history'


class ErpInventorySupplierHistoryContent(models.Model):
    supplier_history_content_id = models.AutoField(primary_key=True)
    supplier_history = models.ForeignKey(ErpInventorySupplierHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_supplier_history_content'


class ErpInventorySupplierProduct(models.Model):
    supplier_product_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(ErpInventorySupplier, models.DO_NOTHING, related_name='supplier')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    cost = models.DecimalField(max_digits=12, decimal_places=4)
    discount = models.FloatField()
    tax = models.FloatField()
    supplier_sku = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_supplier_product'


class ErpInventoryTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    send_stock = models.ForeignKey(ErpInventorySendStock, models.DO_NOTHING, blank=True, null=True, related_name='+')
    request_stock = models.ForeignKey(ErpInventoryRequestStock, models.DO_NOTHING, blank=True, null=True, related_name='+')
    type = models.IntegerField()
    from_id = models.IntegerField(blank=True, null=True)
    from_name = models.CharField(max_length=255, blank=True, null=True)
    to_id = models.IntegerField(blank=True, null=True)
    to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transaction'


class ErpInventoryTransactionProduct(models.Model):
    transaction_product_id = models.AutoField(primary_key=True)
    transaction = models.ForeignKey(ErpInventoryTransaction, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_id = models.IntegerField(blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transaction_product'


class ErpInventoryTransferStock(models.Model):
    transfer_stock_id = models.AutoField(primary_key=True)
    warehouse_from_id = models.IntegerField(blank=True, null=True)
    warehouse_from_name = models.CharField(max_length=255, blank=True, null=True)
    warehouse_to_id = models.IntegerField(blank=True, null=True)
    warehouse_to_name = models.CharField(max_length=255, blank=True, null=True)
    total_products = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    create_at = models.DateField(blank=True, null=True)
    status = models.IntegerField()
    type = models.IntegerField()
    create_by = models.CharField(max_length=255, blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transfer_stock'


class ErpInventoryTransferStockHistory(models.Model):
    transfer_stock_history_id = models.AutoField(primary_key=True)
    transfer_stock = models.ForeignKey(ErpInventoryTransferStock, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transfer_stock_history'


class ErpInventoryTransferStockHistoryContent(models.Model):
    transfer_stock_history_content_id = models.AutoField(primary_key=True)
    transfer_stock_history = models.ForeignKey(ErpInventoryTransferStockHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transfer_stock_history_content'


class ErpInventoryTransferStockProduct(models.Model):
    tranfer_stock_product_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField(blank=True, null=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_sku = models.CharField(max_length=255, blank=True, null=True)
    transfer_stock = models.ForeignKey(ErpInventoryTransferStock, models.DO_NOTHING, blank=True, null=True, related_name='+')
    qty_transfer = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_request = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    qty_receive = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_transfer_stock_product'


class ErpInventoryWarehouse(models.Model):
    warehouse_id = models.AutoField(primary_key=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    manager_name = models.CharField(max_length=255)
    manager_email = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    street = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country_id = models.CharField(max_length=3, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    state_id = models.IntegerField(blank=True, null=True)
    postcode = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.CharField(max_length=255, blank=True, null=True)
    longtitude = models.CharField(max_length=255, blank=True, null=True)
    total_purchase = models.IntegerField(blank=True, null=True)
    status = models.IntegerField()
    is_unwarehouse = models.IntegerField()
    is_main = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse'


class ErpInventoryWarehouseAssignment(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(ErpInventoryWarehouse, models.DO_NOTHING, related_name='+')
    admin_id = models.IntegerField()
    can_edit_warehouse = models.IntegerField()
    can_transfer = models.IntegerField()
    can_adjust = models.IntegerField()
    can_edit_qty = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse_assignment'


class ErpInventoryWarehouseHistory(models.Model):
    warehouse_history_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(ErpInventoryWarehouse, models.DO_NOTHING, related_name='+')
    time_stamp = models.DateTimeField(blank=True, null=True)
    create_by = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse_history'


class ErpInventoryWarehouseHistoryContent(models.Model):
    warehouse_history_content_id = models.AutoField(primary_key=True)
    warehouse_history = models.ForeignKey(ErpInventoryWarehouseHistory, models.DO_NOTHING, related_name='+')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse_history_content'


class ErpInventoryWarehouseOrder(models.Model):
    warehouse_order_id = models.AutoField(primary_key=True)
    order_id = models.IntegerField()
    warehouse_id = models.IntegerField()
    product_id = models.IntegerField()
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse_order'


class ErpInventoryWarehouseProduct(models.Model):
    warehouse_product_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(ErpInventoryWarehouse, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    qty = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'erp_inventory_warehouse_product'
        unique_together = (('warehouse', 'product'),)


class GiftMessage(models.Model):
    gift_message_id = models.AutoField(primary_key=True)
    customer_id = models.IntegerField()
    sender = models.CharField(max_length=255, blank=True, null=True)
    recipient = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'gift_message'


class GoogleshoppingAttributes(models.Model):
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    gcontent_attribute = models.CharField(max_length=255)
    type = models.ForeignKey('GoogleshoppingTypes', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'googleshopping_attributes'


class GoogleshoppingItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    type_id = models.IntegerField()
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    gcontent_item_id = models.CharField(max_length=255)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    published = models.DateTimeField(blank=True, null=True)
    expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'googleshopping_items'


class GoogleshoppingTypes(models.Model):
    type_id = models.AutoField(primary_key=True)
    attribute_set = models.ForeignKey(EavAttributeSet, models.DO_NOTHING, related_name='+')
    target_country = models.CharField(max_length=2)
    category = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'googleshopping_types'
        unique_together = (('attribute_set', 'target_country'),)


class ImportexportImportdata(models.Model):
    entity = models.CharField(max_length=50)
    behavior = models.CharField(max_length=10)
    data = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'importexport_importdata'


class IndexEvent(models.Model):
    event_id = models.BigIntegerField(primary_key=True)
    type = models.CharField(max_length=64)
    entity = models.CharField(max_length=64)
    entity_pk = models.BigIntegerField(blank=True, null=True)
    created_at = TimestampField()
    old_data = models.TextField(blank=True, null=True)
    new_data = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'index_event'
        unique_together = (('type', 'entity', 'entity_pk'),)


class IndexProcess(models.Model):
    process_id = models.AutoField(primary_key=True)
    indexer_code = models.CharField(unique=True, max_length=32)
    status = models.CharField(max_length=15)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    mode = models.CharField(max_length=9)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'index_process'


class IndexProcessEvent(models.Model):
    process = models.ForeignKey(IndexProcess, models.DO_NOTHING, related_name='+')
    event = models.ForeignKey(IndexEvent, models.DO_NOTHING, related_name='+')
    status = models.CharField(max_length=7)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'index_process_event'
        unique_together = (('process', 'event'),)


class LegacyBmc(models.Model):
    entity_id = models.SmallIntegerField(primary_key=True)
    mapping_type = models.CharField(max_length=20)
    mage_entity_id = models.IntegerField(blank=True, null=True)
    mage_entity_varchar = models.CharField(max_length=100)
    legacy_id = models.IntegerField(blank=True, null=True)
    legacy_varchar = models.CharField(max_length=100)
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'legacy_bmc'


class LegacyProductIdMapping(models.Model):
    legacy_product_id = models.IntegerField()
    magento_product_id = models.IntegerField()
    magento_category_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'legacy_product_id_mapping'


class LegacyRedirects(models.Model):
    entity_id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=255)
    mage_url = models.CharField(max_length=255, blank=True, null=True)
    store_id = models.SmallIntegerField()
    category_id = models.IntegerField()
    pdp_url = models.CharField(max_length=255)
    product_id = models.IntegerField()
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'legacy_redirects'
        unique_together = (('url', 'store_id'),)


class LogCustomer(models.Model):
    log_id = models.AutoField(primary_key=True)
    visitor_id = models.BigIntegerField(blank=True, null=True)
    customer_id = models.IntegerField()
    login_at = models.DateTimeField()
    logout_at = models.DateTimeField(blank=True, null=True)
    store_id = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_customer'


class LogLegacyImageImportTemp(models.Model):
    entity_id = models.AutoField(primary_key=True)
    sku = models.CharField(unique=True, max_length=50)
    old_count_before = models.IntegerField(blank=True, null=True)
    new_count_before = models.IntegerField(blank=True, null=True)
    old_count_after = models.IntegerField(blank=True, null=True)
    new_count_after = models.IntegerField(blank=True, null=True)
    imported = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_legacy_image_import_temp'


class LogPhoneReleaseDateTemp(models.Model):
    entity_id = models.IntegerField(primary_key=True)
    parent_id = models.IntegerField()
    entity_varchar = models.CharField(max_length=255)
    url_key = models.CharField(max_length=255)
    url_path = models.CharField(max_length=255)
    release_date = models.DateTimeField()
    previous_date = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_phone_release_date_temp'


class LogQuote(models.Model):
    quote_id = models.IntegerField(primary_key=True)
    visitor_id = models.BigIntegerField(blank=True, null=True)
    created_at = TimestampField()
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_quote'


class LogSummary(models.Model):
    summary_id = models.BigIntegerField(primary_key=True)
    store_id = models.SmallIntegerField()
    type_id = models.SmallIntegerField(blank=True, null=True)
    visitor_count = models.IntegerField()
    customer_count = models.IntegerField()
    add_date = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_summary'


class LogSummaryType(models.Model):
    type_id = models.SmallIntegerField(primary_key=True)
    type_code = models.CharField(max_length=64, blank=True, null=True)
    period = models.SmallIntegerField()
    period_type = models.CharField(max_length=6)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_summary_type'


class LogUrl(models.Model):
    url_id = models.BigIntegerField(primary_key=True)
    visitor_id = models.BigIntegerField(blank=True, null=True)
    visit_time = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_url'


class LogUrlInfo(models.Model):
    url_id = models.BigIntegerField(primary_key=True)
    url = models.CharField(max_length=255, blank=True, null=True)
    referer = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_url_info'


class LogVisitor(models.Model):
    visitor_id = models.BigIntegerField(primary_key=True)
    session_id = models.CharField(max_length=64, blank=True, null=True)
    first_visit_at = models.DateTimeField(blank=True, null=True)
    last_visit_at = models.DateTimeField()
    last_url_id = models.BigIntegerField()
    store_id = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_visitor'


class LogVisitorInfo(models.Model):
    visitor_id = models.BigIntegerField(primary_key=True)
    http_referer = models.CharField(max_length=255, blank=True, null=True)
    http_user_agent = models.CharField(max_length=255, blank=True, null=True)
    http_accept_charset = models.CharField(max_length=255, blank=True, null=True)
    http_accept_language = models.CharField(max_length=255, blank=True, null=True)
    server_addr = models.BigIntegerField(blank=True, null=True)
    remote_addr = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_visitor_info'


class LogVisitorOnline(models.Model):
    visitor_id = models.BigIntegerField(primary_key=True)
    visitor_type = models.CharField(max_length=1)
    remote_addr = models.BigIntegerField()
    first_visit_at = models.DateTimeField(blank=True, null=True)
    last_visit_at = models.DateTimeField(blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True)
    last_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'log_visitor_online'


class MFeedexportCustomAttribute(models.Model):
    attribute_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    conditions_serialized = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_custom_attribute'


class MFeedexportFeed(models.Model):
    feed_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    filename = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    format = models.TextField(blank=True, null=True)
    is_active = models.IntegerField()
    generated_at = models.DateTimeField(blank=True, null=True)
    generated_cnt = models.IntegerField(blank=True, null=True)
    generated_time = models.IntegerField(blank=True, null=True)
    cron = models.IntegerField()
    cron_day = models.CharField(max_length=255, blank=True, null=True)
    cron_time = models.CharField(max_length=255, blank=True, null=True)
    ftp = models.IntegerField()
    ftp_host = models.CharField(max_length=255, blank=True, null=True)
    ftp_user = models.CharField(max_length=255, blank=True, null=True)
    ftp_password = models.CharField(max_length=255, blank=True, null=True)
    ftp_path = models.CharField(max_length=255, blank=True, null=True)
    ftp_passive_mode = models.IntegerField(blank=True, null=True)
    uploaded_at = models.DateTimeField(blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()
    ga_source = models.CharField(max_length=255, blank=True, null=True)
    ga_medium = models.CharField(max_length=255, blank=True, null=True)
    ga_name = models.CharField(max_length=255, blank=True, null=True)
    ga_term = models.CharField(max_length=255, blank=True, null=True)
    ga_content = models.CharField(max_length=255, blank=True, null=True)
    notification_emails = models.CharField(max_length=255, blank=True, null=True)
    notification_events = models.CharField(max_length=255, blank=True, null=True)
    export_only_new = models.IntegerField()
    ftp_protocol = models.CharField(max_length=255)
    report_enabled = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_feed'


class MFeedexportFeedHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')
    type = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_feed_history'


class MFeedexportFeedProduct(models.Model):
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    is_new = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_feed_product'
        unique_together = (('feed', 'product'),)


class MFeedexportMappingCategory(models.Model):
    mapping_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    mapping_serialized = models.TextField()
    created_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_mapping_category'


class MFeedexportPerformanceAggregated(models.Model):
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    period = models.DateField()
    clicks = models.IntegerField(blank=True, null=True)
    orders = models.IntegerField(blank=True, null=True)
    revenue = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_performance_aggregated'
        unique_together = (('feed', 'product', 'store', 'period'),)


class MFeedexportPerformanceClick(models.Model):
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')
    session_id = models.CharField(max_length=255)
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_performance_click'
        unique_together = (('feed', 'session_id', 'product', 'store'),)


class MFeedexportPerformanceOrder(models.Model):
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')
    session_id = models.CharField(max_length=255)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4)
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_performance_order'
        unique_together = (('feed', 'session_id', 'product', 'store'),)


class MFeedexportRule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    conditions_serialized = models.TextField()
    actions_serialized = models.TextField()
    is_active = models.IntegerField()
    created_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_rule'


class MFeedexportRuleFeed(models.Model):
    rule = models.ForeignKey(MFeedexportRule, models.DO_NOTHING, related_name='+')
    feed = models.ForeignKey(MFeedexportFeed, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_rule_feed'
        unique_together = (('rule', 'feed'),)


class MFeedexportRuleProduct(models.Model):
    rule = models.ForeignKey(MFeedexportRule, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_rule_product'
        unique_together = (('rule', 'product', 'store'),)


class MFeedexportTemplate(models.Model):
    template_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    format = models.TextField(blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_feedexport_template'


class MMisspell(models.Model):
    misspell_id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=255)
    trigram = models.CharField(max_length=255)
    freq = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_misspell'


class MMisspellSuggest(models.Model):
    suggest_id = models.AutoField(primary_key=True)
    query = models.CharField(max_length=255)
    suggest = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_misspell_suggest'


class MMstcoreAttachment(models.Model):
    attachment_id = models.AutoField(primary_key=True)
    uid = models.CharField(unique=True, max_length=255)
    entity_type = models.CharField(max_length=255)
    entity_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    size = models.IntegerField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_mstcore_attachment'


class MMstcoreLogger(models.Model):
    log_id = models.AutoField(primary_key=True)
    level = models.IntegerField()
    message = models.CharField(max_length=255)
    content = models.TextField()
    trace = models.TextField()
    module = models.CharField(max_length=255)
    class_field = models.CharField(db_column='class', max_length=255)  # Field renamed because it was a Python reserved word.
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_mstcore_logger'


class MMstcoreUrlrewrite(models.Model):
    urlrewrite_id = models.AutoField(primary_key=True)
    url_key = models.CharField(max_length=255)
    module = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    entity_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_mstcore_urlrewrite'
        unique_together = (('module', 'type', 'entity_id'), ('url_key', 'module'),)


class MRmaComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    rma = models.ForeignKey('MRmaRma', models.DO_NOTHING, related_name='+')
    user = models.ForeignKey(AdminUser, models.DO_NOTHING, blank=True, null=True, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    customer_name = models.CharField(max_length=255)
    text = models.TextField(blank=True, null=True)
    is_html = models.IntegerField()
    is_visible_in_frontend = models.IntegerField()
    is_customer_notified = models.IntegerField()
    status = models.ForeignKey('MRmaStatus', models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    email_id = models.IntegerField(blank=True, null=True)
    is_read = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_comment'


class MRmaCondition(models.Model):
    condition_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sort_order = models.SmallIntegerField()
    is_active = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_condition'


class MRmaField(models.Model):
    field_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    values = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.IntegerField()
    sort_order = models.SmallIntegerField()
    is_required_staff = models.IntegerField()
    is_required_customer = models.IntegerField()
    is_visible_customer = models.IntegerField()
    is_editable_customer = models.IntegerField()
    visible_customer_status = models.CharField(max_length=255)
    is_show_in_confirm_shipping = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_field'


class MRmaItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    rma = models.ForeignKey('MRmaRma', models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField(blank=True, null=True)
    order_item_id = models.IntegerField(blank=True, null=True)
    reason = models.ForeignKey('MRmaReason', models.DO_NOTHING, blank=True, null=True, related_name='+')
    resolution = models.ForeignKey('MRmaResolution', models.DO_NOTHING, blank=True, null=True, related_name='+')
    condition = models.ForeignKey(MRmaCondition, models.DO_NOTHING, blank=True, null=True, related_name='+')
    qty_requested = models.IntegerField(blank=True, null=True)
    qty_returned = models.IntegerField(blank=True, null=True)
    created_at = TimestampField()
    updated_at = TimestampField()
    name = models.CharField(max_length=255)
    product_options = models.TextField(blank=True, null=True)
    to_stock = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_item'


class MRmaReason(models.Model):
    reason_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sort_order = models.SmallIntegerField()
    is_active = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_reason'


class MRmaResolution(models.Model):
    resolution_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sort_order = models.SmallIntegerField()
    is_active = models.IntegerField()
    code = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_resolution'


class MRmaRma(models.Model):
    rma_id = models.AutoField(primary_key=True)
    increment_id = models.CharField(unique=True, max_length=255)
    guest_id = models.CharField(max_length=255)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    telephone = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    region_id = models.IntegerField(blank=True, null=True)
    country_id = models.CharField(max_length=255)
    postcode = models.CharField(max_length=255)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')
    status = models.ForeignKey('MRmaStatus', models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    tracking_code = models.CharField(max_length=255)
    is_resolved = models.IntegerField()
    created_at = TimestampField()
    updated_at = TimestampField()
    ticket_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    last_reply_name = models.CharField(max_length=255)
    last_reply_at = models.DateTimeField(blank=True, null=True)
    is_gift = models.IntegerField()
    exchange_order_id = models.IntegerField(blank=True, null=True)
    credit_memo_id = models.IntegerField(blank=True, null=True)
    number_111 = models.TextField(db_column='111', blank=True, null=True)  # Field renamed because it wasn't a valid Python identifier.

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_rma'


class MRmaRmaStore(models.Model):
    rma_store_id = models.AutoField(primary_key=True)
    rs_rma = models.ForeignKey(MRmaRma, models.DO_NOTHING, related_name='+')
    rs_store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_rma_store'


class MRmaStatus(models.Model):
    status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    sort_order = models.SmallIntegerField()
    is_rma_resolved = models.IntegerField()
    customer_message = models.TextField(blank=True, null=True)
    admin_message = models.TextField(blank=True, null=True)
    history_message = models.TextField(blank=True, null=True)
    is_active = models.IntegerField()
    code = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_rma_status'


class MSearchindex(models.Model):
    index_id = models.AutoField(primary_key=True)
    index_code = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    position = models.IntegerField()
    attributes_serialized = models.TextField(blank=True, null=True)
    properties_serialized = models.TextField(blank=True, null=True)
    status = models.IntegerField()
    is_active = models.IntegerField()
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_searchindex'


class MSearchlandingpage(models.Model):
    page_id = models.AutoField(primary_key=True)
    query_text = models.CharField(max_length=255)
    url_key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    meta_title = models.CharField(max_length=255)
    meta_keywords = models.CharField(max_length=255)
    meta_description = models.CharField(max_length=255)
    layout = models.TextField(blank=True, null=True)
    is_active = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_searchlandingpage'


class MSearchsphinxStopword(models.Model):
    stopword_id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=255)
    store = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_searchsphinx_stopword'


class MSearchsphinxSynonym(models.Model):
    synonym_id = models.AutoField(primary_key=True)
    word = models.CharField(max_length=255)
    synonyms = models.TextField()
    store = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'm_searchsphinx_synonym'


class Magenotification(models.Model):
    magenotification_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=255)
    severity = models.SmallIntegerField()
    is_read = models.IntegerField(blank=True, null=True)
    is_remove = models.IntegerField(blank=True, null=True)
    related_extensions = models.CharField(max_length=255, blank=True, null=True)
    added_date = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'magenotification'


class MagenotificationExtensionFeedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255)
    extension = models.CharField(max_length=255)
    extension_version = models.CharField(max_length=50)
    coupon_code = models.CharField(max_length=255)
    coupon_value = models.CharField(max_length=50)
    expired_counpon = models.DateTimeField()
    content = models.TextField()
    file = models.TextField()
    comment = models.TextField()
    latest_message = models.TextField()
    latest_response = models.TextField()
    latest_response_time = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField()
    is_sent = models.IntegerField()
    created = models.DateTimeField()
    updated = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'magenotification_extension_feedback'


class MagenotificationExtensionFeedbackmessage(models.Model):
    feedbackmessage_id = models.AutoField(primary_key=True)
    feedback_id = models.IntegerField()
    feedback_code = models.CharField(max_length=255)
    user = models.CharField(max_length=255)
    is_customer = models.IntegerField(blank=True, null=True)
    message = models.TextField()
    file = models.TextField()
    posted_time = models.DateTimeField(blank=True, null=True)
    is_sent = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'magenotification_extension_feedbackmessage'


class MagenotificationLicense(models.Model):
    license_id = models.AutoField(primary_key=True)
    extension_code = models.CharField(max_length=100)
    license_key = models.TextField()
    active_at = models.DateField()
    sum_code = models.CharField(max_length=255, blank=True, null=True)
    response_code = models.SmallIntegerField(blank=True, null=True)
    domains = models.CharField(max_length=255, blank=True, null=True)
    is_valid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'magenotification_license'


class MagenotificationLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    extension_code = models.CharField(max_length=100)
    license_type = models.CharField(max_length=50)
    license_key = models.TextField()
    check_date = models.DateField()
    sum_code = models.CharField(max_length=255, blank=True, null=True)
    response_code = models.SmallIntegerField(blank=True, null=True)
    expired_time = models.CharField(max_length=255, blank=True, null=True)
    is_valid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'magenotification_log'


class MobileRedirect(models.Model):
    entity_id = models.AutoField(primary_key=True)
    user_agent = models.CharField(unique=True, max_length=255)
    category_id = models.IntegerField(blank=True, null=True)
    visitors = models.IntegerField()
    views = models.IntegerField()
    first_hit_date = models.DateTimeField()
    last_hit_date = models.DateTimeField()
    is_bot = models.SmallIntegerField()
    device_model_number = models.CharField(max_length=50, blank=True, null=True)
    update_date = models.DateTimeField(blank=True, null=True)
    update_admin_user = models.IntegerField(blank=True, null=True)
    redirect_rule_id = models.SmallIntegerField(blank=True, null=True)
    redirections = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mobile_redirect'


class MobileRedirectRule(models.Model):
    entity_id = models.SmallIntegerField(primary_key=True)
    device_name = models.CharField(unique=True, max_length=30)
    search_include = models.CharField(max_length=100)
    search_exclude = models.CharField(max_length=100)
    search_pattern_start = models.CharField(max_length=100)
    search_pattern_end = models.CharField(max_length=100)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mobile_redirect_rule'


class Morecc(models.Model):
    morecc_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    cus_id = models.IntegerField(blank=True, null=True)
    number = models.CharField(max_length=255)
    card_type = models.CharField(max_length=255)
    expr_month = models.CharField(max_length=255)
    expr_year = models.CharField(max_length=255)
    profile_id = models.CharField(max_length=255)
    pay_id = models.CharField(max_length=255)
    ship_id = models.CharField(max_length=255)
    status = models.SmallIntegerField()
    created_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'morecc'


class MstLicense(models.Model):
    license_id = models.AutoField(primary_key=True)
    domain_count = models.CharField(max_length=255)
    domain_list = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    extension_code = models.CharField(max_length=255)
    license_key = models.CharField(max_length=255)
    created_time = models.DateField()
    domains = models.CharField(max_length=255)
    is_valid = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_license'


class MstPdpAct(models.Model):
    act_id = models.AutoField(primary_key=True)
    domain_count = models.CharField(max_length=255)
    domain_list = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    extension_code = models.CharField(max_length=255)
    act_key = models.CharField(max_length=255)
    created_time = models.DateField()
    domains = models.CharField(max_length=255)
    is_valid = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_act'


class MstPdpAdminTemplate(models.Model):
    product_id = models.IntegerField()
    pdp_design = models.TextField()
    status = models.SmallIntegerField()
    created_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_admin_template'


class MstPdpArtworkCategory(models.Model):
    title = models.CharField(max_length=500)
    status = models.SmallIntegerField()
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_artwork_category'


class MstPdpColors(models.Model):
    color_id = models.AutoField(primary_key=True)
    color_name = models.CharField(max_length=255)
    color_code = models.CharField(max_length=500)
    status = models.SmallIntegerField()
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_colors'


class MstPdpCustomerTemplate(models.Model):
    product_id = models.IntegerField()
    customer_id = models.IntegerField()
    filename = models.CharField(max_length=500)
    status = models.SmallIntegerField()
    created_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    design_title = models.CharField(max_length=500)
    design_note = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_customer_template'


class MstPdpFonts(models.Model):
    font_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    ext = models.CharField(max_length=500)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_fonts'


class MstPdpImageColor(models.Model):
    image_id = models.IntegerField()
    filename = models.CharField(max_length=500)
    color = models.CharField(max_length=500)
    filename_back = models.CharField(max_length=500)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_image_color'


class MstPdpImages(models.Model):
    image_id = models.AutoField(primary_key=True)
    image_type = models.CharField(max_length=255)
    filename = models.CharField(max_length=500)
    category = models.CharField(max_length=500)
    color = models.TextField()
    position = models.IntegerField()
    image_name = models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    color_type = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_images'


class MstPdpJsonFiles(models.Model):
    filename = models.CharField(max_length=500)
    description = models.TextField()
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_json_files'


class MstPdpMultisides(models.Model):
    product_id = models.IntegerField()
    label = models.CharField(max_length=500)
    color_id = models.IntegerField()
    inlay_w = models.CharField(max_length=255)
    inlay_h = models.CharField(max_length=255)
    inlay_t = models.CharField(max_length=255)
    inlay_l = models.CharField(max_length=255)
    filename = models.CharField(max_length=500)
    position = models.IntegerField()
    status = models.SmallIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    overlay = models.CharField(max_length=500)
    color_code = models.CharField(max_length=100)
    color_name = models.CharField(max_length=100)
    background_type = models.CharField(max_length=10)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_multisides'


class MstPdpMultisidesColors(models.Model):
    product_id = models.IntegerField()
    color_id = models.IntegerField()
    status = models.SmallIntegerField()
    position = models.IntegerField()
    color_code = models.CharField(max_length=100)
    color_name = models.CharField(max_length=100)
    color_thumbnail = models.CharField(max_length=100)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_multisides_colors'


class MstPdpMultisidesColorsImages(models.Model):
    product_color_id = models.IntegerField()
    side_id = models.IntegerField()
    filename = models.CharField(max_length=500)
    overlay = models.CharField(max_length=500)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_multisides_colors_images'


class MstPdpProductStatus(models.Model):
    product_id = models.IntegerField()
    note = models.CharField(max_length=500)
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_product_status'


class MstPdpShapeCategory(models.Model):
    title = models.CharField(max_length=500)
    status = models.SmallIntegerField()
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_shape_category'


class MstPdpShapes(models.Model):
    filename = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    category = models.CharField(max_length=500)
    tag = models.CharField(max_length=500)
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_shapes'


class MstPdpTexts(models.Model):
    text_id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=255)
    tags = models.TextField()
    is_popular = models.SmallIntegerField()
    status = models.SmallIntegerField()
    position = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdp_texts'


class MstPdpdesignShare(models.Model):
    product_id = models.IntegerField()
    pdpdesign = models.TextField()
    url = models.TextField()
    note = models.CharField(max_length=500)
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'mst_pdpdesign_share'


class NewsletterProblem(models.Model):
    problem_id = models.AutoField(primary_key=True)
    subscriber = models.ForeignKey('NewsletterSubscriber', models.DO_NOTHING, blank=True, null=True, related_name='+')
    queue = models.ForeignKey('NewsletterQueue', models.DO_NOTHING, related_name='+')
    problem_error_code = models.IntegerField(blank=True, null=True)
    problem_error_text = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_problem'


class NewsletterQueue(models.Model):
    queue_id = models.AutoField(primary_key=True)
    template = models.ForeignKey('NewsletterTemplate', models.DO_NOTHING, related_name='+')
    newsletter_type = models.IntegerField(blank=True, null=True)
    newsletter_text = models.TextField(blank=True, null=True)
    newsletter_styles = models.TextField(blank=True, null=True)
    newsletter_subject = models.CharField(max_length=200, blank=True, null=True)
    newsletter_sender_name = models.CharField(max_length=200, blank=True, null=True)
    newsletter_sender_email = models.CharField(max_length=200, blank=True, null=True)
    queue_status = models.IntegerField()
    queue_start_at = models.DateTimeField(blank=True, null=True)
    queue_finish_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_queue'


class NewsletterQueueLink(models.Model):
    queue_link_id = models.AutoField(primary_key=True)
    queue = models.ForeignKey(NewsletterQueue, models.DO_NOTHING, related_name='+')
    subscriber = models.ForeignKey('NewsletterSubscriber', models.DO_NOTHING, related_name='+')
    letter_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_queue_link'


class NewsletterQueueStoreLink(models.Model):
    queue = models.ForeignKey(NewsletterQueue, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_queue_store_link'
        unique_together = (('queue', 'store'),)


class NewsletterSubscriber(models.Model):
    subscriber_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    change_status_at = models.DateTimeField(blank=True, null=True)
    customer_id = models.IntegerField()
    subscriber_email = models.CharField(max_length=150, blank=True, null=True)
    subscriber_status = models.IntegerField()
    subscriber_confirm_code = models.CharField(max_length=32, blank=True, null=True)
    subscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_subscriber'


class NewsletterTemplate(models.Model):
    template_id = models.AutoField(primary_key=True)
    template_code = models.CharField(max_length=150, blank=True, null=True)
    template_text = models.TextField(blank=True, null=True)
    template_text_preprocessed = models.TextField(blank=True, null=True)
    template_styles = models.TextField(blank=True, null=True)
    template_type = models.IntegerField(blank=True, null=True)
    template_subject = models.CharField(max_length=200, blank=True, null=True)
    template_sender_name = models.CharField(max_length=200, blank=True, null=True)
    template_sender_email = models.CharField(max_length=200, blank=True, null=True)
    template_actual = models.SmallIntegerField(blank=True, null=True)
    added_at = models.DateTimeField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'newsletter_template'


class OauthConsumer(models.Model):
    entity_id = models.AutoField(primary_key=True)
    created_at = TimestampField()
    updated_at = TimestampField(blank=True, null=True)
    name = models.CharField(max_length=255)
    key = models.CharField(unique=True, max_length=32)
    secret = models.CharField(unique=True, max_length=32)
    callback_url = models.CharField(max_length=255, blank=True, null=True)
    rejected_callback_url = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'oauth_consumer'


class OauthNonce(models.Model):
    nonce = models.CharField(unique=True, max_length=32)
    timestamp = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'oauth_nonce'


class OauthToken(models.Model):
    entity_id = models.AutoField(primary_key=True)
    consumer = models.ForeignKey(OauthConsumer, models.DO_NOTHING, related_name='+')
    admin = models.ForeignKey(AdminUser, models.DO_NOTHING, blank=True, null=True, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    type = models.CharField(max_length=16)
    token = models.CharField(unique=True, max_length=32)
    secret = models.CharField(max_length=32)
    verifier = models.CharField(max_length=32, blank=True, null=True)
    callback_url = models.CharField(max_length=255)
    revoked = models.SmallIntegerField()
    authorized = models.SmallIntegerField()
    created_at = TimestampField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'oauth_token'


class PaypalCert(models.Model):
    cert_id = models.SmallIntegerField(primary_key=True)
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    content = models.TextField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'paypal_cert'


class PaypalPaymentTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    txn_id = models.CharField(unique=True, max_length=100, blank=True, null=True)
    additional_information = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'paypal_payment_transaction'


class PaypalSettlementReport(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_date = models.DateTimeField(blank=True, null=True)
    account_id = models.CharField(max_length=64, blank=True, null=True)
    filename = models.CharField(max_length=24, blank=True, null=True)
    last_modified = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'paypal_settlement_report'
        unique_together = (('report_date', 'account_id'),)


class PaypalSettlementReportRow(models.Model):
    row_id = models.AutoField(primary_key=True)
    report = models.ForeignKey(PaypalSettlementReport, models.DO_NOTHING, related_name='+')
    transaction_id = models.CharField(max_length=19, blank=True, null=True)
    invoice_id = models.CharField(max_length=127, blank=True, null=True)
    paypal_reference_id = models.CharField(max_length=19, blank=True, null=True)
    paypal_reference_id_type = models.CharField(max_length=3, blank=True, null=True)
    transaction_event_code = models.CharField(max_length=5, blank=True, null=True)
    transaction_initiation_date = models.DateTimeField(blank=True, null=True)
    transaction_completion_date = models.DateTimeField(blank=True, null=True)
    transaction_debit_or_credit = models.CharField(max_length=2)
    gross_transaction_amount = models.DecimalField(max_digits=20, decimal_places=6)
    gross_transaction_currency = models.CharField(max_length=3, blank=True, null=True)
    fee_debit_or_credit = models.CharField(max_length=2, blank=True, null=True)
    fee_amount = models.DecimalField(max_digits=20, decimal_places=6)
    fee_currency = models.CharField(max_length=3, blank=True, null=True)
    custom_field = models.CharField(max_length=255, blank=True, null=True)
    consumer_id = models.CharField(max_length=127, blank=True, null=True)
    payment_tracking_id = models.CharField(max_length=255, blank=True, null=True)
    store_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'paypal_settlement_report_row'


class PersistentSession(models.Model):
    persistent_id = models.AutoField(primary_key=True)
    key = models.CharField(unique=True, max_length=50)
    customer = models.OneToOneField(CustomerEntity, models.DO_NOTHING, unique=True, blank=True, null=True, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    info = models.TextField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'persistent_session'


class Poll(models.Model):
    poll_id = models.AutoField(primary_key=True)
    poll_title = models.CharField(max_length=255, blank=True, null=True)
    votes_count = models.IntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    date_posted = models.DateTimeField()
    date_closed = models.DateTimeField(blank=True, null=True)
    active = models.SmallIntegerField()
    closed = models.SmallIntegerField()
    answers_display = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'poll'


class PollAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    poll = models.ForeignKey(Poll, models.DO_NOTHING, related_name='+')
    answer_title = models.CharField(max_length=255, blank=True, null=True)
    votes_count = models.IntegerField()
    answer_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'poll_answer'


class PollStore(models.Model):
    poll = models.ForeignKey(Poll, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'poll_store'
        unique_together = (('poll', 'store'),)


class PollVote(models.Model):
    vote_id = models.AutoField(primary_key=True)
    poll_id = models.IntegerField()
    poll_answer = models.ForeignKey(PollAnswer, models.DO_NOTHING, related_name='+')
    ip_address = models.BigIntegerField(blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True)
    vote_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'poll_vote'


class ProductAlertPrice(models.Model):
    alert_price_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    price = models.DecimalField(max_digits=12, decimal_places=4)
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    add_date = models.DateTimeField()
    last_send_date = models.DateTimeField(blank=True, null=True)
    send_count = models.SmallIntegerField()
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'product_alert_price'


class ProductAlertStock(models.Model):
    alert_stock_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    add_date = models.DateTimeField()
    send_date = models.DateTimeField(blank=True, null=True)
    send_count = models.SmallIntegerField()
    status = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'product_alert_stock'


class Rating(models.Model):
    rating_id = models.SmallIntegerField(primary_key=True)
    entity = models.ForeignKey('RatingEntity', models.DO_NOTHING, related_name='+')
    rating_code = models.CharField(unique=True, max_length=64)
    position = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating'


class RatingEntity(models.Model):
    entity_id = models.SmallIntegerField(primary_key=True)
    entity_code = models.CharField(unique=True, max_length=64)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_entity'


class RatingOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    rating = models.ForeignKey(Rating, models.DO_NOTHING, related_name='+')
    code = models.CharField(max_length=32)
    value = models.SmallIntegerField()
    position = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_option'


class RatingOptionVote(models.Model):
    vote_id = models.BigIntegerField(primary_key=True)
    option = models.ForeignKey(RatingOption, models.DO_NOTHING, related_name='+')
    remote_ip = models.CharField(max_length=16)
    remote_ip_long = models.BigIntegerField()
    customer_id = models.IntegerField(blank=True, null=True)
    entity_pk_value = models.BigIntegerField()
    rating_id = models.SmallIntegerField()
    review = models.ForeignKey('Review', models.DO_NOTHING, blank=True, null=True, related_name='+')
    percent = models.SmallIntegerField()
    value = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_option_vote'


class RatingOptionVoteAggregated(models.Model):
    primary_id = models.AutoField(primary_key=True)
    rating = models.ForeignKey(Rating, models.DO_NOTHING, related_name='+')
    entity_pk_value = models.BigIntegerField()
    vote_count = models.IntegerField()
    vote_value_sum = models.IntegerField()
    percent = models.SmallIntegerField()
    percent_approved = models.SmallIntegerField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_option_vote_aggregated'


class RatingStore(models.Model):
    rating = models.ForeignKey(Rating, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_store'
        unique_together = (('rating', 'store'),)


class RatingTitle(models.Model):
    rating = models.ForeignKey(Rating, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'rating_title'
        unique_together = (('rating', 'store'),)


class RecommendationEngineMapping(models.Model):
    store_id = models.IntegerField()
    product_id = models.IntegerField()
    product_ids = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'recommendation_engine_mapping'
        unique_together = (('id', 'store_id', 'product_id'),)


class ReportComparedProductIndex(models.Model):
    index_id = models.BigIntegerField(primary_key=True)
    visitor_id = models.IntegerField(blank=True, null=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    added_at = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_compared_product_index'
        unique_together = (('visitor_id', 'product'), ('customer', 'product'),)


class ReportEvent(models.Model):
    event_id = models.BigIntegerField(primary_key=True)
    logged_at = models.DateTimeField()
    event_type = models.ForeignKey('ReportEventTypes', models.DO_NOTHING, related_name='+')
    object_id = models.IntegerField()
    subject_id = models.IntegerField()
    subtype = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_event'


class ReportEventTypes(models.Model):
    event_type_id = models.SmallIntegerField(primary_key=True)
    event_name = models.CharField(max_length=64)
    customer_login = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_event_types'


class ReportViewedProductAggregatedDaily(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    views_num = models.IntegerField()
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_viewed_product_aggregated_daily'
        unique_together = (('period', 'store', 'product'),)


class ReportViewedProductAggregatedMonthly(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    views_num = models.IntegerField()
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_viewed_product_aggregated_monthly'
        unique_together = (('period', 'store', 'product'),)


class ReportViewedProductAggregatedYearly(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    views_num = models.IntegerField()
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_viewed_product_aggregated_yearly'
        unique_together = (('period', 'store', 'product'),)


class ReportViewedProductIndex(models.Model):
    index_id = models.BigIntegerField(primary_key=True)
    visitor_id = models.IntegerField(blank=True, null=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    added_at = models.DateTimeField()
    brand_model = models.CharField(max_length=255, blank=True, null=True)
    added_from_category_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'report_viewed_product_index'
        unique_together = (('customer', 'product'), ('visitor_id', 'product'),)


class ResponsysImport(models.Model):
    entity_id = models.CharField(primary_key=True, max_length=50)
    imported_at = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'responsys_import'


class ResponsysPushEvent(models.Model):
    entity_id = models.SmallIntegerField(primary_key=True)
    push_event_name = models.CharField(max_length=50)
    table_name = models.CharField(max_length=50)
    folder_name = models.CharField(max_length=50)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'responsys_push_event'
        unique_together = (('push_event_name', 'table_name', 'folder_name'),)


class ResponsysQueue(models.Model):
    entity_id = models.AutoField(primary_key=True)
    match_column_name = models.CharField(max_length=250)
    store_id = models.SmallIntegerField()
    push_event_id = models.SmallIntegerField()
    push_result = models.SmallIntegerField()
    created_at = TimestampField()
    modified_at = models.DateTimeField()
    delay_event = models.CharField(max_length=250, blank=True, null=True)
    time_delay = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'responsys_queue'
        unique_together = (('match_column_name', 'store_id', 'push_event_id'),)


class Review(models.Model):
    review_id = models.BigIntegerField(primary_key=True)
    created_at = TimestampField()
    entity = models.ForeignKey('ReviewEntity', models.DO_NOTHING, related_name='+')
    entity_pk_value = models.IntegerField()
    status = models.ForeignKey('ReviewStatus', models.DO_NOTHING, related_name='+')
    brand_model = models.CharField(max_length=255, blank=True, null=True)
    added_from_category_id = models.IntegerField(blank=True, null=True)
    review_source = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review'


class ReviewDetail(models.Model):
    detail_id = models.BigIntegerField(primary_key=True)
    review = models.ForeignKey(Review, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    title = models.CharField(max_length=255)
    detail = models.TextField()
    nickname = models.CharField(max_length=128)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review_detail'


class ReviewEntity(models.Model):
    entity_id = models.SmallIntegerField(primary_key=True)
    entity_code = models.CharField(max_length=32)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review_entity'


class ReviewEntitySummary(models.Model):
    primary_id = models.BigIntegerField(primary_key=True)
    entity_pk_value = models.BigIntegerField()
    entity_type = models.SmallIntegerField()
    reviews_count = models.SmallIntegerField()
    rating_summary = models.SmallIntegerField()
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review_entity_summary'


class ReviewStatus(models.Model):
    status_id = models.SmallIntegerField(primary_key=True)
    status_code = models.CharField(max_length=32)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review_status'


class ReviewStore(models.Model):
    review = models.ForeignKey(Review, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'review_store'
        unique_together = (('review', 'store'),)


class SalesBestsellersAggregatedByCategory(models.Model):
    added_from_category_id = models.IntegerField()
    product_ids = models.TextField(blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_by_category'


class SalesBestsellersAggregatedByCategoryBrand(models.Model):
    entity_id = models.AutoField(primary_key=True)
    category_id = models.IntegerField()
    model_id = models.IntegerField()
    brand_id = models.IntegerField()
    category_key = models.CharField(max_length=255)
    model_key = models.CharField(max_length=255)
    brand_key = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    brand_name = models.CharField(max_length=255)
    qty_line_item_ordered_15d = models.IntegerField()
    qty_line_item_ordered_30d = models.IntegerField()
    qty_line_item_ordered_45d = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_by_category_brand'
        unique_together = (('category_key', 'model_id', 'brand_id'),)


class SalesBestsellersAggregatedByProduct(models.Model):
    entity_id = models.AutoField(primary_key=True)
    product_id = models.IntegerField()
    category_id = models.IntegerField()
    store_id = models.IntegerField()
    qty_line_item_ordered_15d = models.IntegerField()
    qty_line_item_ordered_30d = models.IntegerField()
    qty_line_item_ordered_45d = models.IntegerField()
    qty_line_item_ordered_60d = models.IntegerField()
    qty_line_item_ordered_90d = models.IntegerField()
    qty_line_item_ordered_365d = models.IntegerField()
    qty_line_item_ordered = models.CharField(max_length=250, blank=True, null=True)
    qty_item_ordered = models.CharField(max_length=250, blank=True, null=True)
    last_item_ordered = models.DateTimeField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_by_product'
        unique_together = (('product_id', 'category_id', 'store_id'),)


class SalesBestsellersAggregatedDaily(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=4)
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_daily'
        unique_together = (('period', 'store', 'product'),)


class SalesBestsellersAggregatedMonthly(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=4)
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_monthly'
        unique_together = (('period', 'store', 'product'),)


class SalesBestsellersAggregatedYearly(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product_name = models.CharField(max_length=255, blank=True, null=True)
    product_price = models.DecimalField(max_digits=12, decimal_places=4)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=4)
    rating_pos = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_bestsellers_aggregated_yearly'
        unique_together = (('period', 'store', 'product'),)


class SalesBillingAgreement(models.Model):
    agreement_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    method_code = models.CharField(max_length=32)
    reference_id = models.CharField(max_length=32)
    status = models.CharField(max_length=20)
    created_at = TimestampField()
    updated_at = TimestampField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    agreement_label = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_billing_agreement'


class SalesBillingAgreementOrder(models.Model):
    agreement = models.ForeignKey(SalesBillingAgreement, models.DO_NOTHING, related_name='+')
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_billing_agreement_order'
        unique_together = (('agreement', 'order'),)


class SalesFlatCreditmemo(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    adjustment_positive = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_adjustment_negative = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    adjustment_negative = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_base_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_global_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_adjustment = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    adjustment = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_adjustment_positive = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')
    email_sent = models.SmallIntegerField(blank=True, null=True)
    creditmemo_status = models.IntegerField(blank=True, null=True)
    state = models.IntegerField(blank=True, null=True)
    shipping_address_id = models.IntegerField(blank=True, null=True)
    billing_address_id = models.IntegerField(blank=True, null=True)
    invoice_id = models.IntegerField(blank=True, null=True)
    store_currency_code = models.CharField(max_length=3, blank=True, null=True)
    order_currency_code = models.CharField(max_length=3, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    global_currency_code = models.CharField(max_length=3, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_hidden_tax_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_description = models.CharField(max_length=255, blank=True, null=True)
    base_reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_points_balance = models.IntegerField(blank=True, null=True)
    reward_points_balance_refund = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_creditmemo'


class SalesFlatCreditmemoComment(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatCreditmemo, models.DO_NOTHING, related_name='+')
    is_customer_notified = models.IntegerField(blank=True, null=True)
    is_visible_on_front = models.SmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    admin_user_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_creditmemo_comment'


class SalesFlatCreditmemoGrid(models.Model):
    entity = models.OneToOneField(SalesFlatCreditmemo, models.DO_NOTHING, primary_key=True, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    store_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_base_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_global_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_id = models.IntegerField()
    creditmemo_status = models.IntegerField(blank=True, null=True)
    state = models.IntegerField(blank=True, null=True)
    invoice_id = models.IntegerField(blank=True, null=True)
    store_currency_code = models.CharField(max_length=3, blank=True, null=True)
    order_currency_code = models.CharField(max_length=3, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    global_currency_code = models.CharField(max_length=3, blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    order_increment_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    order_created_at = TimestampField(blank=True, null=True)
    billing_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_creditmemo_grid'


class SalesFlatCreditmemoItem(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatCreditmemo, models.DO_NOTHING, related_name='+')
    base_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    order_item_id = models.IntegerField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied = models.TextField(blank=True, null=True)
    base_weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_row_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_row_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_creditmemo_item'


class SalesFlatInvoice(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_base_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_global_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    billing_address_id = models.IntegerField(blank=True, null=True)
    is_used_for_refund = models.SmallIntegerField(blank=True, null=True)
    order = models.ForeignKey('SalesFlatOrder', models.DO_NOTHING, related_name='+')
    email_sent = models.SmallIntegerField(blank=True, null=True)
    can_void_flag = models.SmallIntegerField(blank=True, null=True)
    state = models.IntegerField(blank=True, null=True)
    shipping_address_id = models.IntegerField(blank=True, null=True)
    store_currency_code = models.CharField(max_length=3, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    order_currency_code = models.CharField(max_length=3, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    global_currency_code = models.CharField(max_length=3, blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_hidden_tax_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_description = models.CharField(max_length=255, blank=True, null=True)
    base_reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_points_balance = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_invoice'


class SalesFlatInvoiceComment(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatInvoice, models.DO_NOTHING, related_name='+')
    is_customer_notified = models.SmallIntegerField(blank=True, null=True)
    is_visible_on_front = models.SmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    admin_user_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_invoice_comment'


class SalesFlatInvoiceGrid(models.Model):
    entity = models.OneToOneField(SalesFlatInvoice, models.DO_NOTHING, primary_key=True, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_id = models.IntegerField()
    state = models.IntegerField(blank=True, null=True)
    store_currency_code = models.CharField(max_length=3, blank=True, null=True)
    order_currency_code = models.CharField(max_length=3, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    global_currency_code = models.CharField(max_length=3, blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    order_increment_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    order_created_at = TimestampField(blank=True, null=True)
    billing_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_invoice_grid'


class SalesFlatInvoiceItem(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatInvoice, models.DO_NOTHING, related_name='+')
    base_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    order_item_id = models.IntegerField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_row_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_row_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied = models.TextField(blank=True, null=True)
    weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_invoice_item'


class SalesFlatOrder(models.Model):
    entity_id = models.AutoField(primary_key=True)
    state = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    coupon_code = models.CharField(max_length=255, blank=True, null=True)
    protect_code = models.CharField(max_length=255, blank=True, null=True)
    shipping_description = models.CharField(max_length=255, blank=True, null=True)
    is_virtual = models.SmallIntegerField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_global_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_invoiced_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_offline_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_online_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_qty_ordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    discount_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_base_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_order_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_offline_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_online_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_qty_ordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    can_ship_partially = models.SmallIntegerField(blank=True, null=True)
    can_ship_partially_item = models.SmallIntegerField(blank=True, null=True)
    customer_is_guest = models.SmallIntegerField(blank=True, null=True)
    customer_note_notify = models.SmallIntegerField(blank=True, null=True)
    billing_address = models.ForeignKey('SalesFlatOrderAddress', blank=True, null=True, related_name = 'billing_address')
    customer_group_id = models.SmallIntegerField(blank=True, null=True)
    edit_increment = models.IntegerField(blank=True, null=True)
    email_sent = models.SmallIntegerField(blank=True, null=True)
    forced_shipment_with_invoice = models.SmallIntegerField(blank=True, null=True)
    payment_auth_expiration = models.IntegerField(blank=True, null=True)
    quote_address_id = models.IntegerField(blank=True, null=True)
    quote_id = models.IntegerField(blank=True, null=True)
    shipping_address = models.ForeignKey('SalesFlatOrderAddress', blank=True, null=True, related_name = 'shipping_address')
    adjustment_negative = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    adjustment_positive = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_adjustment_negative = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_adjustment_positive = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_due = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    payment_authorization_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_due = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    customer_dob = models.DateTimeField(blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    applied_rule_ids = models.CharField(max_length=255, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    customer_email = models.CharField(max_length=255, blank=True, null=True)
    customer_firstname = models.CharField(max_length=255, blank=True, null=True)
    customer_lastname = models.CharField(max_length=255, blank=True, null=True)
    customer_middlename = models.CharField(max_length=255, blank=True, null=True)
    customer_prefix = models.CharField(max_length=255, blank=True, null=True)
    customer_suffix = models.CharField(max_length=255, blank=True, null=True)
    customer_taxvat = models.CharField(max_length=255, blank=True, null=True)
    discount_description = models.CharField(max_length=255, blank=True, null=True)
    ext_customer_id = models.CharField(max_length=255, blank=True, null=True)
    ext_order_id = models.CharField(max_length=255, blank=True, null=True)
    global_currency_code = models.CharField(max_length=3, blank=True, null=True)
    hold_before_state = models.CharField(max_length=255, blank=True, null=True)
    hold_before_status = models.CharField(max_length=255, blank=True, null=True)
    order_currency_code = models.CharField(max_length=255, blank=True, null=True)
    original_increment_id = models.CharField(max_length=50, blank=True, null=True)
    relation_child_id = models.CharField(max_length=32, blank=True, null=True)
    relation_child_real_id = models.CharField(max_length=32, blank=True, null=True)
    relation_parent_id = models.CharField(max_length=32, blank=True, null=True)
    relation_parent_real_id = models.CharField(max_length=32, blank=True, null=True)
    remote_ip = models.CharField(max_length=255, blank=True, null=True)
    shipping_method = models.CharField(max_length=255, blank=True, null=True)
    store_currency_code = models.CharField(max_length=3, blank=True, null=True)
    store_name = models.CharField(max_length=255, blank=True, null=True)
    x_forwarded_for = models.CharField(max_length=255, blank=True, null=True)
    customer_note = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    total_item_count = models.SmallIntegerField()
    customer_gender = models.IntegerField(blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_hidden_tax_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    coupon_rule_name = models.CharField(max_length=255, blank=True, null=True)
    paypal_ipn_customer_notified = models.IntegerField(blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)
    allow_reminders = models.IntegerField()
    is_archieved = models.IntegerField()
    is_edit = models.IntegerField()
    edit_comments = models.TextField(blank=True, null=True)
    delivery_at = models.DateTimeField(blank=True, null=True)
    admin_email = models.CharField(max_length=255, blank=True, null=True)
    order_source = models.CharField(max_length=100, blank=True, null=True)
    marketplace_order_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    marketplace_seller_order_id = models.CharField(max_length=50, blank=True, null=True)
    marketplace_last_action = models.CharField(max_length=50, blank=True, null=True)
    shipping_progress = models.IntegerField(blank=True, null=True)
    reward_points_balance = models.IntegerField(blank=True, null=True)
    base_reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_rwrd_crrncy_amt_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    rwrd_currency_amount_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_rwrd_crrncy_amnt_refnded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    rwrd_crrncy_amnt_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_points_balance_refund = models.IntegerField(blank=True, null=True)
    reward_points_balance_refunded = models.IntegerField(blank=True, null=True)
    reward_salesrule_points = models.IntegerField(blank=True, null=True)

    @classmethod
    def build_order_info(self, customer_orders):
        """
        Builds a list of order information, including products.
        :param customer_orders: list of order objects from SalesFlatOrder
        :return:
        """
        from modjento.utils import save_percent
        rg_orders = []
        product_ids = []
        for order in customer_orders:
            for item in order.salesflatorderitem_set.all():
                product_ids.append((item.product_id, item.added_from_category_id))
        rg_fields = ['name', 'image', 'product_type',
                     'price', 'special_price', 'msrp',
                     'special_from_date', 'special_to_date',
                     'url_path', 'url_key']
        rg_temp = list({ x for x, _ in product_ids })
        p_attr = EavAttribute.objects.get_values(
            rg_temp,
            field_names=rg_fields,
        )
        for order in customer_orders:
            order_items = []
            item_qty = 0
            for item in order.salesflatorderitem_set.all():
                data = p_attr.get(item.product_id, {})
                if data.get('image', None) and data.get('image').startswith('URL/'):
                    image = data.get('image').replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
                else:
                    image = 'http://cellularoutfitter.com/media/catalog/product%s' % (data.get('image',))
                item_qty += int(item.qty_ordered)
                item_info = {
                    'product_id': item.product_id,
                    'sku': item.sku,
                    'qty': int(item.qty_ordered),
                    'price': data.get('price'),
                    'special_price': item.price,
                    'total': float(item.price * item.qty_ordered),
                    'name': item.name,
                    'url_path': 'http://cellularoutfitter.com/%s/%s' % (
                        EavAttribute.objects.get_bmc_link(item.added_from_category_id).replace('.html', '/'),
                        data.get('url_path')
                    ),
                    'image': image,
                    'save_percent': save_percent(data.get('price'), item.price, item_id=item.product_id),
                    'save_dollars': int(round(
                        (data.get('price', 0) * float(item.qty_ordered)) - int(item.price * item.qty_ordered), 0
                    )),
                    'added_from_category_id': item.added_from_category_id,
                    'og_url_path': data.get('url_path'),
                }
                order_items.append(item_info)
            order_info = {
                'products': order_items,
                'items_count': item_qty,
                'billing_address': model_to_dict(order.billing_address),
                'shipping_address': model_to_dict(order.shipping_address),
                'customer_email': order.customer_email,
                'grand_total': order.grand_total,
                'tax_amount': order.tax_amount,
                'order_id': order.increment_id,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'discount_amount': order.discount_amount,
                'coupon_code': order.coupon_code,
                'shipping_amount': order.shipping_amount,
                'shipping_description': order.shipping_description,
                'subtotal': order.subtotal
            }
            rg_orders.append(order_info)
        return rg_orders


    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        # managed = True
        db_table = 'sales_flat_order'


class SalesFlatOrderAddress(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatOrder, models.DO_NOTHING, blank=True, null=True, related_name='+')
    customer_address_id = models.IntegerField(blank=True, null=True)
    quote_address_id = models.IntegerField(blank=True, null=True)
    region_id = models.IntegerField(blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    postcode = models.CharField(max_length=255, blank=True, null=True)
    lastname = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=255, blank=True, null=True)
    country_id = models.CharField(max_length=2, blank=True, null=True)
    firstname = models.CharField(max_length=255, blank=True, null=True)
    address_type = models.CharField(max_length=255, blank=True, null=True)
    prefix = models.CharField(max_length=255, blank=True, null=True)
    middlename = models.CharField(max_length=255, blank=True, null=True)
    suffix = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    vat_id = models.TextField(blank=True, null=True)
    vat_is_valid = models.SmallIntegerField(blank=True, null=True)
    vat_request_id = models.TextField(blank=True, null=True)
    vat_request_date = models.TextField(blank=True, null=True)
    vat_request_success = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_order_address'


class SalesFlatOrderGrid(models.Model):
    entity = models.OneToOneField(SalesFlatOrder, models.DO_NOTHING, primary_key=True, related_name='+')
    status = models.CharField(max_length=32, blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    store_name = models.CharField(max_length=255, blank=True, null=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_total_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    base_currency_code = models.CharField(max_length=3, blank=True, null=True)
    order_currency_code = models.CharField(max_length=255, blank=True, null=True)
    shipping_name = models.CharField(max_length=255, blank=True, null=True)
    billing_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    is_archieved = models.IntegerField()
    is_edit = models.IntegerField()
    edit_comments = models.TextField(blank=True, null=True)
    delivery_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_order_grid'


class SalesFlatOrderItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(SalesFlatOrder, models.CASCADE)
    parent_item_id = models.IntegerField(blank=True, null=True)
    quote_item_id = models.IntegerField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    product_id = models.IntegerField(blank=True, null=True)
    product_type = models.CharField(max_length=255, blank=True, null=True)
    product_options = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    is_virtual = models.SmallIntegerField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    applied_rule_ids = models.TextField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    free_shipping = models.SmallIntegerField()
    is_qty_decimal = models.SmallIntegerField(blank=True, null=True)
    no_discount = models.SmallIntegerField()
    qty_backordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_ordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty_shipped = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    base_price = models.DecimalField(max_digits=12, decimal_places=4)
    original_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_original_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total = models.DecimalField(max_digits=12, decimal_places=4)
    base_row_total = models.DecimalField(max_digits=12, decimal_places=4)
    row_invoiced = models.DecimalField(max_digits=12, decimal_places=4)
    base_row_invoiced = models.DecimalField(max_digits=12, decimal_places=4)
    row_weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_before_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_before_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    ext_order_item_id = models.CharField(max_length=255, blank=True, null=True)
    locked_do_invoice = models.SmallIntegerField(blank=True, null=True)
    locked_do_ship = models.SmallIntegerField(blank=True, null=True)
    price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    is_nominal = models.IntegerField()
    tax_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)
    gift_message_available = models.IntegerField(blank=True, null=True)
    base_weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_row_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_row_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied = models.TextField(blank=True, null=True)
    weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)
    added_from_category_id = models.IntegerField(blank=True, null=True)
    lithium_ion_type = models.CharField(max_length=20, blank=True, null=True)
    sku_location = models.CharField(max_length=10, blank=True, null=True)
    post_purchase_item = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_order_item'


class SalesFlatOrderPayment(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatOrder, models.CASCADE)
    # parent = models.ForeignKey(SalesFlatOrder, models.CASCADE, related_name='+')
    base_shipping_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_authorized = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_paid_online = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_refunded_online = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_authorized = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_ordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount_ordered = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_amount_canceled = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    quote_payment_id = models.IntegerField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    cc_exp_month = models.CharField(max_length=255, blank=True, null=True)
    cc_ss_start_year = models.CharField(max_length=255, blank=True, null=True)
    echeck_bank_name = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    cc_debug_request_body = models.CharField(max_length=255, blank=True, null=True)
    cc_secure_verify = models.CharField(max_length=255, blank=True, null=True)
    protection_eligibility = models.CharField(max_length=255, blank=True, null=True)
    cc_approval = models.CharField(max_length=255, blank=True, null=True)
    cc_last4 = models.CharField(max_length=255, blank=True, null=True)
    cc_status_description = models.CharField(max_length=255, blank=True, null=True)
    echeck_type = models.CharField(max_length=255, blank=True, null=True)
    cc_debug_response_serialized = models.CharField(max_length=255, blank=True, null=True)
    cc_ss_start_month = models.CharField(max_length=255, blank=True, null=True)
    echeck_account_type = models.CharField(max_length=255, blank=True, null=True)
    last_trans_id = models.CharField(max_length=255, blank=True, null=True)
    cc_cid_status = models.CharField(max_length=255, blank=True, null=True)
    cc_owner = models.CharField(max_length=255, blank=True, null=True)
    cc_type = models.CharField(max_length=255, blank=True, null=True)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    cc_exp_year = models.CharField(max_length=255, blank=True, null=True)
    cc_status = models.CharField(max_length=255, blank=True, null=True)
    echeck_routing_number = models.CharField(max_length=255, blank=True, null=True)
    account_status = models.CharField(max_length=255, blank=True, null=True)
    anet_trans_method = models.CharField(max_length=255, blank=True, null=True)
    cc_debug_response_body = models.CharField(max_length=255, blank=True, null=True)
    cc_ss_issue = models.CharField(max_length=255, blank=True, null=True)
    echeck_account_name = models.CharField(max_length=255, blank=True, null=True)
    cc_avs_status = models.CharField(max_length=255, blank=True, null=True)
    cc_number_enc = models.CharField(max_length=255, blank=True, null=True)
    cc_trans_id = models.CharField(max_length=255, blank=True, null=True)
    paybox_request_number = models.CharField(max_length=255, blank=True, null=True)
    address_status = models.CharField(max_length=255, blank=True, null=True)
    additional_information = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_order_payment'


class SalesFlatOrderStatusHistory(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatOrder, models.DO_NOTHING, related_name='+')
    is_customer_notified = models.IntegerField(blank=True, null=True)
    is_visible_on_front = models.SmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    entity_name = models.CharField(max_length=32, blank=True, null=True)
    admin_user_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_order_status_history'


class SalesFlatQuote(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    converted_at = models.DateTimeField(blank=True, null=True)
    is_active = models.SmallIntegerField(blank=True, null=True)
    is_virtual = models.SmallIntegerField(blank=True, null=True)
    is_multi_shipping = models.SmallIntegerField(blank=True, null=True)
    items_count = models.IntegerField(blank=True, null=True)
    items_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    orig_order_id = models.IntegerField(blank=True, null=True)
    store_to_base_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    store_to_quote_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_currency_code = models.CharField(max_length=255, blank=True, null=True)
    store_currency_code = models.CharField(max_length=255, blank=True, null=True)
    quote_currency_code = models.CharField(max_length=255, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    checkout_method = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.IntegerField(blank=True, null=True)
    customer_tax_class_id = models.IntegerField(blank=True, null=True)
    customer_group_id = models.IntegerField(blank=True, null=True)
    customer_email = models.CharField(max_length=255, blank=True, null=True)
    customer_prefix = models.CharField(max_length=40, blank=True, null=True)
    customer_firstname = models.CharField(max_length=255, blank=True, null=True)
    customer_middlename = models.CharField(max_length=40, blank=True, null=True)
    customer_lastname = models.CharField(max_length=255, blank=True, null=True)
    customer_suffix = models.CharField(max_length=40, blank=True, null=True)
    customer_dob = models.DateTimeField(blank=True, null=True)
    customer_note = models.CharField(max_length=255, blank=True, null=True)
    customer_note_notify = models.SmallIntegerField(blank=True, null=True)
    customer_is_guest = models.SmallIntegerField(blank=True, null=True)
    remote_ip = models.CharField(max_length=32, blank=True, null=True)
    applied_rule_ids = models.CharField(max_length=255, blank=True, null=True)
    reserved_order_id = models.CharField(max_length=64, blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True)
    coupon_code = models.CharField(max_length=255, blank=True, null=True)
    global_currency_code = models.CharField(max_length=255, blank=True, null=True)
    base_to_global_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_to_quote_rate = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    customer_taxvat = models.CharField(max_length=255, blank=True, null=True)
    customer_gender = models.CharField(max_length=255, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal_with_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_with_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    is_changed = models.IntegerField(blank=True, null=True)
    trigger_recollect = models.SmallIntegerField()
    ext_shipping_info = models.TextField(blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)
    is_persistent = models.SmallIntegerField(blank=True, null=True)
    is_place_order_clicked = models.SmallIntegerField(blank=True, null=True)
    is_mobile = models.SmallIntegerField(blank=True, null=True)
    ever_declined = models.SmallIntegerField(blank=True, null=True)
    is_fixed_width = models.SmallIntegerField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    use_reward_points = models.IntegerField(blank=True, null=True)
    reward_points_balance = models.IntegerField(blank=True, null=True)
    base_reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote'


class SalesFlatQuoteAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    quote = models.ForeignKey(SalesFlatQuote, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    customer_id = models.IntegerField(blank=True, null=True)
    save_in_address_book = models.SmallIntegerField(blank=True, null=True)
    customer_address_id = models.IntegerField(blank=True, null=True)
    address_type = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    prefix = models.CharField(max_length=40, blank=True, null=True)
    firstname = models.CharField(max_length=255, blank=True, null=True)
    middlename = models.CharField(max_length=40, blank=True, null=True)
    lastname = models.CharField(max_length=255, blank=True, null=True)
    suffix = models.CharField(max_length=40, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    street = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    region_id = models.IntegerField(blank=True, null=True)
    postcode = models.CharField(max_length=255, blank=True, null=True)
    country_id = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=255, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    same_as_billing = models.SmallIntegerField()
    free_shipping = models.SmallIntegerField()
    collect_shipping_rates = models.SmallIntegerField()
    shipping_method = models.CharField(max_length=255, blank=True, null=True)
    shipping_description = models.CharField(max_length=255, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal = models.DecimalField(max_digits=12, decimal_places=4)
    base_subtotal = models.DecimalField(max_digits=12, decimal_places=4)
    subtotal_with_discount = models.DecimalField(max_digits=12, decimal_places=4)
    base_subtotal_with_discount = models.DecimalField(max_digits=12, decimal_places=4)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4)
    base_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4)
    shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    grand_total = models.DecimalField(max_digits=12, decimal_places=4)
    base_grand_total = models.DecimalField(max_digits=12, decimal_places=4)
    customer_notes = models.TextField(blank=True, null=True)
    applied_taxes = models.TextField(blank=True, null=True)
    discount_description = models.CharField(max_length=255, blank=True, null=True)
    shipping_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    subtotal_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_subtotal_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_hidden_tax_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_shipping_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    vat_id = models.TextField(blank=True, null=True)
    vat_is_valid = models.SmallIntegerField(blank=True, null=True)
    vat_request_id = models.TextField(blank=True, null=True)
    vat_request_date = models.TextField(blank=True, null=True)
    vat_request_success = models.SmallIntegerField(blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)
    reward_points_balance = models.IntegerField(blank=True, null=True)
    base_reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    reward_currency_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_address'


class SalesFlatQuoteAddressItem(models.Model):
    address_item_id = models.AutoField(primary_key=True)
    parent_item = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, related_name='+')
    quote_address = models.ForeignKey(SalesFlatQuoteAddress, models.DO_NOTHING, related_name='+')
    quote_item = models.ForeignKey('SalesFlatQuoteItem', models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    applied_rule_ids = models.TextField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total = models.DecimalField(max_digits=12, decimal_places=4)
    base_row_total = models.DecimalField(max_digits=12, decimal_places=4)
    row_total_with_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    super_product_id = models.IntegerField(blank=True, null=True)
    parent_product_id = models.IntegerField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    free_shipping = models.IntegerField(blank=True, null=True)
    is_qty_decimal = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    no_discount = models.IntegerField(blank=True, null=True)
    tax_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_address_item'


class SalesFlatQuoteItem(models.Model):
    item_id = models.AutoField(primary_key=True)
    quote = models.ForeignKey(SalesFlatQuote, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    parent_item = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, related_name='+')
    is_virtual = models.SmallIntegerField(blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    applied_rule_ids = models.TextField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    free_shipping = models.SmallIntegerField()
    is_qty_decimal = models.SmallIntegerField(blank=True, null=True)
    no_discount = models.SmallIntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    base_price = models.DecimalField(max_digits=12, decimal_places=4)
    custom_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_discount_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total = models.DecimalField(max_digits=12, decimal_places=4)
    base_row_total = models.DecimalField(max_digits=12, decimal_places=4)
    row_total_with_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    product_type = models.CharField(max_length=255, blank=True, null=True)
    base_tax_before_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_before_discount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    original_custom_price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    redirect_url = models.CharField(max_length=255, blank=True, null=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_price_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_row_total_incl_tax = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_hidden_tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    gift_message_id = models.IntegerField(blank=True, null=True)
    weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_row_disposition = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied = models.TextField(blank=True, null=True)
    weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weee_tax_applied_row_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    base_weee_tax_applied_row_amnt = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    brand_model = models.CharField(max_length=255, blank=True, null=True)
    added_from_category_id = models.IntegerField(blank=True, null=True)
    lithium_ion_type = models.CharField(max_length=20, blank=True, null=True)
    sku_location = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_item'


class SalesFlatQuoteItemOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    item = models.ForeignKey(SalesFlatQuoteItem, models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    code = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_item_option'


class SalesFlatQuotePayment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    quote = models.ForeignKey(SalesFlatQuote, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    method = models.CharField(max_length=255, blank=True, null=True)
    cc_type = models.CharField(max_length=255, blank=True, null=True)
    cc_number_enc = models.CharField(max_length=255, blank=True, null=True)
    cc_last4 = models.CharField(max_length=255, blank=True, null=True)
    cc_cid_enc = models.CharField(max_length=255, blank=True, null=True)
    cc_owner = models.CharField(max_length=255, blank=True, null=True)
    cc_exp_month = models.SmallIntegerField(blank=True, null=True)
    cc_exp_year = models.SmallIntegerField(blank=True, null=True)
    cc_ss_owner = models.CharField(max_length=255, blank=True, null=True)
    cc_ss_start_month = models.SmallIntegerField(blank=True, null=True)
    cc_ss_start_year = models.SmallIntegerField(blank=True, null=True)
    po_number = models.CharField(max_length=255, blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    cc_ss_issue = models.CharField(max_length=255, blank=True, null=True)
    additional_information = models.TextField(blank=True, null=True)
    paypal_payer_id = models.CharField(max_length=255, blank=True, null=True)
    paypal_payer_status = models.CharField(max_length=255, blank=True, null=True)
    paypal_correlation_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_payment'


class SalesFlatQuoteShippingRate(models.Model):
    rate_id = models.AutoField(primary_key=True)
    address = models.ForeignKey(SalesFlatQuoteAddress, models.DO_NOTHING, related_name='+')
    created_at = TimestampField()
    updated_at = TimestampField()
    carrier = models.CharField(max_length=255, blank=True, null=True)
    carrier_title = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    method_description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    error_message = models.TextField(blank=True, null=True)
    method_title = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_quote_shipping_rate'


class SalesFlatShipment(models.Model):
    entity_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    total_weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    email_sent = models.SmallIntegerField(blank=True, null=True)
    order = models.ForeignKey(SalesFlatOrder, models.DO_NOTHING, related_name='+')
    customer_id = models.IntegerField(blank=True, null=True)
    shipping_address_id = models.IntegerField(blank=True, null=True)
    billing_address_id = models.IntegerField(blank=True, null=True)
    shipment_status = models.IntegerField(blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    packages = models.TextField(blank=True, null=True)
    shipping_label = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_shipment'


class SalesFlatShipmentComment(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatShipment, models.DO_NOTHING, related_name='+')
    is_customer_notified = models.IntegerField(blank=True, null=True)
    is_visible_on_front = models.SmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    admin_user_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_shipment_comment'


class SalesFlatShipmentGrid(models.Model):
    entity = models.OneToOneField(SalesFlatShipment, models.DO_NOTHING, primary_key=True, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    total_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_id = models.IntegerField()
    shipment_status = models.IntegerField(blank=True, null=True)
    increment_id = models.CharField(unique=True, max_length=50, blank=True, null=True)
    order_increment_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    order_created_at = TimestampField(blank=True, null=True)
    shipping_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_shipment_grid'


class SalesFlatShipmentItem(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatShipment, models.DO_NOTHING, related_name='+')
    row_total = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    order_item_id = models.IntegerField(blank=True, null=True)
    additional_data = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_shipment_item'


class SalesFlatShipmentTrack(models.Model):
    entity_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey(SalesFlatShipment, models.DO_NOTHING, related_name='+')
    weight = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    order_id = models.IntegerField()
    track_number = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    carrier_code = models.CharField(max_length=32, blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_flat_shipment_track'


class SalesInvoicedAggregated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    orders_count = models.IntegerField()
    orders_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced_not_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_invoiced_aggregated'
        unique_together = (('period', 'store', 'order_status'),)


class SalesInvoicedAggregatedOrder(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50)
    orders_count = models.IntegerField()
    orders_invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    invoiced_not_captured = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_invoiced_aggregated_order'
        unique_together = (('period', 'store', 'order_status'),)


class SalesOrderAggregatedCreated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50)
    orders_count = models.IntegerField()
    total_qty_ordered = models.DecimalField(max_digits=12, decimal_places=4)
    total_qty_invoiced = models.DecimalField(max_digits=12, decimal_places=4)
    total_income_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_revenue_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_profit_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_invoiced_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_canceled_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_paid_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_refunded_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_tax_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_tax_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_shipping_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_discount_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_aggregated_created'
        unique_together = (('period', 'store', 'order_status'),)


class SalesOrderAggregatedUpdated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50)
    orders_count = models.IntegerField()
    total_qty_ordered = models.DecimalField(max_digits=12, decimal_places=4)
    total_qty_invoiced = models.DecimalField(max_digits=12, decimal_places=4)
    total_income_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_revenue_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_profit_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_invoiced_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_canceled_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_paid_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_refunded_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_tax_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_tax_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_shipping_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_shipping_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)
    total_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    total_discount_amount_actual = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_aggregated_updated'
        unique_together = (('period', 'store', 'order_status'),)


class SalesOrderStatus(models.Model):
    status = models.CharField(primary_key=True, max_length=32)
    label = models.CharField(max_length=128)
    colour = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_status'


class SalesOrderStatusLabel(models.Model):
    status = models.ForeignKey(SalesOrderStatus, models.DO_NOTHING, db_column='status', related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    label = models.CharField(max_length=128)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_status_label'
        unique_together = (('status', 'store'),)


class SalesOrderStatusState(models.Model):
    status = models.ForeignKey(SalesOrderStatus, models.DO_NOTHING, db_column='status', related_name='+')
    state = models.CharField(max_length=32)
    is_default = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_status_state'
        unique_together = (('status', 'state'),)


class SalesOrderTax(models.Model):
    tax_id = models.AutoField(primary_key=True)
    order_id = models.IntegerField()
    code = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    percent = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    priority = models.IntegerField()
    position = models.IntegerField()
    base_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    process = models.SmallIntegerField()
    base_real_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    hidden = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_tax'


class SalesOrderTaxItem(models.Model):
    tax_item_id = models.AutoField(primary_key=True)
    tax = models.ForeignKey(SalesOrderTax, models.DO_NOTHING, related_name='+')
    item = models.ForeignKey(SalesFlatOrderItem, models.DO_NOTHING, related_name='+')
    tax_percent = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_order_tax_item'
        unique_together = (('tax', 'item'),)


class SalesPaymentTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, related_name='+')
    order = models.ForeignKey(SalesFlatOrder, models.DO_NOTHING, related_name='+')
    payment = models.ForeignKey(SalesFlatOrderPayment, models.DO_NOTHING, related_name='+')
    txn_id = models.CharField(max_length=100, blank=True, null=True)
    parent_txn_id = models.CharField(max_length=100, blank=True, null=True)
    txn_type = models.CharField(max_length=15, blank=True, null=True)
    is_closed = models.SmallIntegerField()
    additional_information = models.TextField(blank=True, null=True)
    created_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_payment_transaction'
        unique_together = (('order', 'payment', 'txn_id'),)


class SalesRecurringProfile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    state = models.CharField(max_length=20)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    method_code = models.CharField(max_length=32)
    created_at = TimestampField()
    updated_at = TimestampField(blank=True, null=True)
    reference_id = models.CharField(max_length=32, blank=True, null=True)
    subscriber_name = models.CharField(max_length=150, blank=True, null=True)
    start_datetime = models.DateTimeField()
    internal_reference_id = models.CharField(unique=True, max_length=42)
    schedule_description = models.CharField(max_length=255)
    suspension_threshold = models.SmallIntegerField(blank=True, null=True)
    bill_failed_later = models.SmallIntegerField()
    period_unit = models.CharField(max_length=20)
    period_frequency = models.SmallIntegerField(blank=True, null=True)
    period_max_cycles = models.SmallIntegerField(blank=True, null=True)
    billing_amount = models.DecimalField(max_digits=12, decimal_places=4)
    trial_period_unit = models.CharField(max_length=20, blank=True, null=True)
    trial_period_frequency = models.SmallIntegerField(blank=True, null=True)
    trial_period_max_cycles = models.SmallIntegerField(blank=True, null=True)
    trial_billing_amount = models.TextField(blank=True, null=True)
    currency_code = models.CharField(max_length=3)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    init_amount = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    init_may_fail = models.SmallIntegerField()
    order_info = models.TextField()
    order_item_info = models.TextField()
    billing_address_info = models.TextField()
    shipping_address_info = models.TextField(blank=True, null=True)
    profile_vendor_info = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_recurring_profile'


class SalesRecurringProfileOrder(models.Model):
    link_id = models.AutoField(primary_key=True)
    profile = models.ForeignKey(SalesRecurringProfile, models.DO_NOTHING, related_name='+')
    order = models.ForeignKey(SalesFlatOrder, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_recurring_profile_order'
        unique_together = (('profile', 'order'),)


class SalesRefundedAggregated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50)
    orders_count = models.IntegerField()
    refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    online_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    offline_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_refunded_aggregated'
        unique_together = (('period', 'store', 'order_status'),)


class SalesRefundedAggregatedOrder(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    orders_count = models.IntegerField()
    refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    online_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    offline_refunded = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_refunded_aggregated_order'
        unique_together = (('period', 'store', 'order_status'),)


class SalesShippingAggregated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    shipping_description = models.CharField(max_length=255, blank=True, null=True)
    orders_count = models.IntegerField()
    total_shipping = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_shipping_actual = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_shipping_aggregated'
        unique_together = (('period', 'store', 'order_status', 'shipping_description'),)


class SalesShippingAggregatedOrder(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    order_status = models.CharField(max_length=50, blank=True, null=True)
    shipping_description = models.CharField(max_length=255, blank=True, null=True)
    orders_count = models.IntegerField()
    total_shipping = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_shipping_actual = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sales_shipping_aggregated_order'
        unique_together = (('period', 'store', 'order_status', 'shipping_description'),)


class Salesrule(models.Model):
    rule_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    uses_per_customer = models.IntegerField()
    is_active = models.SmallIntegerField()
    conditions_serialized = models.TextField(blank=True, null=True)
    actions_serialized = models.TextField(blank=True, null=True)
    stop_rules_processing = models.SmallIntegerField()
    is_advanced = models.SmallIntegerField()
    product_ids = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField()
    simple_action = models.CharField(max_length=32, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    max_discount_amount = models.DecimalField(max_digits=12, decimal_places=4)
    discount_qty = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    discount_step = models.IntegerField()
    simple_free_shipping = models.SmallIntegerField()
    apply_to_shipping = models.SmallIntegerField()
    times_used = models.IntegerField()
    is_rss = models.SmallIntegerField()
    coupon_type = models.SmallIntegerField()
    use_auto_generation = models.SmallIntegerField()
    uses_per_coupon = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule'


class SalesruleCoupon(models.Model):
    coupon_id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    code = models.CharField(unique=True, max_length=255, blank=True, null=True)
    usage_limit = models.IntegerField(blank=True, null=True)
    usage_per_customer = models.IntegerField(blank=True, null=True)
    times_used = models.IntegerField()
    expiration_date = models.DateTimeField(blank=True, null=True)
    is_primary = models.SmallIntegerField(blank=True, null=True)
    created_at = TimestampField()
    type = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_coupon'
        unique_together = (('rule', 'is_primary'),)


class SalesruleCouponUsage(models.Model):
    coupon = models.ForeignKey(SalesruleCoupon, models.DO_NOTHING, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    times_used = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_coupon_usage'
        unique_together = (('coupon', 'customer'),)


class SalesruleCustomer(models.Model):
    rule_customer_id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    times_used = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_customer'


class SalesruleCustomerGroup(models.Model):
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey(CustomerGroup, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_customer_group'
        unique_together = (('rule', 'customer_group'),)


class SalesruleLabel(models.Model):
    label_id = models.AutoField(primary_key=True)
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    label = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_label'
        unique_together = (('rule', 'store'),)


class SalesruleProductAttribute(models.Model):
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey(CustomerGroup, models.DO_NOTHING, related_name='+')
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_product_attribute'
        unique_together = (('rule', 'website', 'customer_group', 'attribute'),)


class SalesruleWebsite(models.Model):
    rule = models.ForeignKey(Salesrule, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'salesrule_website'
        unique_together = (('rule', 'website'),)


class SendfriendLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    ip = models.BigIntegerField()
    time = models.IntegerField()
    website_id = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sendfriend_log'


class ShippingStoreIdStoreName(models.Model):
    store_id = models.IntegerField()
    store_name = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'shipping_store_id_store_name'


class ShippingTablerate(models.Model):
    id = models.AutoField(primary_key=True, db_column='pk')
    website_id = models.IntegerField()
    dest_country_id = models.CharField(max_length=4)
    dest_region_id = models.IntegerField()
    dest_zip = models.CharField(max_length=10)
    condition_name = models.CharField(max_length=20)
    condition_value = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    cost = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'shipping_tablerate'
        unique_together = (('website_id', 'dest_country_id', 'dest_region_id', 'dest_zip', 'condition_name', 'condition_value'),)


class Sitemap(models.Model):
    sitemap_id = models.AutoField(primary_key=True)
    sitemap_type = models.CharField(max_length=32, blank=True, null=True)
    sitemap_filename = models.CharField(max_length=32, blank=True, null=True)
    sitemap_path = models.CharField(max_length=255, blank=True, null=True)
    sitemap_time = models.DateTimeField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'sitemap'


class SmartwaveBlog(models.Model):
    post_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    post_content = models.TextField()
    status = models.SmallIntegerField()
    image = models.CharField(max_length=255, blank=True, null=True)
    banner = models.CharField(max_length=255, blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    identifier = models.CharField(unique=True, max_length=255)
    user = models.CharField(max_length=255)
    update_user = models.CharField(max_length=255)
    meta_keywords = models.TextField()
    meta_description = models.TextField()
    comments = models.IntegerField()
    tags = models.TextField()
    short_content = models.TextField()
    banner_content = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog'


class SmartwaveBlogCat(models.Model):
    cat_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)
    sort_order = models.IntegerField()
    meta_keywords = models.TextField()
    meta_description = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_cat'


class SmartwaveBlogCatStore(models.Model):
    cat_id = models.SmallIntegerField(blank=True, null=True)
    store_id = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_cat_store'


class SmartwaveBlogComment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    post_id = models.SmallIntegerField()
    comment = models.TextField()
    status = models.SmallIntegerField()
    created_time = models.DateTimeField(blank=True, null=True)
    user = models.CharField(max_length=255)
    email = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_comment'


class SmartwaveBlogPostCat(models.Model):
    cat_id = models.SmallIntegerField(blank=True, null=True)
    post_id = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_post_cat'


class SmartwaveBlogStore(models.Model):
    post_id = models.SmallIntegerField(blank=True, null=True)
    store_id = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_store'


class SmartwaveBlogTags(models.Model):
    tag = models.CharField(max_length=255)
    tag_count = models.IntegerField()
    store_id = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'smartwave_blog_tags'


class Tag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.SmallIntegerField()
    first_customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    first_store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tag'


class TagProperties(models.Model):
    tag = models.ForeignKey(Tag, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    base_popularity = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tag_properties'
        unique_together = (('tag', 'store'),)


class TagRelation(models.Model):
    tag_relation_id = models.AutoField(primary_key=True)
    tag = models.ForeignKey(Tag, models.DO_NOTHING, related_name='+')
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, blank=True, null=True, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    active = models.SmallIntegerField()
    created_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tag_relation'
        unique_together = (('tag', 'customer', 'product', 'store'),)


class TagSummary(models.Model):
    tag = models.ForeignKey(Tag, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    customers = models.IntegerField()
    products = models.IntegerField()
    uses = models.IntegerField()
    historical_uses = models.IntegerField()
    popularity = models.IntegerField()
    base_popularity = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tag_summary'
        unique_together = (('tag', 'store'),)


class TaxCalculation(models.Model):
    tax_calculation_id = models.AutoField(primary_key=True)
    tax_calculation_rate = models.ForeignKey('TaxCalculationRate', models.DO_NOTHING, related_name='+')
    tax_calculation_rule = models.ForeignKey('TaxCalculationRule', models.DO_NOTHING, related_name='+')
    customer_tax_class = models.ForeignKey('TaxClass', models.DO_NOTHING, related_name='+')
    product_tax_class = models.ForeignKey('TaxClass', models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_calculation'


class TaxCalculationRate(models.Model):
    tax_calculation_rate_id = models.AutoField(primary_key=True)
    tax_country_id = models.CharField(max_length=2)
    tax_region_id = models.IntegerField()
    tax_postcode = models.CharField(max_length=21, blank=True, null=True)
    code = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=12, decimal_places=4)
    zip_is_range = models.SmallIntegerField(blank=True, null=True)
    zip_from = models.IntegerField(blank=True, null=True)
    zip_to = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_calculation_rate'


class TaxCalculationRateTitle(models.Model):
    tax_calculation_rate_title_id = models.AutoField(primary_key=True)
    tax_calculation_rate = models.ForeignKey(TaxCalculationRate, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')
    value = models.CharField(max_length=255)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_calculation_rate_title'


class TaxCalculationRule(models.Model):
    tax_calculation_rule_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=255)
    priority = models.IntegerField()
    position = models.IntegerField()
    calculate_subtotal = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_calculation_rule'


class TaxClass(models.Model):
    class_id = models.SmallIntegerField(primary_key=True)
    class_name = models.CharField(max_length=255)
    class_type = models.CharField(max_length=8)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_class'


class TaxOrderAggregatedCreated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    code = models.CharField(max_length=255)
    order_status = models.CharField(max_length=50)
    percent = models.FloatField(blank=True, null=True)
    orders_count = models.IntegerField()
    tax_base_amount_sum = models.FloatField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_order_aggregated_created'
        unique_together = (('period', 'store', 'code', 'percent', 'order_status'),)


class TaxOrderAggregatedUpdated(models.Model):
    period = models.DateField(blank=True, null=True)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    code = models.CharField(max_length=255)
    order_status = models.CharField(max_length=50)
    percent = models.FloatField(blank=True, null=True)
    orders_count = models.IntegerField()
    tax_base_amount_sum = models.FloatField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'tax_order_aggregated_updated'
        unique_together = (('period', 'store', 'code', 'percent', 'order_status'),)


class WeAbandcartSent(models.Model):
    quote_id = models.IntegerField()
    created = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'we_abandcart_sent'


class WeReward(models.Model):
    reward_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(CustomerEntity, models.DO_NOTHING, related_name='+')
    website_id = models.SmallIntegerField(blank=True, null=True)
    points_balance = models.IntegerField()
    website_currency_code = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'we_reward'
        unique_together = (('customer', 'website_id'),)


class WeRewardHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    reward = models.ForeignKey(WeReward, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    action = models.SmallIntegerField()
    entity = models.IntegerField(blank=True, null=True)
    points_balance = models.IntegerField()
    points_delta = models.IntegerField()
    points_used = models.IntegerField()
    points_voided = models.IntegerField()
    currency_amount = models.DecimalField(max_digits=12, decimal_places=4)
    currency_delta = models.DecimalField(max_digits=12, decimal_places=4)
    base_currency_code = models.CharField(max_length=5)
    additional_data = models.TextField()
    comment = models.TextField(blank=True, null=True)
    created_at = TimestampField()
    expired_at_static = models.DateTimeField(blank=True, null=True)
    expired_at_dynamic = models.DateTimeField(blank=True, null=True)
    is_expired = models.SmallIntegerField()
    is_duplicate_of = models.IntegerField(blank=True, null=True)
    notification_sent = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'we_reward_history'


class WeRewardRate(models.Model):
    rate_id = models.AutoField(primary_key=True)
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    customer_group_id = models.SmallIntegerField()
    direction = models.SmallIntegerField()
    points = models.IntegerField()
    currency_amount = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'we_reward_rate'
        unique_together = (('website', 'customer_group_id', 'direction'),)


class WeRewardSalesrule(models.Model):
    rule = models.OneToOneField(Salesrule, models.DO_NOTHING, unique=True, related_name='+')
    points_delta = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'we_reward_salesrule'


class WeeeDiscount(models.Model):
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    customer_group = models.ForeignKey(CustomerGroup, models.DO_NOTHING, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'weee_discount'


class WeeeTax(models.Model):
    value_id = models.AutoField(primary_key=True)
    website = models.ForeignKey(CoreWebsite, models.DO_NOTHING, related_name='+')
    entity = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    country = models.ForeignKey(DirectoryCountry, models.DO_NOTHING, db_column='country', blank=True, null=True, related_name='+')
    value = models.DecimalField(max_digits=12, decimal_places=4)
    state = models.CharField(max_length=255)
    attribute = models.ForeignKey(EavAttribute, models.DO_NOTHING, related_name='+')
    entity_type_id = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'weee_tax'


class Widget(models.Model):
    widget_id = models.AutoField(primary_key=True)
    widget_code = models.CharField(max_length=255, blank=True, null=True)
    widget_type = models.CharField(max_length=255, blank=True, null=True)
    parameters = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'widget'


class WidgetInstance(models.Model):
    instance_id = models.AutoField(primary_key=True)
    instance_type = models.CharField(max_length=255, blank=True, null=True)
    package_theme = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    store_ids = models.CharField(max_length=255)
    widget_parameters = models.TextField(blank=True, null=True)
    sort_order = models.SmallIntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'widget_instance'


class WidgetInstancePage(models.Model):
    page_id = models.AutoField(primary_key=True)
    instance = models.ForeignKey(WidgetInstance, models.DO_NOTHING, related_name='+')
    page_group = models.CharField(max_length=25, blank=True, null=True)
    layout_handle = models.CharField(max_length=255, blank=True, null=True)
    block_reference = models.CharField(max_length=255, blank=True, null=True)
    page_for = models.CharField(max_length=25, blank=True, null=True)
    entities = models.TextField(blank=True, null=True)
    page_template = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'widget_instance_page'


class WidgetInstancePageLayout(models.Model):
    page = models.ForeignKey(WidgetInstancePage, models.DO_NOTHING, related_name='+')
    layout_update = models.ForeignKey(CoreLayoutUpdate, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'widget_instance_page_layout'
        unique_together = (('layout_update', 'page'),)


class Wishlist(models.Model):
    wishlist_id = models.AutoField(primary_key=True)
    customer = models.OneToOneField(CustomerEntity, models.DO_NOTHING, unique=True, related_name='+')
    shared = models.SmallIntegerField()
    sharing_code = models.CharField(max_length=32, blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'wishlist'


class WishlistItem(models.Model):
    wishlist_item_id = models.AutoField(primary_key=True)
    wishlist = models.ForeignKey(Wishlist, models.DO_NOTHING, related_name='+')
    product = models.ForeignKey(CatalogProductEntity, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    added_at = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    qty = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'wishlist_item'


class WishlistItemOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    wishlist_item = models.ForeignKey(WishlistItem, models.DO_NOTHING, related_name='+')
    product_id = models.IntegerField()
    code = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'wishlist_item_option'


class XmlconnectApplication(models.Model):
    application_id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(unique=True, max_length=32)
    type = models.CharField(max_length=32)
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, blank=True, null=True, related_name='+')
    active_from = models.DateField(blank=True, null=True)
    active_to = models.DateField(blank=True, null=True)
    updated_at = TimestampField(blank=True, null=True)
    status = models.SmallIntegerField()
    browsing_mode = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_application'


class XmlconnectConfigData(models.Model):
    application = models.ForeignKey(XmlconnectApplication, models.DO_NOTHING, related_name='+')
    category = models.CharField(max_length=60)
    path = models.CharField(max_length=250)
    value = models.TextField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_config_data'
        unique_together = (('application', 'category', 'path'),)


class XmlconnectHistory(models.Model):
    history_id = models.AutoField(primary_key=True)
    application = models.ForeignKey(XmlconnectApplication, models.DO_NOTHING, related_name='+')
    created_at = TimestampField(blank=True, null=True)
    store_id = models.SmallIntegerField(blank=True, null=True)
    params = models.TextField(blank=True, null=True)
    title = models.CharField(max_length=200)
    activation_key = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_history'


class XmlconnectImages(models.Model):
    image_id = models.AutoField(primary_key=True)
    application = models.ForeignKey(XmlconnectApplication, models.DO_NOTHING, related_name='+')
    image_file = models.CharField(max_length=255)
    image_type = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_images'


class XmlconnectNotificationTemplate(models.Model):
    template_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    push_title = models.CharField(max_length=140)
    message_title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = TimestampField(blank=True, null=True)
    modified_at = models.DateTimeField(blank=True, null=True)
    application = models.ForeignKey(XmlconnectApplication, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_notification_template'


class XmlconnectQueue(models.Model):
    queue_id = models.AutoField(primary_key=True)
    create_time = models.DateTimeField(blank=True, null=True)
    exec_time = models.DateTimeField(blank=True, null=True)
    template = models.ForeignKey(XmlconnectNotificationTemplate, models.DO_NOTHING, related_name='+')
    push_title = models.CharField(max_length=140)
    message_title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    status = models.SmallIntegerField()
    type = models.CharField(max_length=12)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'xmlconnect_queue'


class ZeonManufacturer(models.Model):
    id = models.AutoField(primary_key=True, db_column='manufacturer_id')
    manufacturer = models.ForeignKey(EavAttributeOption, models.DO_NOTHING, db_column='manufacturer', related_name='+')
    status = models.SmallIntegerField()
    is_display_home = models.SmallIntegerField()
    identifier = models.CharField(max_length=255, blank=True, null=True)
    manufacturer_logo = models.CharField(max_length=255, blank=True, null=True)
    manufacturer_banner = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    sort_order = models.SmallIntegerField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'zeon_manufacturer'


class ZeonManufacturerStore(models.Model):
    manufacturer = models.ForeignKey(ZeonManufacturer, models.DO_NOTHING, related_name='+')
    store = models.ForeignKey(CoreStore, models.DO_NOTHING, related_name='+')

    class Meta:
        managed = getattr(settings, 'IS_TEST', False)
        db_table = 'zeon_manufacturer_store'
        unique_together = (('manufacturer', 'store'),)

from modjento.managers import EavAttributeManager, EavOptionManager
