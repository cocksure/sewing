# materials/urls.py
from django.urls import path

from . import views

app_name = "info"

urlpatterns = [
    path("materials/", views.MaterialListView.as_view(), name="materials-list"),
    path("material-create/", views.MaterialListCreateView.as_view(), name="material-create"),

    path("material-groups/", views.MaterialGroupListCreateView.as_view(), name="material-groups"),
    path("colors/", views.ColorListCreateView.as_view(), name="colors-list"),
    path("size/", views.SizeListCreateView.as_view(), name="sizes-list"),
    path("operations/", views.OperationListCreateView.as_view(), name="operations-list"),
    path("specifications/", views.SpecificationListCreateView.as_view(), name="spec-list"),

    path("firms/", views.FirmListCreateView.as_view(), name="firm-list"),
    path("processes/", views.ProcessesListCreateView.as_view(), name="process-list"),
    path("worktype/", views.WorkTypeListCreateView.as_view(), name="work_type-list"),
]
