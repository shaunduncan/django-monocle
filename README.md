==================================
Monocle: Rich Content using OEmbed
==================================

![Like A Sir](http://i.imgur.com/WzjGo.png)

Monocle is a Django app built for rich content embedding using [OEmbed](http://oembed.com)
that is built with scalability and performance in mind


Documentation
-------------
Nothing to see here yet


Things This Should Do/Notes
---------------------------
- Allow for a local provider mechanism: a model/view aware provider that doesn't hit the network
  - Don't make any assumptions here about doing image resizing and what not
    just define any requirements that implementors should handle
- Custom oembeddable content field that triggers a celery task (if configured) to retrieve content
- On request/template tag for oembeddable content, if cache miss, trigger a celery task (if configured)
  for content and hyperlink the oembed link. If not, retrieve the content from the provider
- Utilize django cache backend for holding rendered oembed content (Need to determine a good hash key)
  Cache Key: request\_url
- Similar template tags and filters from existing library
- Tasks? Should there be any for cache maintenance?
- Make no assumptions of "automagic" providers, try to generalize as much as possible
- Prefer lxml.html over BeautifulSoup?
- Model system should only provide for endpoints (i.e. third party providers)
  - Multiple URL patterns for a single endpoint?
  - Old system stores all providers in memory. Is that good? Use an in-memory registry?
- Url/view system should allow retrieval of oembed content
- Configurable exposing oembed endpoint for providers: is it needed?
  - Currently used by the admin to suggest content details for video/etc
- Configure to enable image resizing for local/model providers
  - Model endpoint should define how to handle this?
- Special case for embed.ly? Requires API credentials
