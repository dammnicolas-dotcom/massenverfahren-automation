"""Tests für zustaendigkeit_checker.py (§ 104a UrhG, § 23 Nr. 1 GVG, § 78 Abs. 1 ZPO)."""

import unittest

from app.zustaendigkeit.zustaendigkeit_checker import (
    GRENZWERT_AMTSGERICHT_EUR,
    pruefe_zustaendigkeit,
)


class WohnsitzgerichtTest(unittest.TestCase):
    """Natürliche Person, keine gewerbliche Nutzung -> § 104a UrhG greift."""

    def test_niedriger_streitwert_amtsgericht_kein_anwaltszwang(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True, gewerbliche_nutzung=False, streitwert=850.0
        )
        self.assertEqual(ergebnis.gerichtsstand_norm, "§ 104a UrhG")
        self.assertIn("Amtsgericht", ergebnis.zustaendiges_gericht)
        self.assertFalse(ergebnis.anwaltszwang)
        self.assertEqual(ergebnis.rechtsgrundlage_anwaltszwang, "§ 78 Abs. 1 ZPO")

    def test_hoher_streitwert_landgericht_mit_anwaltszwang(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True,
            gewerbliche_nutzung=False,
            streitwert=GRENZWERT_AMTSGERICHT_EUR + 1000.0,
        )
        self.assertEqual(ergebnis.gerichtsstand_norm, "§ 104a UrhG")
        self.assertIn("Landgericht", ergebnis.zustaendiges_gericht)
        self.assertTrue(ergebnis.anwaltszwang)

    def test_plz_ist_nur_dokumentation_und_aendert_ergebnis_nicht(self):
        ohne_plz = pruefe_zustaendigkeit(True, False, 850.0)
        mit_plz = pruefe_zustaendigkeit(True, False, 850.0, wohnsitz_beklagter_plz="10115")
        self.assertEqual(ohne_plz.gerichtsstand_norm, mit_plz.gerichtsstand_norm)
        self.assertEqual(ohne_plz.anwaltszwang, mit_plz.anwaltszwang)
        self.assertIn("10115", mit_plz.kurzbegruendung)


class FliegenderGerichtsstandTest(unittest.TestCase):
    """Keine natürliche Person oder gewerbliche Nutzung -> § 104a UrhG greift nicht."""

    def test_juristische_person_trotz_privater_nutzung(self):
        # ist_natuerliche_person=False dominiert unabhängig von gewerbliche_nutzung.
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=False, gewerbliche_nutzung=False, streitwert=850.0
        )
        self.assertEqual(ergebnis.gerichtsstand_norm, "§ 32 ZPO")
        self.assertIn("keine natürliche Person", ergebnis.kurzbegruendung)

    def test_gewerbliche_nutzung_durch_natuerliche_person(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True, gewerbliche_nutzung=True, streitwert=850.0
        )
        self.assertEqual(ergebnis.gerichtsstand_norm, "§ 32 ZPO")
        self.assertIn("gewerbliche/berufliche Nutzung", ergebnis.kurzbegruendung)

    def test_fliegender_gerichtsstand_niedriger_streitwert_amtsgericht(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True, gewerbliche_nutzung=True, streitwert=850.0
        )
        self.assertIn("Amtsgericht", ergebnis.zustaendiges_gericht)
        self.assertFalse(ergebnis.anwaltszwang)

    def test_fliegender_gerichtsstand_hoher_streitwert_landgericht(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=False,
            gewerbliche_nutzung=False,
            streitwert=GRENZWERT_AMTSGERICHT_EUR + 1000.0,
        )
        self.assertIn("Landgericht", ergebnis.zustaendiges_gericht)
        self.assertTrue(ergebnis.anwaltszwang)


class StreitwertGrenzeTest(unittest.TestCase):
    """Grenzfälle rund um GRENZWERT_AMTSGERICHT_EUR (aktuell 5.000 EUR, § 23 Nr. 1 GVG)."""

    def test_streitwert_exakt_grenzwert_ist_landgericht(self):
        # ">=": bei exakt 5.000 EUR bereits Landgericht (Spezifikation, Grenzfall).
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True,
            gewerbliche_nutzung=False,
            streitwert=GRENZWERT_AMTSGERICHT_EUR,
        )
        self.assertIn("Landgericht", ergebnis.zustaendiges_gericht)
        self.assertTrue(ergebnis.anwaltszwang)

    def test_streitwert_knapp_unter_grenzwert_ist_amtsgericht(self):
        ergebnis = pruefe_zustaendigkeit(
            ist_natuerliche_person=True,
            gewerbliche_nutzung=False,
            streitwert=GRENZWERT_AMTSGERICHT_EUR - 0.01,
        )
        self.assertIn("Amtsgericht", ergebnis.zustaendiges_gericht)
        self.assertFalse(ergebnis.anwaltszwang)


class ValidierungTest(unittest.TestCase):
    def test_negativer_streitwert_wirft_fehler(self):
        with self.assertRaises(ValueError):
            pruefe_zustaendigkeit(ist_natuerliche_person=True, gewerbliche_nutzung=False, streitwert=-1.0)


if __name__ == "__main__":
    unittest.main()
