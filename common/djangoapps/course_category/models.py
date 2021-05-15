from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField(max_length=255, verbose_name=_("Category Name"))
    description = models.TextField(null=True, blank=True)
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        on_delete=models.CASCADE
    )
    enabled = models.BooleanField(default=True)
    slug = models.SlugField(max_length=255, unique=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def get_course_ids(self, **kwargs):
        qs = self.coursecategory_set.filter(**kwargs)
        return [c.course_id for c in qs]

    def get_course_names(self, **kwargs):
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

        qs = self.coursecategory_set.filter(**kwargs)
        return [CourseOverview.get_from_id(c.course_id).display_name for c in qs]

    def is_level_passed(self, user):
        if not self.parent:
            return True
        from lms.djangoapps.certificates.models import GeneratedCertificate
        # descendants = self.get_descendants(include_self=False)
        is_passed = False
        certificates = GeneratedCertificate.eligible_certificates.filter(user=user)
        course_ids = self.parent.get_course_ids()
        if certificates.count() >= len(course_ids):
            for course_id in course_ids:
                try:
                    certificates.get(
                        Q(course_id=course_id) &
                        (Q(status='generating') | Q(status='downloadable'))
                    )
                except:
                    return is_passed
            is_passed = True
        return is_passed

    @classmethod
    def get_category_tree(cls, **kwargs):
        def add_nodes(nodes):
            tree = {}
            for node in nodes:
                tree[node] = None
                if not node.is_leaf_node():
                    tree[node] = add_nodes(node.children.filter(**kwargs))
            return tree
        return add_nodes(cls.objects.filter(parent=None, **kwargs))

    @classmethod
    def get_level_tree(cls):
        """
        This will return list of level with URL and tree representation
        """
        level_list = []
        def add_nodes(categories, count):
            for course_category in categories:
                num = count
                level_about = reverse('course_category', kwargs={'slug': course_category.slug})
                level_list.append([level_about, ('-- '*num) + course_category.name])
                if not course_category.is_leaf_node():
                    num += 1
                    add_nodes(course_category.children.all(), num)

        add_nodes(cls.objects.filter(parent=None), 0)
        return level_list

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class CourseCategory(models.Model):
    category = models.ManyToManyField(Category, blank=True)
    course_id = CourseKeyField(
        max_length=255,
        db_index=True,
        verbose_name=_("Course"),
        unique=True,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Course Category")
        verbose_name_plural = _("Course Categories")

    @classmethod
    def get_course_category(cls, course_id, return_obj_id=False):
        try:
            course_category = cls.objects.get(course_id=course_id)
            if return_obj_id:
                course_category = list(map(str, list(course_category.category.values_list('id', flat=True))))
            else:
                course_category = course_category.category.all()
        except cls.DoesNotExist:
            course_category = None
        return course_category
