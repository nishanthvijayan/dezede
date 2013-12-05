# coding: utf-8

from __future__ import unicode_literals
import json
from django.http import HttpResponse
from django.views.generic import ListView
from haystack.query import SearchQuerySet
from haystack.views import SearchView
from .models import Diapositive


class HomeView(ListView):
    model = Diapositive
    template_name = 'home.html'

    def get_queryset(self):
        qs = super(HomeView, self).get_queryset()
        return qs.published(self.request)


class CustomSearchView(SearchView):
    """
    Custom SearchView to fix spelling suggestions.
    """
    def extra_context(self):
        context = {'suggestion': None}

        if self.results.query.backend.include_spelling:
            suggestion = self.form.get_suggestion()
            if suggestion != self.query:
                context['suggestion'] = suggestion

        return context


def autocomplete(request):
    q = request.GET.get('q', '')
    sqs = SearchQuerySet().autocomplete(content_auto=q)[:5]
    suggestions = [unicode(result.object) for result in sqs]
    data = json.dumps(suggestions)
    return HttpResponse(data, content_type='application/json')
