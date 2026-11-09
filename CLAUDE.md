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
- Feiertage (ab v1.15): Nur 18,2 % der deutschen Einträge nennen PH. Ohne Ergänzung wären am 25.12.2026 11.302
  von 14.011 Apotheken „offen“ gewesen. `mitFeiertagen()` hängt „; PH off“ an, außer bei 24/7 oder sonntags
  offenen Einträgen (65); danach 115 offen, alle 14.011 Einträge weiter lesbar. Heiligabend und Silvester sind
  keine Feiertage; verkürzte Zeiten kennt OpenStreetMap meist nicht.
- Sortierung „Nächste Öffnung“ (ab v1.15) stellt den Filter auf „Alle“, damit auch Apotheken erscheinen, die erst
  am Montag oder nach Feiertagen öffnen (Wunsch 08.11.); Test 24.12. 19:00 → „Öffnet Mo 07:00“ (28.12.).
  Ab v1.16 auch beim Start: Die Sortierung wird gemerkt, der Startfilter „Jetzt offen“ machte die Liste sonst leer.
- Adresssuche/Rückwärtssuche: Nominatim (max. 1 Anfrage/s, nur auf Absenden).
  Nur ein Ortsname („München“) liefert bei Nominatim keine PLZ (addresstype city) → ab v1.9 PLZ per
  Rückwärtssuche am Ortsmittelpunkt (München → 80331, Hamburg → 20095); ohne PLZ zeigte aponet nur die leere Suche.
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
  vermutlich bei jedem Öffnen erneut.
  Ab v1.7 öffnet der Rahmen mit Sprungmarke `#pharmacy-search-result` (aponets Ergebnisliste; bleibt über die
  301-Weiterleitung erhalten) und ist bildschirmhoch. Die weißen Lücken auf aponet sind leere Werbeplätze
  (`div-gpt-ad … adslot`), in fremden Rahmen nicht entfernbar; die Sprungmarke überspringt die zwei großen.
  Ab v1.8: Rahmen-Adresse `notdienstsuche/<PLZ>-<Ort>` (Ort = Gemeinde aus Nominatim; „PLZ-Irgendwas“ findet
  nichts, echte Ortsteile schon) – ohne aponets 301-Umleitung kennt die App die Rahmen-Adresse. Auf dem iPhone
  wuchsen Werbeplätze nach dem Sprung und schoben die Liste weg (Screenshot 08.11. 20:07); daher springt die App
  1,5/3,5/6 s nach dem Laden und 1/3 s nach dem ersten Tipp in den Rahmen (meist „Zustimmen“) erneut, indem sie
  dieselbe Adresse setzt (= Sprung innerhalb der Seite, kein Neuladen). Solange aponets Zustimmungsabfrage offen
  ist, lässt sich deren Seite nicht scrollen.
  Ab v1.13 (ersetzt die Sprung-Wiederholungen aus v1.8): Rahmen ohne `allow-scripts`. aponets Notdienstliste
  kommt fertig vom Server; deren Skripte laden nur Werbung, Karte und Zustimmungsabfrage. Am iPhone sprang die
  Liste trotz erneuter Sprünge weg (Nutzer 08.11. 21:10). Ohne Skripte: keine Werbung, keine Zustimmung, nichts
  verschiebt sich; Karte und erweiterte Suche nur noch über „In Safari öffnen“. Wirkt wie ein Werbeblocker –
  für die private Nutzung gewählt, bei einer Veröffentlichung neu bewerten. Filter „Heute noch offen“ heißt seit v1.5 „Jetzt oder später“
  (= jetzt offen oder öffnet heute noch).

## Gestaltungsregel des Nutzers (08.11.)

Der Bezug einer Suche gehört groß und oben auf den Bildschirm: Wo gesucht wird, muss auf einen Blick erkennbar
sein, nicht als kleine graue Zeile. Umgesetzt ab v1.14 als grüner Kasten „Suche um“ über allen Eingaben
(Straße groß, PLZ/Ort darunter, Quelle GPS oder Adresse); die Statuszeile nennt den Ort ebenfalls
(„… im Umkreis von 10 km um Wettenberg“). Gilt für alle Apps des Nutzers.
Zweite Regel (09.11., „völlig gegen die Design-Regeln“): Bedienleisten bleiben in **einer** Zeile und springen
nicht, wenn sich Zahlen ändern; nichts wird abgeschnitten. Umgesetzt ab v1.18: Filter als dreigeteilte Leiste
(`.filter3`, gleich breite Felder, Zahl klein darunter, `tabular-nums`, feste Höhe 52 px), Beschriftungen gekürzt
(„Noch heute“, „Di offen“), auf schmalen Geräten (≤ 380 px) 13,5 px Schrift; Tagesauswahl „Morgen 10.11.“.
Geprüft auf iPhone SE und iPhone 14 mit zwei- und dreistelligen Zahlen. Offene Apotheken: grüne Klammer links
und rechts (Wunsch 09.11.).

## Startverhalten (ab v1.6, Wunsch des Nutzers 08.11.)

- Jeder Start: 10 km, Fahrstrecke, Filter **„Alle“** (ab v1.17, vorher „Jetzt offen“ – lieferte nachts und
  sonntags leere Listen), Apotheken ohne Zeitangabe ausgeblendet, Reiter Apotheken, Tag Heute. Gemerkt werden nur
  letzter Ort (Rückfall) und Sortierung.
- Grundsatz ab v1.17 (Wunsch 09.11.): erst alles zeigen, die Liste sagt, wer wann offen hat; Filter grenzen nur ein.
  Filterknöpfe tragen die Trefferzahl („Jetzt offen (0)“). Bei „Empfohlen“ und „Nächste Öffnung“
  Zwischenüberschriften nach `gruppe()`: „Jetzt geöffnet“, „Öffnet heute noch“, „Öffnet morgen (Mo 9.11.)“,
  „Öffnet Mo 16.11.“ …; „Empfohlen“ sortiert nach diesem Rang, je Gruppe nach Entfernung. Offene Karten grüner Rand.
- Hat heute im Umkreis nichts offen: Hinweis mit der nächsten jetzt geöffneten Apotheke bis 50 km Luftlinie
  (Kacheln), Knopf „Umkreis auf X km“ (Fahrstrecke grob 1,4 × Luftlinie, max. 30) und Route; sonst Notdienst-Knopf.
- Beim Öffnen wird sofort geortet (`holeStandort(true)`, wie die Standort-Uhr); der gemerkte Ort wird parallel
  gezeigt und durch den Standort ersetzt, sobald er da ist. Fehler beim Start: nur einzeilige Hilfe.
- Ortung in Safari sofort abgelehnt, in der Standort-Uhr (gleiche Domain luperttrading-lab.github.io) gefragt:
  Safari-Freigabe gilt je Domain, die Home-Bildschirm-App hat eine eigene → Nutzer soll die App vom
  Home-Bildschirm öffnen. Die Hilfekarte nennt das als ersten Schritt (nur außerhalb des Home-Bildschirms).

## Tag und Filter (ab v1.11, Wunsch 08.11.)

Wird ein anderer Tag als heute gewählt und steht der Filter auf „Jetzt offen“, stellt die App auf „Am Mo offen“
um; zurück auf heute wieder auf „Jetzt offen“ – nur wenn die App selbst umgestellt hat (`filterAutomatisch`).
Ab v1.12: Steht man im Notdienst-Reiter und wählt einen anderen Tag, wechselt die App auf den Reiter Apotheken
(Notdienst zeigt nur heute) und holt die Liste an den oberen Rand.

## Anzeige nach Sortierung (ab v1.10, Wunsch 08.11.)

Oben rechts in der Karte steht der Wert, nach dem sortiert ist (`sortBadge`): „Schließt 20:00“, „Öffnet 07:00“,
„3,5 km“ (blau), „9 min Auto“; der Jetzt-Status rückt dann in eine Zeile „Jetzt: …“. Derselbe Wert ist im Text
gelb markiert (`mark.sortwert`). Bei „Empfohlen“, „Nächste Öffnung“ und „Name“ bleibt der normale Status.
Die Versionsprüfung vergleicht nur auf „anders“ – „1.10“ nach „1.9“ ist deshalb in Ordnung.

## Testen

Playwright mit iPhone-Maßen und simuliertem Standort. In der Cloud-Sandbox blockiert der Proxy
`overpass-api.de` und Pfade mit `;` (OSRM) für den Browser – das ist die Sandbox, nicht die Dienste.
