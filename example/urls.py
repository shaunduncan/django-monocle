from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from monocle import urls as monocle_urls

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'example.views.home', name='home'),
    url(r'^entry/(?P<id>\d+)/$', 'example.views.entry', name='entry'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oembed/', include(monocle_urls)),
)

urlpatterns += staticfiles_urlpatterns()
