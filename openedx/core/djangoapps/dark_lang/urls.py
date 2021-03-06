"""
Contains all the URLs for the Dark Language Support App
"""

from django.conf.urls import patterns, url

from openedx.core.djangoapps.dark_lang import views

urlpatterns = patterns(
    '',
    url(r'^$', views.PreviewLanguageFragmentView.as_view(), name='preview_lang'),
)
