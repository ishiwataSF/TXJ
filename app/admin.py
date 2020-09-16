from django.contrib import admin
from .models import Staff, Customer, GenerateData, MatchedData, VisuallyMachedData, ImportData

admin.site.register(Staff)
admin.site.register(Customer)
admin.site.register(GenerateData)
admin.site.register(MatchedData)
admin.site.register(VisuallyMachedData)
admin.site.register(ImportData)

