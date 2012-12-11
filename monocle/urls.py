from django.conf.urls.defaults import *

urlpatterns = patterns('monocle.views',
    url(r'^$', 'oembed', name='oembed'),
)
