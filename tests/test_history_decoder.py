"""Regression tests for the BLE history packet decoder.

The decoder is extracted from coordinator.py's AST so these protocol tests
can run without installing the full Home Assistant runtime.
"""

import ast
import unittest
from pathlib import Path


def load_decoder():
    source_path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "oregon_idtw21r"
        / "coordinator.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "HISTORY_CHANNELS"
            for target in node.targets
        ):
            selected.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_decode_history_packet":
            selected.append(node)

    module = ast.Module(body=selected, type_ignores=[])
    namespace = {}
    exec(compile(module, str(source_path), "exec"), namespace)
    return namespace["_decode_history_packet"]


decode_history_packet = load_decoder()


class HistoryDecoderTests(unittest.TestCase):
    def test_all_captured_indoor_packets_with_0x31_terminator(self):
        packets = [
            "00 24 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31",
            "00 29 c8 00 31 c8 00 31 c8 00 30 c9 00 30 ca 00 30 31",
            "00 2e cc 00 2f d4 00 2e e9 00 2d e9 00 31 cc 00 30 31",
            "00 33 ce 00 31 cf 00 30 cb 00 2f cb 00 2f cd 00 2f 31",
            "00 38 cf 00 2f d6 00 2f d5 00 30 d2 00 30 ce 00 30 31",
            "00 3d cc 00 30 cb 00 30 ca 00 30 c8 00 30 c8 00 31 31",
            "00 42 c8 00 30 c8 00 30 c8 00 30 c8 00 30 c7 00 30 31",
        ]
        expected_first_samples = [
            (20.7, 46),
            (20.0, 49),
            (20.4, 47),
            (20.6, 49),
            (20.7, 47),
            (20.4, 48),
            (20.0, 48),
        ]

        for offset, (raw, expected_sample) in enumerate(
            zip(packets, expected_first_samples, strict=True)
        ):
            with self.subTest(packet=offset):
                packet = bytes.fromhex(raw)
                decoded = decode_history_packet(packet)
                self.assertIsNotNone(decoded)
                channel, start_index, samples = decoded
                self.assertEqual(channel, 0x00)
                self.assertEqual(start_index, 0x24 + offset * 5)
                self.assertEqual(len(samples), 5)
                self.assertEqual(samples[0], expected_sample)

    def test_existing_terminators_remain_supported(self):
        base = bytearray.fromhex(
            "00 01 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31"
        )
        for terminator in (0x01, 0x26, 0x31):
            with self.subTest(terminator=terminator):
                packet = bytes(base[:-1] + bytes([terminator]))
                self.assertIsNotNone(decode_history_packet(packet))

    def test_unknown_terminator_is_rejected(self):
        packet = bytearray.fromhex(
            "00 24 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31"
        )
        packet[-1] = 0x32
        self.assertIsNone(decode_history_packet(bytes(packet)))

    def test_wrong_packet_length_is_rejected(self):
        packet = bytes.fromhex(
            "00 24 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31"
        )
        self.assertIsNone(decode_history_packet(packet[:-1]))


if __name__ == "__main__":
    unittest.main()
