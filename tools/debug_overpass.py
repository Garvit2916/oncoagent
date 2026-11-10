import urllib.request, urllib.parse, json, time

ENDPOINTS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
    'https://overpass.openstreetmap.ru/api/interpreter',
]

def test(endpoint):
    q = '[out:json][timeout:15];(nwr["amenity"~"hospital|clinic"](around:3000,40.7580,-73.9855););out center tags 8;'
    url = endpoint + '?' + urllib.parse.urlencode({'data': q})
    req = urllib.request.Request(url, headers={'User-Agent': 'OncoAgent/2.0 (educational research)'})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        n = len(d.get('elements', []))
        print(endpoint.split('/')[2], 'OK elements:', n)
        if d.get('elements'):
            print('   sample:', json.dumps({'name': d['elements'][0].get('tags', {}).get('name')})[:120])
        return n
    except Exception as e:
        print(endpoint.split('/')[2], 'FAIL:', e)
        return None

for ep in ENDPOINTS:
    test(ep)
    time.sleep(3)