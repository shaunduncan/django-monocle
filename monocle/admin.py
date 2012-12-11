from django.contrib import admin
from monocle.models import ThirdPartyProvider, URLScheme


class ThirdPartyProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_endpoint', 'resource_type', 'is_active', 'expose')
    list_filter = ('is_active', 'expose')


class URLSchemeAdmin(admin.ModelAdmin):
    list_display = ('scheme',)


admin.site.register(ThirdPartyProvider, ThirdPartyProviderAdmin)
admin.site.register(URLScheme, URLSchemeAdmin)
