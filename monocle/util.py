from urlparse import urlparse, parse_qs


def extract_content_url(endpoint_url):
    """
    Extracts the original url from an OEmbed request URL
    """
    url = parse_qs(urlparse(endpoint_url).query)

    if isinstance(url, list):
        return url[0]
    else:
        return url
