from django.contrib import admin
from .models import WebPage, Author

class WebPageAdmin(admin.ModelAdmin):
    list_display = ('url', 'crawled_at')
    search_fields = ('url',)
    list_filter = ('crawled_at',)
    ordering = ('-crawled_at',)

class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'page', 'interests', 'homepage', 'email', 'sent_email')
    search_fields = ('name', 'interests', 'homepage')
    list_filter = ('sent_email',)
    ordering = ('-page__crawled_at',)
    
admin.site.register(WebPage, WebPageAdmin)
admin.site.register(Author, AuthorAdmin)