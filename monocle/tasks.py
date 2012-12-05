import json
import urllib2

from celery.task import task
from django.core.cache import cache

from monocle.cache import make_key
from monocle.resources import Resource
from monocle.settings import (HTTP_TIMEOUT,
                              TASK_QUEUE,
                              TASK_EXTERNAL_MAX_RETRIES,
                              TASK_EXTERNAL_RETRY_DELAY)


@task(queue=TASK_QUEUE,
      ignore_result=True,
      max_retries=TASK_EXTERNAL_MAX_RETRIES,
      default_retry_delay=TASK_EXTERNAL_RETRY_DELAY)
def request_external_oembed(url):
    """
    Obtains an oembed resource from an external provider with
    sensible task retry. Results are expected to be valid JSON
    meaning the url provided must explicitly contain format=json
    """
    logger = request_external_oembed.get_logger()
    logger.info('Requesting OEmbed Resource %s' % url)

    try:
        request = urllib2.urlopen(url, timeout=HTTP_TIMEOUT)
    except urllib2.HTTPError, e:
        logger.error('Failed to obtain %s : Status %s' % (url, e.code))
    except urllib2.URLError, e:
        if 'timed out' in str(e):
            # On a timeout, retry in hopes that it won't next time
            request_external_oembed.retry(args=[url], exc=e)
        else:
            logger.exception('Unexeped error when retrieving OEmbed %s' % url)
    else:
        if request.getcode() != 200:
            logger.error('URL %s resulted in unexpected HTTP status' % (url, request.getcode()))
        else:
            try:
                # TODO: creating a resource should validate and raise
                resource = Resource(json.loads(request.read()))
            except ValueError:
                logger.error('OEmbed response from %s contains invalid JSON' % url)
            else:
                # Update the cache with this data
                cache.set(make_key(url), resource.ttl)
            finally:
                request.close()
