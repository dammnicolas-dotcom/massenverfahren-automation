"""Tests für frist_berechnung.py (§ 222 ZPO i.V.m. §§ 187-193 BGB)."""

import unittest
from datetime import date

from app.fristverwaltung.frist_berechnung import berechne_frist, _add_months, _letzter_tag_im_monat


class TagesfristTest(unittest.TestCase):
    def test_tagesfrist_ohne_verschiebung(self):
        # Montag 3.8.2026 + 14 Tage -> Montag 17.8.2026 (kein Wochenende/Feiertag)
        self.assertEqual(
            berechne_frist(date(2026, 8, 3), tage=14),
            date(2026, 8, 17),
        )

    def test_tagesfrist_mit_wochenend_verschiebung(self):
        # Ereignis 3.8.2026 + 5 Tage -> rohes Fristende 8.8.2026 ist ein Samstag,
        # § 222 Abs. 2 ZPO verschiebt auf den nächsten Werktag (Montag 10.8.2026)
        self.assertEqual(
            berechne_frist(date(2026, 8, 3), tage=5),
            date(2026, 8, 10),
        )


class WochenfristTest(unittest.TestCase):
    def test_wochenfrist_entspricht_tage_mal_sieben(self):
        self.assertEqual(
            berechne_frist(date(2026, 8, 3), wochen=2),
            berechne_frist(date(2026, 8, 3), tage=14),
        )


class MonatsfristTest(unittest.TestCase):
    def test_monatsfrist_normal(self):
        self.assertEqual(
            berechne_frist(date(2026, 8, 3), monate=1),
            date(2026, 9, 3),
        )

    def test_monatsfrist_ueber_jahreswechsel(self):
        self.assertEqual(
            berechne_frist(date(2026, 12, 15), monate=1),
            date(2027, 1, 15),
        )

    def test_monatsfrist_sonderfall_kein_31_im_zielmonat(self):
        # § 188 Abs. 3 BGB: 31.1.2026 (kein Schaltjahr) + 1 Monat -> Fristende
        # rechnerisch 28.2.2026 (Samstag), verschoben auf Montag 2.3.2026
        self.assertEqual(
            berechne_frist(date(2026, 1, 31), monate=1),
            date(2026, 3, 2),
        )

    def test_monatsfrist_sonderfall_schaltjahr(self):
        # 2028 ist ein Schaltjahr -> Zielmonat Februar hat 29 Tage
        self.assertEqual(
            berechne_frist(date(2028, 1, 31), monate=1),
            date(2028, 2, 29),
        )


class FeiertagTest(unittest.TestCase):
    def test_verschiebung_bei_feiertag(self):
        # Rohes Fristende 24.9.2026 ist ein Donnerstag (kein Wochenende);
        # als Feiertag markiert, verschiebt sich das Ende auf Freitag 25.9.2026
        self.assertEqual(
            berechne_frist(date(2026, 9, 19), tage=5),
            date(2026, 9, 24),
        )
        self.assertEqual(
            berechne_frist(date(2026, 9, 19), tage=5, feiertage={date(2026, 9, 24)}),
            date(2026, 9, 25),
        )

    def test_verschiebung_ueber_feiertag_und_wochenende_hinweg(self):
        # Rohes Fristende 3.10.2026 (Samstag) faellt zusaetzlich auf einen
        # Feiertag; beide Bedingungen fuehren gemeinsam zur Verschiebung
        # auf den naechsten Werktag Montag 5.10.2026
        self.assertEqual(
            berechne_frist(date(2026, 9, 19), tage=14, feiertage={date(2026, 10, 3)}),
            date(2026, 10, 5),
        )


class ValidierungTest(unittest.TestCase):
    def test_fehler_wenn_keine_einheit_angegeben(self):
        with self.assertRaises(ValueError):
            berechne_frist(date(2026, 1, 1))

    def test_fehler_wenn_mehrere_einheiten_angegeben(self):
        with self.assertRaises(ValueError):
            berechne_frist(date(2026, 1, 1), tage=1, wochen=1)


class AddMonthsHelperTest(unittest.TestCase):
    def test_letzter_tag_im_monat_dezember(self):
        self.assertEqual(_letzter_tag_im_monat(2026, 12), 31)

    def test_letzter_tag_im_monat_februar_schaltjahr(self):
        self.assertEqual(_letzter_tag_im_monat(2028, 2), 29)

    def test_add_months_jahreswechsel(self):
        self.assertEqual(_add_months(date(2026, 12, 15), 1), date(2027, 1, 15))

    def test_add_months_clamp_auf_monatsende(self):
        self.assertEqual(_add_months(date(2026, 1, 31), 1), date(2026, 2, 28))


if __name__ == "__main__":
    unittest.main()
