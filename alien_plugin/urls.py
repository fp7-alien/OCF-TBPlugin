
from django.conf.urls.defaults import *

urlpatterns = patterns('alien_plugin.controller.aggregate',
    url(r'^aggregate/create/$', 'aggregate_crud', name='alien_plugin_aggregate_create'),
    url(r'^aggregate/(?P<agg_id>\d+)/edit/$', 'aggregate_crud', name='alien_plugin_aggregate_edit'),
)

urlpatterns = urlpatterns + patterns('alien_plugin.controller.GUIdispatcher',
    url(r'^create/(?P<slice_id>\d+)/(?P<agg_id>\d+)/$', 'create_resource', name='alien_plugin_resource_create'),
    url(r'^edit/(?P<slice_id>\d+)/(?P<agg_id>\d+)/(?P<resource_id>\d+)/$', 'resource_crud', name='alien_plugin_resource_edit'),
    url(r'^manage/(?P<resource_id>\d+)/(?P<action_type>\w+)/$', 'manage_resource', name='alien_plugin_resource_manage'),
    url(r'^crud/(?P<slice_id>\d+)/(?P<agg_id>\d+)/$', 'resource_crud', name='alien_plugin_resource_crud'),
    url(r'^alienController/(?P<agg_id>\d+)/(?P<slice_id>\d+)/$', 'add_controller_to_slice', name='alien_aggregate_slice_controller_add'),
    url(r'^alienVlan/(?P<agg_id>\d+)/(?P<slice_id>\d+)/$', 'add_vlan_to_slice', name='alien_aggregate_slice_vlan_add'),
    url(r'^alienTimeSlot/(?P<agg_id>\d+)/(?P<slice_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$', 'book_time_slot', name='alien_aggregate_slice_time_slot'),
    url(r'^calender/(?P<slice_id>\d+)/(?P<pYear>\d+)/(?P<pMonth>\d+)/$', 'calender', name='calender'),
)

