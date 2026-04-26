const CACHE_NAME = 'trd-v12.3';
const STATIC_ASSETS = [
  '/trading-server/',
  '/trading-server/index.html',
  '/trading-server/manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // API calls - network first
  if (url.hostname.includes('trycloudflare.com')) {
    e.respondWith(
      fetch(e.request).catch(() => new Response(JSON.stringify({error:'offline',cached:true}), {headers:{'Content-Type':'application/json'}}))
    );
    return;
  }
  // App shell - cache first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.status === 200) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      }
      return res;
    }))
  );
});

// Push notifications
self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : {title:'TRD Alert', body:'Check your dashboard'};
  e.waitUntil(
    self.registration.showNotification(data.title || 'TRD v12.3', {
      body: data.body || '',
      icon: '/trading-server/icons/icon-192.png',
      badge: '/trading-server/icons/icon-72.png',
      tag: data.tag || 'trd-alert',
      vibrate: [200, 100, 200],
      data: {url: data.url || '/trading-server/'},
      actions: [
        {action: 'view', title: 'View', icon: '/trading-server/icons/icon-72.png'},
        {action: 'dismiss', title: 'Dismiss'}
      ]
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  if (e.action === 'view' || !e.action) {
    e.waitUntil(clients.openWindow(e.notification.data?.url || '/trading-server/'));
  }
});
