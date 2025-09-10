from django.urls import path

from sewing import views

app_name = 'sewing'

urlpatterns = [
    path('models/', views.ModelsListView.as_view(), name='models-list'),
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

    # ------------- Orders strat
    path('orders/', views.SewingOrderListView.as_view(), name='orders-list'),

    path("order-create", views.SewingOrderCreateView.as_view(), name="order-create"),
    path("orders/<int:pk>/edit/", views.SewingOrderEditView.as_view(), name="order-edit"),

    # AJAX-модалки для строк
    path("orders/<int:pk>/edit/", views.SewingOrderEditView.as_view(), name="orders-edit"),
    path("orders/<int:pk>/items/partial/", views.order_items_partial, name="order-items-list"),

    path("orders/<int:pk>/items/add/", views.order_item_form, name="order-item-add"),
    path("order-items/<int:item_id>/edit/", views.order_item_form, name="order-item-edit"),
    path("order-items/<int:item_id>/delete/", views.order_item_delete, name="order-item-delete"),

    path("order-items/<int:item_id>/sizes/", views.order_item_sizes_modal, name="order-item-sizes"),
    path("order-items/<int:item_id>/sizes/save/", views.order_item_sizes_save, name="order-item-sizes-save"),

]
