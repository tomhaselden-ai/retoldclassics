const CACHE_NAME = "story-universe-shell-v2";
const SHELL_FILES = ["/", "/manifest.webmanifest", "/icon.svg"];

function isCacheableRequest(request) {
  const url = new URL(request.url);

  if (request.method !== "GET") {
    return false;
  }

  if (url.origin !== self.location.origin) {
    return false;
  }

  if (
    url.pathname.startsWith("/auth") ||
    url.pathname.startsWith("/accounts") ||
    url.pathname.startsWith("/readers") ||
    url.pathname.startsWith("/stories") ||
    url.pathname.startsWith("/classics") ||
    url.pathname.startsWith("/dashboard") ||
    url.pathname.startsWith("/worlds") ||
    url.pathname.startsWith("/continuity") ||
    url.pathname.startsWith("/safety") ||
    url.pathname.startsWith("/alexa")
  ) {
    return false;
  }

  return true;
}

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))),
    ),
  );
});

self.addEventListener("fetch", (event) => {
  if (!isCacheableRequest(event.request)) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return response;
      });
    }),
  );
});
