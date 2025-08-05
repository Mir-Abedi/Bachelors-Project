from django.shortcuts import render
from django.views.generic import ListView
from django.core.paginator import Paginator
from webpages.models import WebPage, Author, WebPagePart
from webpages.forms import WebPageForm
from django.shortcuts import redirect
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

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

class WebPageDetailView(ListView):
    model = WebPage
    template_name = 'webpages/webpage.html'
    context_object_name = 'webpage'

    def get_queryset(self):
        """
        Override the default queryset to filter parts by the webpage ID.
        """
        webpage_id = self.kwargs.get('pk')
        return WebPage.objects.filter(id=webpage_id).annotate(
            authors_count=Count("authors")
        ).first()

class AuthorDetailView(ListView):
    model = Author
    template_name = 'webpages/author.html'
    context_object_name = 'author'

    def get_queryset(self):
        """
        Override the default queryset to filter authors by the author ID.
        """
        author_id = self.kwargs.get('author_id')
        author = Author.objects.get(id=author_id)
        works = [i["title"] for i in author.works["results"]] if author.works else []
        author.works_list = works[:5]
        return author

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

def update_author_email(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    
    if request.method == 'POST':
        new_email = request.POST.get('email')
        if new_email:
            author.email = new_email
            author.save()
            messages.success(request, "Email updated successfully!")
        else:
            messages.error(request, "Please provide a valid email address.")
    
    return redirect('author_detail', author_id=author_id)

class SendEmailView(ListView):
    model = Author
    template_name = 'webpages/send_email.html'
    context_object_name = 'send_email'

    def get_queryset(self):
        """
        Override the default queryset to filter authors by the author ID.
        """
        author_id = self.kwargs.get('author_id')
        author = Author.objects.get(id=author_id)
        return author