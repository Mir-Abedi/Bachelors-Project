from django.shortcuts import render
from django.views.generic import ListView
from django.core.paginator import Paginator
from webpages.models import WebPage, Author, WebPagePart
from webpages.forms import WebPageForm
from django.shortcuts import redirect
from django.db.models import Count, Q

def index(request):
    """
    View function for the home page of the website.
    """
    return render(request, 'webpages/index.html') 

def about(request):
    """
    View function for the about page of the website.
    """
    return render(request, 'webpages/about.html') 

class AuthorListView(ListView):
    model = Author
    template_name = 'webpages/authors.html'
    context_object_name = 'authors'
    paginate_by = 10  # Show 10 authors per page


class WebPageListView(ListView):
    model = WebPage
    template_name = 'webpages/webpages.html'
    context_object_name = 'webpages'
    paginate_by = 10  # Show 10 webpages per page

    def get_queryset(self):
        """
        Override the default queryset to annotate the number of parts for each webpage.
        """
        return WebPage.objects.annotate(
            parts_count=Count('parts'),
            parts_done=Count('parts', filter=Q(parts__is_done=True))
        ).order_by('id')


def add_webpage(request):
    """
    View function for the add webpage page of the website.
    """
    if request.method == 'POST':
        form = WebPageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('webpages')
    else:
        form = WebPageForm()
    return render(request, 'webpages/add_webpage.html', {'form': form}) 

