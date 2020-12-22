from django.contrib import admin
from django.forms import ModelForm
from models import *
# Register your models here.
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin


# class SalesDirectorAdmin(admin.ModelAdmin):
#     list_display = ('channel', 'endpoint_name', 'inactivity_threshold', 'funnel_step', 'lifecycle_messaging_stage')
#     search_fields = ('channel', 'endpoint_name', 'inactivity_threshold', 'funnel_step', 'lifecycle_messaging_stage')


class FilterChildAdmin(PolymorphicChildModelAdmin):
    """
    Common base class for Filter's children's Admins
    """
    base_model = Filter


class AbandonedCartCandidateFilterAdmin(FilterChildAdmin):
    pass


class HasRIIDFilterAdmin(FilterChildAdmin):
    base_model = HasRIIDFilter


class HasRIIDFilterInline(admin.StackedInline):
    model = HasRIIDFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return super(HasRIIDFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


class PDPBrowseAbandonInfoFilterAdmin(FilterChildAdmin):
    base_model = PDPBrowseAbandonInfoFilter


class PDPBrowseAbandonInfoFilterInline(admin.StackedInline):
    model = PDPBrowseAbandonInfoFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0


class NoPDPBrowseAbandonInfoFilterAdmin(FilterChildAdmin):
    base_model = NoPDPBrowseAbandonInfoFilter


class NoPDPBrowseAbandonInfoFilterInline(admin.StackedInline):
    model = NoPDPBrowseAbandonInfoFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0


class StrandsProductRecsFilterAdmin(FilterChildAdmin):
    base_model = StrandsProductRecsFilter


class StrandsProductRecsFilterInline(admin.StackedInline):
    model = StrandsProductRecsFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return super(StrandsProductRecsFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


class SearchAbandonFilterAdmin(FilterChildAdmin):
    base_model = SearchAbandonFilter


class SearchAbandonFilterInline(admin.StackedInline):
    model = SearchAbandonFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return super(SearchAbandonFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


class ActiveCartInfoFilterAdmin(FilterChildAdmin):
    base_model = ActiveCartInfoFilter


class InactivityFilterAdmin(FilterChildAdmin):
    base_model = InactivityFilter


class ActiveCartInfoFilterInline(admin.StackedInline):
    model = ActiveCartInfoFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return super(ActiveCartInfoFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


class PolymorphicModelForm(ModelForm):
    def __new__(cls, *args, **kwargs):
        # we have the instance (param) that we can use to pick the right form...
        # we could to it a bit nicer by creating a delegate and proxying everything
        # class ModelFormWithMeta(ModelForm):
        #     _meta = cls._meta
        #     __dict__ = cls.__dict__

        print "#### Here we could do some magic if defaults has values for the generic FK"
        print "   cls = %s , args = %s, kwargs = %s, cls.__dict__ = %s" % (cls, args, kwargs, cls.__dict__)
        # return ModelFormWithMeta(*args, **kwargs)
        AbandonedCartCandidateFilterInline.form._meta = cls._meta
        return AbandonedCartCandidateFilterInline.form(*args, **kwargs)


class FilterInline(admin.StackedInline):
    model = Filter # This is ignored
    form = PolymorphicModelForm
    # readonly_fields = ['filter_ptr']


class AbandonedCartCandidateFilterInline(admin.StackedInline):
    model = AbandonedCartCandidateFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    # @staticmethod
    # def form(**defaults):
    #     print "#### Here we could do some magic if defaults has values for the generic FK"
    #     return ModelForm(**defaults)

    def get_formset(self, request, obj=None, **kwargs):
        return super(AbandonedCartCandidateFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


class InactivityFilterInline(admin.StackedInline):
    model = InactivityFilter
    readonly_fields = ['filter_ptr']
    min_num = 0
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        return super(InactivityFilterInline, self).get_formset(request, obj, can_order=True, **kwargs)


@admin.register(Filter)
class FilterAdmin(PolymorphicParentModelAdmin):
    base_model = Filter
    polymorphic_list = True
    list_display = ('id', 'filter_type', 'campaign', 'order')
    list_display_links = ('id', 'filter_type')
    list_filter = ('campaign',)

    # TODO: implement get_child_models instead to make Filter discovery automatic
    child_models = (
        (ActiveCartInfoFilter, ActiveCartInfoFilterAdmin),
        (AbandonedCartCandidateFilter, AbandonedCartCandidateFilterAdmin),
        (HasRIIDFilter, HasRIIDFilterAdmin),
        (InactivityFilter, InactivityFilterAdmin),
        (PDPBrowseAbandonInfoFilter, PDPBrowseAbandonInfoFilterAdmin),
        (StrandsProductRecsFilter, StrandsProductRecsFilterAdmin),
        (NoPDPBrowseAbandonInfoFilter, NoPDPBrowseAbandonInfoFilterAdmin),
        (SearchAbandonFilter, SearchAbandonFilterAdmin),
    )

    def filter_type(self, obj):
        return obj.__class__.__name__


class DjangoEmailBackendSenderAdmin(PolymorphicChildModelAdmin):
    base_model = DjangoEmailBackendSender


class ResponsysAdmin(PolymorphicChildModelAdmin):
    base_model = Responsys

class ResponsysEventAdmin(PolymorphicChildModelAdmin):
    base_model = ResponsysEvent

class MandrillAdmin(PolymorphicChildModelAdmin):
    base_model = Mandrill


@admin.register(Sender)
class SenderAdmin(PolymorphicParentModelAdmin):
    base_model = Sender

    child_models = (
        (DjangoEmailBackendSender, DjangoEmailBackendSenderAdmin),
        (Responsys, ResponsysAdmin),
        (Mandrill, MandrillAdmin),
        (ResponsysEvent, ResponsysEventAdmin),
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    # inlines = [FilterInline]
    inlines = [ActiveCartInfoFilterInline,
               HasRIIDFilterInline,
               InactivityFilterInline,
               PDPBrowseAbandonInfoFilterInline,
               StrandsProductRecsFilterInline,
               NoPDPBrowseAbandonInfoFilterInline,
               SearchAbandonFilterInline]


@admin.register(SenderLog)
class SenderLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'sender', 'response', 'send_datetime')


@admin.register(OrderConfirmationSendLog)
class OrderConfirmationSendLogAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'response', 'order_updated_at', 'base_grand_total')


@admin.register(ProductReviewEntity)
class ProductReviewEntityAdmin(admin.ModelAdmin):
    list_display = ('email', 'order_id', 'product_id',
                    'rating', 'price_paid', 'review_title',
                    'review_content', 'nickname', 'created_dt')

# admin.site.register(SalesDirector, SalesDirectorAdmin)
# admin.site.register(Filter, FilterAdmin)
# admin.site.register(Sender, SenderAdmin)

