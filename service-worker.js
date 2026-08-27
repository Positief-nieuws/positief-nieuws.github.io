const CACHE_NAME = "positief-nieuws-v3";

const CORE_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
  "/icon-192-v2.png",
  "/icon-512-v2.png",
  "/edities/index.json"
];


self.addEventListener(
  "install",
  event => {

    event.waitUntil(
      caches.open(CACHE_NAME)
        .then(cache => cache.addAll(CORE_ASSETS))
    );

    self.skipWaiting();
  }
);


self.addEventListener(
  "activate",
  event => {

    event.waitUntil(
      caches.keys()
        .then(
          keys => Promise.all(
            keys
              .filter(key => key !== CACHE_NAME)
              .map(key => caches.delete(key))
          )
        )
    );

    self.clients.claim();
  }
);


self.addEventListener(
  "fetch",
  event => {

    const request = event.request;

    if (request.method !== "GET") {
      return;
    }


    const url =
      new URL(request.url);

    if (url.origin !== self.location.origin) {
      return;
    }


    const isNavigation =
      request.mode === "navigate";

    const isFreshData =
      url.pathname.endsWith("/nieuws.json")
      || url.pathname.endsWith("/edities/index.json")
      || /\/edities\/\d{4}-\d{2}-\d{2}\.json$/.test(
        url.pathname
      );


    if (isNavigation || isFreshData) {

      event.respondWith(
        fetch(request)
          .then(
            response => {

              const copy =
                response.clone();

              caches.open(CACHE_NAME)
                .then(
                  cache =>
                    cache.put(
                      request,
                      copy
                    )
                );

              return response;
            }
          )
          .catch(
            () =>
              caches.match(request)
                .then(
                  cached =>
                    cached
                    || caches.match("/")
                )
          )
      );

      return;
    }


    event.respondWith(
      caches.match(request)
        .then(
          cached =>
            cached
            || fetch(request)
              .then(
                response => {

                  const copy =
                    response.clone();

                  caches.open(CACHE_NAME)
                    .then(
                      cache =>
                        cache.put(
                          request,
                          copy
                        )
                    );

                  return response;
                }
              )
        )
    );
  }
);
