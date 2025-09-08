from django.urls import path

from sewing import views

app_name = 'sewing'

urlpatterns = [
    path('', views.ModelsListView.as_view(), name='models-list'),
    path("models/create/", views.SewingProductModelCreateView.as_view(), name="model-create"),
    path("models/<int:pk>/edit/", views.SewingProductModelEditView.as_view(), name="model-edit"),
    path("variants/<int:pk>/edit/", views.VariantEditView.as_view(), name="variant-edit"),
    path("variants/<int:pk>/clone/", views.VariantCloneView.as_view(), name="variant-clone"),

    path("variant/<int:pk>/accessories/fill/", views.VariantFillFromView.as_view(kind="accessories"),
         name="variant-accessories-fill"),
    path("variant/<int:pk>/operations/fill/", views.VariantFillFromView.as_view(kind="operations"),
         name="variant-operations-fill"),

    # variant -materials
    path("variant/<int:pk>/materials/", views.VariantMaterialsListView.as_view(), name="variant-materials"),
    path("variant/<int:pk>/materials/create/", views.VariantMaterialCreateView.as_view(),
         name="variant-material-create"),
    path("variant/material/<int:pk>/edit/", views.VariantMaterialUpdateView.as_view(), name="variant-material-edit"),
    path("variant/material/<int:pk>/delete/", views.VariantMaterialDeleteView.as_view(),
         name="variant-material-delete"),

    # variant -accessories
    path("variant/<int:pk>/accessories/", views.VariantAccessoriesListView.as_view(), name="variant-accessories"),
    path("variant/<int:variant_id>/accessories/create/", views.VariantAccessoryCreateView.as_view(),
         name="variant-accessory-create"),
    path("variant/accessory/<int:pk>/edit/", views.VariantAccessoryUpdateView.as_view(), name="variant-accessory-edit"),
    path("variant/accessory/<int:pk>/delete/", views.VariantAccessoryDeleteView.as_view(),
         name="variant-accessory-delete"),

    # variant -operations
    path("variant/<int:pk>/operations/", views.VariantOperationsListView.as_view(), name="variant-operations", ),
    path("variant/<int:variant_id>/operations/create/", views.VariantOperationCreateView.as_view(),
         name="variant-operation-create", ),
    path("variant/operation/<int:pk>/edit/", views.VariantOperationUpdateView.as_view(),
         name="variant-operation-edit", ),
    path("variant/operation/<int:pk>/delete/", views.VariantOperationDeleteView.as_view(),
         name="variant-operation-delete", ),

    # variant -sizes
    path("variant/<int:pk>/sizes/", views.VariantSizesListView.as_view(), name="variant-sizes"),
    path("variant/<int:variant_id>/sizes/create/", views.VariantSizeCreateView.as_view(), name="variant-size-create"),
    path("variant/size/<int:pk>/edit/", views.VariantSizeUpdateView.as_view(), name="variant-size-edit"),
    path("variant/size/<int:pk>/delete/", views.VariantSizeDeleteView.as_view(), name="variant-size-delete"),

]
