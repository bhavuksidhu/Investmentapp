from django.db.utils import IntegrityError
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .custom_mixins import OnlyPOSTUpdateModelMixin
from core.models import User
from .utils import NoDataException, StandardResultsSetPagination


class GetViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    def get_object(self):
        return self.get_queryset()

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(self,"many"):
            serializer = self.get_serializer(instance,many=True)
        else:
            serializer = self.get_serializer(instance)
        return Response(serializer.data)


class GetPostViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    def get_object(self):
        return self.get_queryset()

    def perform_update(self, serializer):
        serializer.save()

    def list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
    
    def dispatch(self, request, *args, **kwargs):
        response =  super().dispatch(request, *args, **kwargs)
        if "status" in response.data:
            return response
        else:
            response.data["status"] = response.status_code
        return response


@extend_schema(parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)])
class GetPostUsingIdViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    def get_object(self):
        return self.get_queryset()

    # This relies on the NotSoSimpleRouter described in custom_routers
    def upload(self, request, *args, **kwargs):

        user_id = self.kwargs["pk"]
        try:
            user = User.objects.select_related().get(id=user_id)
            if user.linked_to != self.request.user:
                return NoDataException
        except User.DoesNotExist:
            return NoDataException

        profile = user.profile

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile_photo = self.perform_create(serializer)
        profile.profile_photo = profile_photo
        profile.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        return serializer.save()

    def get_success_headers(self, data):
        try:
            return {"Location": str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    ),
    update=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    ),
    destroy=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    ),
)
class ListGetPostUpdateDestroyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    OnlyPOSTUpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = StandardResultsSetPagination

@extend_schema_view(
    retrieve=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    ),
    update=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    ),
)
class ListGetUpdateViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    OnlyPOSTUpdateModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = StandardResultsSetPagination
