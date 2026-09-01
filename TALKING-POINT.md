# Talking Point: Automatisierung im Filesharing-Massenabmahnverfahren

> Hinweis: Es gab kein vorheriges Talking-Point-Dokument im Projekt; dieses wurde als
> fachliche Grundlage für den Prototyp neu formuliert, ausgehend von der Aufgabenbeschreibung.
> Es dient als Diskussionsgrundlage für ein Vorstellungsgespräch, nicht als Rechtsberatung.

## Ausgangslage

Kanzleien, die Filesharing-Urheberrechtsverletzungen für Mandanten (z. B. Gaming-Publisher)
verfolgen, bearbeiten typischerweise eine hohe Fallzahl mit stark standardisiertem Ablauf:
Ermittlung des Anschlussinhabers über den Access-Provider (nach vorherigem
Gestattungsbeschluss gem. § 101 Abs. 9 UrhG), Versand einer Abmahnung, Fristüberwachung der
Reaktion, und je nach Reaktion Fallabschluss, Rückfrage oder gerichtliche Weiterverfolgung.

Der Engpass ist selten die juristische Bewertung des Einzelfalls, sondern die **operative
Bewältigung der Masse**: Fristen dürfen nicht verpasst werden, Standardfälle sollen nicht
unnötig anwaltliche Kapazität binden, und untypische oder streitige Fälle müssen zuverlässig
und schnell an die richtige Stelle eskaliert werden.

## These

Ein Großteil dieses Ablaufs lässt sich als klar strukturierter, nachvollziehbarer
Workflow abbilden — **ohne** dass juristische Entscheidungen automatisiert getroffen werden.
Automatisiert wird die *Triage*, nicht das *Urteil*: Das System sortiert eingehende Reaktionen
regelbasiert in Grün/Gelb/Rot vor, aber jede Entscheidung mit Streitpotenzial (Gelb, Rot)
landet bei einem Menschen.

## Warum regelbasiert statt ML

- **Nachvollziehbarkeit:** Für eine Kanzlei muss jede automatische Fallabschluss-Entscheidung
  im Zweifel erklärbar und auditierbar sein — eine Blackbox-Klassifikation ist hier ein
  Haftungsrisiko, keine Vereinfachung.
- **Geringe Grundmenge an Mustern:** Die Standardreaktionen (Unterlassungserklärung,
  Zahlung, Widerspruch) sind gut abgrenzbar; ein Regelwerk deckt den Großteil der Fälle ab.
- **Erweiterbarkeit bleibt offen:** Die Regel-Engine ist so strukturiert, dass sie später um
  zusätzliche Signalquellen (z. B. ein Klassifikationsmodell als weitere "Regel") ergänzt
  werden kann, ohne die Aufrufer im Triage-Modul anzupassen.

## Warum zentrale Fristverwaltung als eigenes Modul

Fristversäumnisse sind das größte operative Risiko in der Masse. Die Fristberechnung folgt
festen gesetzlichen Regeln (§§ 187-193 BGB, § 222 ZPO) und ist deshalb bewusst als eigenständiges,
wiederverwendbares Modul (`fristenwaechter`) ausgelagert statt in die Falllogik verwoben — jede
Phase, die eine Frist setzt (Abmahnung, Eskalation), ruft dasselbe geprüfte Modul auf.

## Grenzen des Prototyps

- Keine echte Anbindung an Access-Provider, Gerichte oder Mandanten-Systeme.
- Kein echter Versand von Abmahnungen (Ausgabe nur als Markdown/Datei).
- Die Ampel-Klassifizierung ist ein vereinfachtes Demonstrationsregelwerk, kein
  produktionsreifes Textverständnis eingehender Schreiben.
- Alle Testdaten sind fiktiv (Dummy-IPs aus dem RFC-5737-Dokumentationsbereich, erfundene
  Werktitel und Mandanten).
