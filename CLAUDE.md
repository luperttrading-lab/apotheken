# Apotheken-App

Home-Bildschirm-Web-App (PWA) auf GitHub Pages: <https://luperttrading-lab.github.io/apotheken/>.
Eine Datei `index.html` (HTML, CSS, JS), dazu `sw.js`, `manifest.webmanifest`, Icons. Kein Bauschritt.

## Bei jeder Änderung

- `const APP_VERSION = '…';` in `index.html` hochzählen (Schreibweise exakt so lassen, die Update-Prüfung
  liest sie per Regex). Der Service Worker holt eigene Dateien „Netz zuerst“, die App prüft beim Öffnen und
  beim Zurückholen aus dem Hintergrund, Tipp auf die Versionsnummer prüft von Hand (Skill „app-update-iphone“).
- Datenabrufe (Overpass, Nominatim, OSRM) nie im Service Worker cachen.

## Datenquellen (geprüft 07.11.2026)

- Apotheken und Öffnungszeiten (ab v1.4): vorberechnete Kacheln `daten/<floor(lat*2)>_<floor(lon*2)>.json`
  (0,5° × 0,5°, 225 Kacheln, Median 8 KB, max. 104 KB) plus `daten/index.json` (Stand, bbox, Kachelliste).
  Gebaut von `tools/daten_bauen.py`, wöchentlich durch `.github/workflows/daten.yml` (montags, auch von Hand).
  Gemessen 07.11.: Liste Wettenberg 0,9 s inkl. Adresssuche, Berlin 30 km (844 Apotheken) 0,6 s.
  Live-Overpass (`around:`) nur noch als Rückfall, wenn der Kreis außerhalb liegt oder Kacheln fehlen.
- Live-Abfrage: OpenStreetMap über Overpass (`amenity=pharmacy`, `around:`), mit
  Ersatzservern. Deutschland: 17.101 Apotheken, 81,9 % mit `opening_hours`.
  Öffentliche Overpass-Server sind zeitweise überlastet (504, Antwortzeiten 16–45 s am 07.11.): deshalb zwei
  Runden über alle Server und Rückfall auf den zuletzt gespeicherten Stand (`localStorage` `apotheke.daten`),
  wenn er den gesuchten Kreis abdeckt (ab v1.1).
- Auswertung der Öffnungszeiten: `opening_hours.js` 3.15.0 von jsDelivr (`/+esm`, ~90 KB über die Leitung).
  Alle 14.011 deutschen Einträge werden fehlerfrei gelesen; Feiertage nach Bundesland über die
  Nominatim-Adresse (`ISO3166-2-lvl4`).
- Adresssuche/Rückwärtssuche: Nominatim (max. 1 Anfrage/s, nur auf Absenden).
  Nominatim hat keine Tippfehler-Toleranz („35435 Wettenebrg“ → nichts). Ab v1.2 Rückfall: ohne Wort nach der
  PLZ → bis zur PLZ → nur PLZ, je 1,1 s Abstand; ab dem zweiten Versuch nur Treffer mit genau dieser PLZ
  (sonst fand „Musterweg, 35435“ einen Musterweg in 34302). Gemeinde vor Ortsteil anzeigen.
- Standort: `getCurrentPosition` direkt im Tipp aufrufen, ohne `await` davor. Ob iOS die Frage zeigt, entscheidet
  das Telefon (Safari → Website-Einstellungen → Standort bzw. Ortungsdienste → Safari-Websites); eine gesperrte
  Frage kann keine Webseite erzwingen. Ablehnung in < 1,2 s heißt: Frage wurde gar nicht gezeigt → Hilfekarte.
- Fahrstrecke/-zeit: OSRM-Tabelle (`router.project-osrm.org`, Ersatz `routing.openstreetmap.de`), 99 Ziele je
  Anfrage, ohne Verkehrslage. Demo-Server, nur für privaten Gebrauch; bei Veröffentlichung eigenen Anbieter.
- Notdienst: Die tagesaktuellen Daten vertreibt Avoxa im Auftrag der Bundesapothekerkammer nur gegen Lizenz
  (apotheken-notdienstdaten.de). Frei erlaubt ist der Link `https://www.aponet.de/notdienstsuche/<PLZ>`.
  aponet nicht auslesen. Hotline 0800 00 22833 (Festnetz, kostenlos), 22833 vom Handy (max. 69 ct/Min.).
  Ab v1.5 ist die aponet-Seite im Notdienst-Reiter eingebettet (`iframe`, erst beim Öffnen des Reiters geladen,
  `sandbox` ohne Top-Navigation). aponet sendet weder CORS- noch Frame-Sperre (geprüft 08.11.). Davor steht deren
  Zustimmungsabfrage („Kostenfrei mit Werbung“); Safari speichert Cookies eingebetteter Seiten nicht, daher
  vermutlich bei jedem Öffnen erneut. Filter „Heute noch offen“ heißt seit v1.5 „Jetzt oder später“
  (= jetzt offen oder öffnet heute noch).

## Testen

Playwright mit iPhone-Maßen und simuliertem Standort. In der Cloud-Sandbox blockiert der Proxy
`overpass-api.de` und Pfade mit `;` (OSRM) für den Browser – das ist die Sandbox, nicht die Dienste.
