from django.contrib import admin
from .models import Staff, Customer, GeneratedData, MatchedData, VisuallyMatchedData, ImportData

admin.site.register(Staff)
admin.site.register(Customer)
admin.site.register(GeneratedData)
admin.site.register(MatchedData)
admin.site.register(VisuallyMatchedData)
admin.site.register(ImportData)

