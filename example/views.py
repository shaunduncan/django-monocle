from django.http import HttpResponse, Http404
from django.template import RequestContext, loader

from .models import Blog, Entry


def home(request):
    try:
        blog = Blog.objects.all()[0]
    except IndexError:
        return HttpResponse('No blog is configured')
    else:
        entries = Entry.objects.filter(blog=blog).order_by('-id')

        template = loader.get_template('home.html')
        context = RequestContext(request, {
            'blog': blog,
            'entries': entries
        })

        return HttpResponse(template.render(context))


def entry(request, id):
    try:
        entry = Entry.objects.get(id=id)
    except Entry.DoesNotExist:
        raise Http404

    template = loader.get_template('entry.html')
    context = RequestContext(request, {'entry': entry})

    return HttpResponse(template.render(context))
