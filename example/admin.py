from django.contrib import admin

from .models import Blog, Entry


class BlogAdmin(admin.ModelAdmin):
    list_display = ('name',)


class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'blog')
    verbose_name_plural = 'Entries'


admin.site.register(Blog, BlogAdmin)
admin.site.register(Entry, EntryAdmin)
