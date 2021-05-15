from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Category, CourseCategory


from django.contrib import admin


class CourseCategoryInline(admin.TabularInline):
    model = CourseCategory.category.through


class CategoryAdmin(MPTTModelAdmin):
    tree_auto_open = True
    prepopulated_fields = {'slug': ('name',)}
    fields = ['name', 'slug', 'description', 'parent']
    search_fields = ['name', 'slug']
    exclude = ('enabled',)


class CourseCategoryAdmin(admin.ModelAdmin):
    inlines = [CourseCategoryInline,]
    list_display = ('course_id',)
    search_fields = ['course_id']


admin.site.register(Category, CategoryAdmin)
admin.site.register(CourseCategory, CourseCategoryAdmin)

