""" reimplementation of rest_framework.routers.DefaultRouter. Mostly copied, added get_view_description to APIRoot """

from rest_framework import routers
from collections import OrderedDict
from django.core.urlresolvers import NoReverseMatch
from rest_framework import views
from rest_framework.response import Response
from rest_framework.reverse import reverse
from django.utils.safestring import mark_safe


class DefaultRouter(routers.DefaultRouter):
    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)
        registry = self.registry

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get_view_description(self, html=False):
                parts = []
                for authenticator in self.get_authenticators():
                    if hasattr(authenticator, 'get_authenticator_description'):
                        desc = authenticator.get_authenticator_description(self, html)
                        parts.append(desc)
                return mark_safe('\n'.join([part for part in parts if part]))

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue

                return Response(ret)

        return APIRoot.as_view()
