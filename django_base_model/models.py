import re

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

ATTRIBUTE_MODEL_NAME_PATTERN = re.compile('^[a-z0-9_]+$')


class ModelAttribute(models.Model):
    """
    Defines a simple name/value pair model that can be used with generic
    content type relationships to add any number of arbitrary properties to a
    model that inherits from BaseModel.

    Names should follow standard Python property naming conventions (and are
    enforced with a model validation method).  It will also be automatically
    lower-cased if it isn't already.

    Values can be anything as they are stored in a TextField.
    """

    name = models.CharField(
        max_length=255,
        help_text="""The name must be set to something that looks like a Python property (e.g., "my_property")."""
    )
    value = models.TextField(blank=True, default='')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u'%s: %s' % (self.name, self.value)

    def clean(self):
        """
        Model clean method to validate the value of "name" before saving any
        changes to the model.  We only want valid names that could be turned
        easily into Python attributes on an object.
        """

        self.name = self.name.lower()

        if ATTRIBUTE_MODEL_NAME_PATTERN.match(self.name) is None:
            raise ValidationError(
                'The name must be in the format of a Python property (e.g., "my_property").'
            )

    def save(self, *args, **kwargs):
        """
        Override the save method so that we ensure we're only saving the name
        field in lower case.
        """

        # This will have already passed validation and we want to keep the
        # names lower case.
        self.name = self.name.lower()

        return super(ModelAttribute, self).save(*args, **kwargs)


class BaseModelManager(models.Manager):
    """
    Defines a model manager that accounts for arbitrary content type
    relationships associated with the model and sets up the necessary
    properties when doing a get of a single instance of the model.
    """

    def get(self, *args, **kwargs):
        return super(BaseModelManager, self).get(*args, **kwargs)

    def get_or_create(self, **kwargs):
        return super(BaseModelManager, self).get_or_create(**kwargs)

    def create(self, **kwargs):
        return super(BaseModelManager, self).create(**kwargs)


class BaseModel(models.Model):
    """
    Defines an abstract model built off of Django's Model class that
    provides some common fields that are useful on multiple models
    across multiple projects.
    """

    time_created = models.DateTimeField(auto_now_add=True, null=True)
    time_modified = models.DateTimeField(auto_now=True, null=True)
    last_modified_by = models.ForeignKey(
        User,
        related_name='%(app_label)s_%(class)s_related',
        null=True,
        blank=True
    )
    attributes = generic.GenericRelation(ModelAttribute)

    objects = BaseModelManager()

    class Meta:
        abstract = True
