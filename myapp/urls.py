"""
URL configuration for voicevault project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from myapp import views

urlpatterns = [
    path('adminhome_get/',views.adminhome_get),
    path('login_get/',views.login_get),
    path('viewuser_get/',views.viewuser_get),
    path('viewcom_get/',views.viewcom_get),
    path('sentrep_get/<id>',views.sentrep_get),
    path('login_post/',views.login_post),
    path('sentrep_post/',views.sentrep_post),
    path('adminchgpass_get/',views.adminchgpass_get),
    path('adminchgpass_post/',views.adminchgpass_post),
    path('logout_get/',views.logout_get),

    # Client routes
    path('client_register_get/', views.client_register_get),
    path('client_register_post/', views.client_register_post),
    path('client_voice_login_get/', views.client_voice_login_get),
    path('client_voice_login_post/', views.client_voice_login_post),
    path('clienthome_get/', views.clienthome_get),
    path('client_complaint_get/', views.client_complaint_get),
    path('client_complaint_post/', views.client_complaint_post),
    path('client_view_complaints_get/', views.client_view_complaints_get),
    path('uploadvoice_get/', views.uploadvoice_get),
    path('uploadvoice_post/', views.uploadvoice_post),
    path('uploadvoice_delete/<int:audio_id>/', views.uploadvoice_delete),
    path('speakvoice_get/', views.speakvoice_get),
    path('speakvoice_record_post/', views.speakvoice_record_post),

    # App Lock
    path('applock_get/', views.applock_get),
    path('applock_toggle/<int:app_id>/', views.applock_toggle_post),

    # Document Lock
    path('doclock_get/', views.doclock_get),
    path('doclock_upload_post/', views.doclock_upload_post),
    path('doclock_delete/<int:doc_id>/', views.doclock_delete_post),
    path('doclock_toggle/<int:doc_id>/', views.doclock_toggle_post),
    path('doclock_access/<int:doc_id>/', views.doclock_access_post),
    path('doclock_rename/<int:doc_id>/', views.doclock_rename_post),
    path('update_profile/', views.update_profile),
    path('delete_account/', views.delete_account),
]
