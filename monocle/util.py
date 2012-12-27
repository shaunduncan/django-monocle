from urlparse import urlparse, parse_qs


def extract_content_url(endpoint_url):
    """
    Extracts the original url from an OEmbed request URL
    """
    url = parse_qs(urlparse(endpoint_url).query).get('url')

    if isinstance(url, list):
        return url[0]
    else:
        return url


def synced(*models):
    """
    Returns True if all model tables are in the full table list.
    If database introspection fails, False is returned
    """
    try:
        from django.db import connection as conn
        tables = conn.introspection.get_table_list(conn.cursor())
    except:
        return False

    for model in models:
        if model._meta.db_table not in tables:
            return False
    return True
