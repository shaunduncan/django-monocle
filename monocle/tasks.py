import json
import urllib2

from celery import registry
from celery.task import Task

from monocle.cache import cache
from monocle.resources import Resource
from monocle.settings import settings
from monocle.util import extract_content_url


class RequestExternalOEmbedTask(Task):
    """
    A celery task that is meant to perform asynchronous requests to external
    providers so as not to block anything. Results are explicitly expected
    to be valid JSON, meaning the URL provided must contain ``format=json``.
    XML formatted responses are currently unsupported
    """
    name = 'request_external_oembed'
    ignore_result = True
    queue = settings.TASK_QUEUE
    max_retries = settings.TASK_EXTERNAL_MAX_RETRIES
    default_retry_delay = settings.TASK_EXTERNAL_RETRY_DELAY

    def run(self, url):
        logger = self.get_logger()
        logger.info('Requesting OEmbed Resource %s' % url)
        # The user agent needs to be spoofed here because some services,
        # like Vimeo, block requests that look like they came from a bot
        req = urllib2.Request(url, headers={'User-agent': settings.USER_AGENT})
        try:
            request = urllib2.urlopen(req, timeout=settings.HTTP_TIMEOUT)
        except urllib2.HTTPError, e:
            logger.error('Failed to obtain %s : Status %s' % (url, e.code))
        except urllib2.URLError, e:
            if 'timed out' in str(e):
                # On a timeout, retry in hopes that it won't next time
                self.retry(args=[url], exc=e)
            else:
                logger.exception('Unexeped error when retrieving OEmbed %s' % url)
        else:
            if request.getcode() != 200:
                logger.error('URL %s resulted in unexpected HTTP status' % (url, request.getcode()))
            else:
                original_url = extract_content_url(url)

                try:
                    # TODO: Any validation that should happen here?
                    # Do we store invalid data? If invalid do we clear the cache?
                    data = json.loads(request.read())
                except ValueError:
                    logger.error('OEmbed response from %s contains invalid JSON' % url)
                else:
                    # Update the cache with this data
                    cache.set(url, Resource(original_url, data))
                finally:
                    request.close()


request_external_oembed = registry.tasks[RequestExternalOEmbedTask.name]
