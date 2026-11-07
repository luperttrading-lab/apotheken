#!/usr/bin/env python3
"""Baut die Apotheken-Kacheln unter daten/ aus OpenStreetMap.

Warum: Live-Abfragen an die öffentlichen Overpass-Server dauerten am 07.11.2026 16-45 s oder
scheiterten (504). Die App lädt stattdessen vorberechnete Kacheln von GitHub Pages (< 1 s).

Aufruf:  python3 tools/daten_bauen.py                 # holt die Daten selbst von Overpass
         python3 tools/daten_bauen.py rohdaten.json   # nimmt eine fertige Overpass-Antwort

Kacheln: 0,5 Grad Breite x 0,5 Grad Länge, Name "<floor(lat*2)>_<floor(lon*2)>.json".
Zeile je Apotheke: [lat, lon, name, straße, plz, ort, telefon, website, opening_hours, osm-id]
"""
import json, os, sys, glob, math, datetime, urllib.request, urllib.parse

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'daten')
MINDEST = 15000          # weniger Apotheken = Abfrage unvollständig -> nichts überschreiben
SERVER = [
    'https://overpass-api.de/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
    'https://overpass.private.coffee/api/interpreter',
]
ABFRAGE = ('[out:json][timeout:300];area["ISO3166-1"="DE"][admin_level=2]->.a;'
           'nwr["amenity"="pharmacy"](area.a);out center tags;')


def hole():
    fehler = []
    for url in SERVER:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({'data': ABFRAGE}).encode(),
                                         headers={'User-Agent': 'apotheken-app/1 (github.com/luperttrading-lab/apotheken)'})
            with urllib.request.urlopen(req, timeout=400) as r:
                return json.load(r)
        except Exception as e:                       # nächster Server
            fehler.append(f'{url}: {e}')
    sys.exit('Kein Overpass-Server lieferte Daten:\n' + '\n'.join(fehler))


def kachel(lat, lon):
    return f'{math.floor(lat * 2)}_{math.floor(lon * 2)}'


def main():
    roh = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else hole()
    els = roh.get('elements', [])
    if len(els) < MINDEST:
        sys.exit(f'Nur {len(els)} Apotheken erhalten (erwartet >= {MINDEST}) – breche ab, Daten bleiben unverändert.')
    kacheln = {}
    for e in els:
        t = e.get('tags', {})
        lat = e.get('lat', (e.get('center') or {}).get('lat'))
        lon = e.get('lon', (e.get('center') or {}).get('lon'))
        if lat is None or lon is None:
            continue
        zeile = [round(lat, 5), round(lon, 5),
                 t.get('name') or t.get('brand') or '',
                 ' '.join(x for x in [t.get('addr:street') or t.get('addr:place'), t.get('addr:housenumber')] if x),
                 t.get('addr:postcode', ''), t.get('addr:city', ''),
                 (t.get('phone') or t.get('contact:phone') or t.get('contact:mobile') or '').split(';')[0].strip(),
                 t.get('website') or t.get('contact:website') or t.get('url') or '',
                 (t.get('opening_hours') or '').strip(),
                 e['type'][0] + str(e['id'])]
        kacheln.setdefault(kachel(lat, lon), []).append(zeile)

    os.makedirs(ZIEL, exist_ok=True)
    for alt in glob.glob(os.path.join(ZIEL, '*_*.json')):
        os.remove(alt)
    for k, zeilen in kacheln.items():
        zeilen.sort(key=lambda z: (z[0], z[1]))
        with open(os.path.join(ZIEL, k + '.json'), 'w', encoding='utf-8') as f:
            json.dump(zeilen, f, ensure_ascii=False, separators=(',', ':'))
    lats = [z[0] for zs in kacheln.values() for z in zs]
    lons = [z[1] for zs in kacheln.values() for z in zs]
    index = {
        'stand': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
        'quelle': 'OpenStreetMap-Mitwirkende, ODbL',
        'anzahl': sum(len(z) for z in kacheln.values()),
        'raster': 0.5,
        'bbox': [min(lats), min(lons), max(lats), max(lons)],
        'kacheln': sorted(kacheln),
    }
    with open(os.path.join(ZIEL, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    groessen = sorted(os.path.getsize(p) for p in glob.glob(os.path.join(ZIEL, '*_*.json')))
    print(f"{index['anzahl']} Apotheken in {len(kacheln)} Kacheln, "
          f"Kachel median {groessen[len(groessen) // 2] // 1024} KB, max {groessen[-1] // 1024} KB, Stand {index['stand']}")


if __name__ == '__main__':
    main()
