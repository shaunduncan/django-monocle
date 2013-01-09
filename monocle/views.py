from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)

from monocle.providers import registry


class HttpResponseNotImplemented(HttpResponse):
    status_code = 501


def oembed(request):
    """
    A view that adheres to `OEmbed Spec <http://oembed.com>`_ of what a provider
    endpoint should do. Any :class:`monocle.providers.Provider` that is configured
    to be exposed can be provided via this view.

    Both ``maxwidth`` and ``maxheight`` are honored, but no other URL parameter is.
    This implies that all responses are delivered as JSON (i.e. ``format=json``).
    XML is not supported. If a request specifies ``format=xml`` or some other unknown
    format other than JSON, a 501 response is returned.

    If no provider is found, or a provider is not exposed, a 404 is returned.
    If no resource can be retrieved from the found provider, or it is invalid, a 404
    is also returned. Else the resource is returned as JSON.
    """
    url = request.GET.get('url')
    format = request.GET.get('format', 'json').lower()

    if not url:
        return HttpResponseBadRequest('Paramater URL is missing')

    # TODO: Support xml
    if format != 'json':
        return HttpResponseNotImplemented('OEmbed format %s not implemented' % format)

    # Get optional and trim None
    params = {
        'maxwidth': request.GET.get('maxwidth'),
        'maxheight': request.GET.get('maxheight')
    }

    # Filter nones and non-numbers
    for k, v in params.items():
        if not v:
            del params[k]
        else:
            # Coerce
            try:
                params[k] = int(v)
            except ValueError:
                del params[k]

    provider = registry.match(url)

    # 404 on resource not found on non-exposed endpoint
    if not provider or not provider.expose:
        return HttpResponseNotFound('OEmbed for this URL not available')

    resource = provider.get_resource(url, **params)

    if resource.is_valid:
        return HttpResponse(resource.json, mimetype='application/json')
    else:
        return HttpResponseNotFound('OEmbed resource is invalid or unavailable')
