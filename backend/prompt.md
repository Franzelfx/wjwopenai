Bitte analysiere den Inhalt des Bildes und gib die Daten ausschließlich im folgenden **JSON-Format** zurück. Es sollen **keine zusätzlichen Informationen** oder Erläuterungen gegeben werden, **nur das JSON**.

**Beachte die folgenden Vorgaben:**

1. **Zulässige Gemarkungsnamen**: Nur die unten aufgeführten Gemarkungsnamen dürfen verwendet werden. Alle anderen Orts- und Gemarkungsnamen sind zu ignorieren oder zu entfernen.

   - Ebhausen
   - Ebhausen-Ebershardt
   - Ebhausen-Rotfelden
   - Ebhausen-Wenden
   - Haiterbach
   - Haiterbach-Altnuifra
   - Haiterbach-Beihingen
   - Haiterbach-Oberschwandorf
   - Haiterbach-Uni.Schwandorf
   - Jettingen-Oberjettingen
   - Nagold
   - Nagold-Emmingen
   - Nagold-Gündringen
   - Nagold-Hochdorf
   - Nagold-Iselshausen
   - Nagold-Mindersbach
   - Nagold-Pfrondorf
   - Nagold-Schietingen
   - Nagold-Vollmaringen
   - Rohrdorf

2. **Leere Felder**: Wenn eine Information nicht aus dem Bild extrahiert werden kann, lasse das Feld leer oder markiere es mit dem Stichwort `"unbekannt"`. Dieses Stichwort dient dazu, die leeren Felder später leichter in Excel zu bearbeiten.

3. **Erlaubte Informationen**: Verwende ausschließlich die unten aufgeführten Begriffe als Schlüssel für die JSON-Ausgabe. Die Begriffe in Klammern sind alternative Schreibweisen, wie sie im Bild vorkommen können, und sollen auf die standardisierten Begriffe abgebildet werden.

   - `"Dateiname"` (Barcode)
   - `"Aktenkürzel"`
   - `"Jahreszahl"` (Jahr, Jahrgang, Baujahr)
   - `"Fortlaufende Nummer"` (Aktenzeichen, Aktennummer, BGV, BER, BÜW, BTB, BTB. Nr., Bautagebuch Nr., Baugenehmigungsverfahren, vereinfachtes BGV, Bauüberwachung)
   - `"Ort"` (Bauort, Stadt, Ortschaft)
   - `"Straße Hausnummer"` (Bauvorhaben, Grundstück, Baugrundstück, Weg, Straße, Anschrift, Adresse)
   - `"Hausnummer"` (Hausadresse, Nummer des Gebäudes)
   - `"Gemarkung"` (Flur, Flurbezeichnung)
   - `"Flurstücknummer"` (Parzellennummer, Fl.St., Flst., Flurnummer, Flst.Nr., Flurstück, Parz., Parz.Nr.)
   - `"Bezeichnung"` (Bauvorhaben, Titel, Name)

4. **Beispiel JSON-Ausgabe**:

   ```json
   {
     "Dateiname": "12345678",
     "Aktenkürzel": "AK-789",
     "Jahreszahl": "2022",
     "Fortlaufende Nummer": "BGV-456",
     "Ort": "Nagold",
     "Straße Hausnummer": "Hauptstraße 12",
     "Hausnummer": "12",
     "Gemarkung": "Nagold-Emmingen",
     "Flurstücknummer": "Flst.1234",
     "Bezeichnung": "Wohnhaus Neubau"
   }

5. **Anforderungen**:

Filterung von Gemarkungen: Es dürfen nur die oben aufgeführten Gemarkungsnamen akzeptiert werden. Alle anderen sind zu ignorieren.
Einhaltung des JSON-Formats: Achte darauf, dass die JSON-Struktur korrekt ist und keine zusätzlichen Informationen oder Kommentare außerhalb des JSON-Blocks ausgegeben werden.