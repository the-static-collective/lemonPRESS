import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from fencepost import Parameters, radius_at, run_plan, run_tone
from prusaslicer_hook import annotate


class FencepostTests(unittest.TestCase):
    def test_radius_calculation(self):
        p=Parameters(rpm=45,groove_pitch_mm=.18)
        self.assertAlmostEqual(radius_at(60,p),76-45*.18)

    def test_invalid_radii_fail_closed(self):
        with self.assertRaises(ValueError):
            Parameters(min_radius_mm=75, start_radius_mm=76, rpm=90, groove_pitch_mm=.5).check(10)

    def test_non_finite_rejected(self):
        with self.assertRaises(ValueError):
            Parameters(rpm=float('nan')).check(2)

    def test_tone_and_provenance_and_hook_idempotence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            wav=root/'tone.wav'
            run_tone(wav,2,44100,440)
            o=root/'plan'
            receipt=run_plan(wav,o,Parameters())
            self.assertEqual(receipt['status'],'HOLD_SIMULATION_ONLY')
            self.assertFalse(receipt['cutting_authorized'])
            self.assertFalse(receipt['physical_record_made'])
            self.assertFalse(receipt['motor_commands_generated'])
            self.assertAlmostEqual(receipt['planner']['final_radius_mm'],75.73)
            self.assertIn('<svg', (o/'schematic-spiral.svg').read_text())
            self.assertIn('linear_extrude', (o/'printable-seismograph-trace.scad').read_text())
            gc=root/'example.gcode'
            gc.write_text('G28\nG1 X10 Y10\n')
            self.assertTrue(annotate(gc,o/'receipt.json'))
            initial=gc.read_bytes()
            self.assertFalse(annotate(gc,o/'receipt.json'))
            self.assertEqual(initial,gc.read_bytes())
            self.assertTrue(gc.read_bytes().endswith(b'G28\nG1 X10 Y10\n'))
            tampered=json.loads((o/'receipt.json').read_text())
            tampered['cutting_authorized']=True
            (o/'receipt.json').write_text(json.dumps(tampered))
            with self.assertRaises(ValueError):
                annotate(root/'example2.gcode',o/'receipt.json')

    def test_mono_stereo_and_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            run_tone(p/'tone.wav',0.2,8000,440)
            with self.assertRaises(ValueError):
                run_plan(p/'tone.wav',p/'fail',Parameters(max_duration_s=.1))


if __name__=='__main__':
    unittest.main()
