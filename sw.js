// 상한가 농장 오프라인 저장: 그림·소리(a/)는 한 번 받으면 보관, 페이지는 늘 새 것 먼저
const V='shg-161618b573';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V&&k!=='shg-a').map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==location.origin)return;
 if(u.pathname.includes('/a/')){e.respondWith(caches.open('shg-a').then(c=>c.match(e.request).then(r=>r||fetch(e.request).then(n=>{if(n.ok)c.put(e.request,n.clone());return n}))));return}
 e.respondWith(fetch(e.request,{cache:'no-cache'}).then(n=>{const c=n.clone();caches.open(V).then(x=>x.put(e.request,c));return n}).catch(()=>caches.match(e.request)))});
