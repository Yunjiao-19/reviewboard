"""Django model administration for OAuth2 applications."""

from __future__ import unicode_literals

import importlib

from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import flatten_fieldsets
from django.utils.translation import ugettext_lazy as _
from djblets.forms.fieldsets import filter_fieldsets

from reviewboard.admin import ModelAdmin, admin_site
from reviewboard.oauth.forms import (ApplicationChangeForm,
                                     ApplicationCreationForm)
from reviewboard.oauth.models import Application


class ApplicationAdmin(ModelAdmin):
    """The model admin for the OAuth application model.

    The default model admin provided by django-oauth-toolkit does not provide
    help text for the majority of the fields, so this admin uses a custom form
    which does provide the help text.
    """

    form = ApplicationChangeForm
    add_form = ApplicationCreationForm
    raw_id_fields = ('local_site',)

    fieldsets = (
        (_('General Settings'), {
            'fields': ('name',
                       'enabled',
                       'user',
                       'redirect_uris',),
        }),

        (_('Client Settings'), {
            'fields': ('client_id',
                       'client_secret',
                       'client_type'),
        }),

        (_('Authorization Settings'), {
            'fields': ('authorization_grant_type',
                       'skip_authorization',
                       'local_site',),
        }),

        (_('Internal State'), {
            'description': _(
                '<p>This is advanced state that should not be modified unless '
                'something is wrong.</p>'
            ),
            'fields': ('original_user',
                       'extra_data'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = tuple(filter_fieldsets(
        form=add_form,
        fieldsets=fieldsets,
        exclude_collapsed=False,
    ))

    def get_fieldsets(self, request, obj=None):
        """Return the appropriate fieldset.

        Args:
            request (django.http.HttpRequest):
                The current HTTP request.

            obj (reviewboard.oauth.models.Application, optional):
                The application being edited, if it already exists.

        Returns:
            tuple:
            The fieldset for either changing an Application (i.e., when
            ``obj is not None``) or the fieldset for creating an Application.
        """
        if obj is None:
            return self.add_fieldsets

        return super(ApplicationAdmin, self).get_fieldsets(request, obj=obj)

    def get_form(self, request, obj=None, **kwargs):
        """Return the form class to use.

        This method mostly delegates to the superclass, but hints that we
        should use :py:attr:`add_form` (and its fields) when we are creating
        the Application.

        Args:
            request (django.http.HttpRequest):
                The current HTTP request.

            obj (reviewboard.oauth.models.Application, optional):
                The application being edited, if it exists.

        Returns:
            type:
            The form class to use.
        """
        if obj is None:
            kwargs = kwargs.copy()
            kwargs['form'] = self.add_form
            kwargs['fields'] = flatten_fieldsets(self.add_fieldsets)

        return super(ApplicationAdmin, self).get_form(request, obj=obj,
                                                      **kwargs)

    def response_add(self, request, obj, post_url_continue=None):
        """Return the response for the ``add_view`` stage.

        This method will redirect the user to the change form after creating
        the application. We do this because the ``client_secret`` and
        ``client_id`` fields are generated by saving the form and it is likely
        the user will want to view and/or copy them after creating this
        Application.

        Args:
            request (django.http.HttpRequest):
                The current HTTP request.

            obj (reviewboard.oauth.models.Application):
                The application that was created.

            post_url_continue (unicode, optional):
                The next URL to go to.

        Returns:
            django.http.HttpResponse:
            A response redirecting the user to the change form.
        """
        if ('_addanother' not in request.POST and
            IS_POPUP_VAR not in request.POST):
            # request.POST is immutable on modern versions of Django. The
            # pattern used within Django for this exact situation is to copy
            # the dictionary and then modify it.
            request.POST = request.POST.copy()
            request.POST['_continue'] = 1

        return super(ApplicationAdmin, self).response_add(
            request,
            obj,
            post_url_continue=post_url_continue,
        )


# Ensure that the oauth2_provider admin modules is loaded so that we can
# replace their admin registration with our own. If we do not do this, we can't
# guarantee that it will be registered before we try to unregister it during
# unit tests.
importlib.import_module('oauth2_provider.admin')
admin_site.unregister(Application)
admin_site.register(Application, ApplicationAdmin)
