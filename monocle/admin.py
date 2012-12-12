from django.contrib import admin

from monocle.models import ThirdPartyProvider, URLScheme


class URLSchemeInline(admin.TabularInline):
    model = URLScheme
    verbose_name = 'URL Scheme'
    verbose_name_plural = 'URL Schemes'


class ThirdPartyProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_endpoint', 'resource_type', 'is_active', 'expose')
    list_filter = ('is_active', 'expose')

    # This makes managing much easier
    inlines = [
        URLSchemeInline,
    ]


admin.site.register(ThirdPartyProvider, ThirdPartyProviderAdmin)
