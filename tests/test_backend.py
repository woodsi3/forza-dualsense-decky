import struct
import unittest

from forza_haptics.config import Settings
from forza_haptics.effects import EffectEngine
from forza_haptics.hidraw import USB, BLUETOOTH, assemble_report
from forza_haptics.telemetry import decode_packet
from forza_haptics.triggers import clear_effect, resistance


class BackendTests(unittest.TestCase):
    def make_packet(self):
        raw = bytearray(324)
        struct.pack_into("<iIfff", raw, 0, 1, 1234, 8000.0, 900.0, 7600.0)
        struct.pack_into("<4f", raw, 84, 0.5, 0.6, 0.1, 0.1)
        struct.pack_into("<4f", raw, 180, 0.4, 0.5, 0.1, 0.1)
        struct.pack_into("<f", raw, 256, 25.0)
        raw[315] = 220
        raw[316] = 180
        raw[318] = 0
        raw[319] = 4
        return bytes(raw)

    def test_decode(self):
        state = decode_packet(self.make_packet())
        self.assertTrue(state.is_racing)
        self.assertEqual(state.gear, 4)
        self.assertAlmostEqual(state.speed_kmh, 90.0)
        self.assertGreater(state.rpm_ratio, 0.9)

    def test_report_lengths(self):
        clear = clear_effect()
        force = resistance(0, 75)
        self.assertEqual(len(assemble_report(USB, force, clear)), 64)
        self.assertEqual(len(assemble_report(BLUETOOTH, force, clear)), 78)

    def test_effects(self):
        settings = Settings()
        state = decode_packet(self.make_packet())
        engine = EffectEngine(settings)
        left, right = engine.compute(state)
        self.assertEqual(len(left.pack()), 11)
        self.assertEqual(len(right.pack()), 11)
        self.assertIn(engine.status.brake_mode, ("ABS vibration", "pedal resistance"))


if __name__ == "__main__":
    unittest.main()
