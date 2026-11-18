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
        elif isinstance(node, ast.FunctionDef) and node.name in {
            "_history_humidity_value",
            "_decode_history_packet",
        }:
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
        expected_samples = [
            [(20.7, 46), (20.5, 47), (20.3, 48), (20.2, 48), (20.1, 49)],
            [(20.0, 49), (20.0, 49), (20.0, 48), (20.1, 48), (20.2, 48)],
            [(20.4, 47), (21.2, 46), (23.3, 45), (23.3, 49), (20.4, 48)],
            [(20.6, 49), (20.7, 48), (20.3, 47), (20.3, 47), (20.5, 47)],
            [(20.7, 47), (21.4, 47), (21.3, 48), (21.0, 48), (20.6, 48)],
            [(20.4, 48), (20.3, 48), (20.2, 48), (20.0, 48), (20.0, 49)],
            [(20.0, 48), (20.0, 48), (20.0, 48), (20.0, 48), (19.9, 48)],
        ]

        for offset, (raw, expected_packet_samples) in enumerate(
            zip(packets, expected_samples, strict=True)
        ):
            with self.subTest(packet=offset):
                packet = bytes.fromhex(raw)
                decoded = decode_history_packet(packet)
                self.assertIsNotNone(decoded)
                channel, start_index, samples = decoded
                self.assertEqual(channel, 0x00)
                self.assertEqual(start_index, 0x24 + offset * 5)
                self.assertEqual(len(samples), 5)
                self.assertEqual(samples, expected_packet_samples)

    def test_channel_3_0x4a_packet_with_missing_humidity(self):
        packet = bytes.fromhex(
            "12 01 44 00 7f 44 00 7f 46 00 7f 46 00 7f 46 00 7f 4a"
        )
        decoded = decode_history_packet(packet)
        self.assertIsNotNone(decoded)
        channel, start_index, samples = decoded
        self.assertEqual(channel, 0x12)
        self.assertEqual(start_index, 1)
        self.assertEqual(
            samples,
            [(6.8, None), (6.8, None), (7.0, None), (7.0, None), (7.0, None)],
        )

    def test_observed_trailing_bytes_are_ignored(self):
        base = bytearray.fromhex(
            "00 01 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31"
        )
        for trailing_byte in (0x01, 0x26, 0x31, 0x3D, 0x48, 0x49, 0x4A, 0x99):
            with self.subTest(trailing_byte=trailing_byte):
                packet = bytes(base[:-1] + bytes([trailing_byte]))
                decoded = decode_history_packet(packet)
                self.assertIsNotNone(decoded)
                self.assertEqual(decoded[0], 0x00)
                self.assertEqual(decoded[1], 0x01)
                self.assertEqual(
                    decoded[2],
                    [(20.7, 46), (20.5, 47), (20.3, 48), (20.2, 48), (20.1, 49)],
                )


    def test_captured_0x3d_packets_decode_for_all_channels(self):
        packets = [
            (
                "10 01 76 00 40 74 00 41 73 00 43 72 00 46 6e 00 49 3d",
                0x10,
                1,
                [(11.8, 64), (11.6, 65), (11.5, 67), (11.4, 70), (11.0, 73)],
            ),
            (
                "11 01 6c 00 42 62 00 43 61 00 44 61 00 47 5f 00 4a 3d",
                0x11,
                1,
                [(10.8, 66), (9.8, 67), (9.7, 68), (9.7, 71), (9.5, 74)],
            ),
            (
                "00 01 d2 00 31 cf 00 30 d0 00 32 cf 00 32 cc 00 32 3d",
                0x00,
                1,
                [(21.0, 49), (20.7, 48), (20.8, 50), (20.7, 50), (20.4, 50)],
            ),
        ]

        for raw, expected_channel, expected_index, expected_samples in packets:
            with self.subTest(channel=expected_channel):
                decoded = decode_history_packet(bytes.fromhex(raw))
                self.assertIsNotNone(decoded)
                channel, start_index, samples = decoded
                self.assertEqual(channel, expected_channel)
                self.assertEqual(start_index, expected_index)
                self.assertEqual(samples, expected_samples)


    def test_captured_0x48_packets_decode_for_all_channels(self):
        packets = [
            ("10 01 70 00 40 71 00 40 71 00 40 72 00 41 73 00 41 48", 0x10, 1,
             [(11.2, 64), (11.3, 64), (11.3, 64), (11.4, 65), (11.5, 65)]),
            ("11 01 ff 7f 7f 6b 00 3f 6c 00 3f 6e 00 3f 72 00 3f 48", 0x11, 1,
             [(None, None), (10.7, 63), (10.8, 63), (11.0, 63), (11.4, 63)]),
            ("00 01 ce 00 33 cf 00 33 d1 00 33 d4 00 34 d5 00 33 48", 0x00, 1,
             [(20.6, 51), (20.7, 51), (20.9, 51), (21.2, 52), (21.3, 51)]),
        ]
        for raw, expected_channel, expected_index, expected_samples in packets:
            with self.subTest(channel=expected_channel):
                decoded = decode_history_packet(bytes.fromhex(raw))
                self.assertIsNotNone(decoded)
                channel, start_index, samples = decoded
                self.assertEqual(channel, expected_channel)
                self.assertEqual(start_index, expected_index)
                self.assertEqual(samples, expected_samples)


    def test_channel_3_history_accepts_0x4a_terminator_and_missing_humidity(self):
        """Channel 3 temperature history decodes with its observed 0x4A terminator."""
        packet = bytes.fromhex(
            "12 01 5f 00 7f 60 00 7f 61 00 7f 62 00 7f 63 00 7f 4a"
        )
        decoded = decode_history_packet(packet)
        self.assertIsNotNone(decoded)
        channel, start_index, samples = decoded
        self.assertEqual(channel, 0x12)
        self.assertEqual(start_index, 1)
        self.assertEqual(
            samples,
            [
                (9.5, None),
                (9.6, None),
                (9.7, None),
                (9.8, None),
                (9.9, None),
            ],
        )


    def test_channel_3_history_preserves_available_humidity(self):
        """Channel 3 humidity is decoded when a paired sensor provides it."""
        packet = bytes.fromhex(
            "12 01 5f 00 40 60 00 41 61 00 42 62 00 43 63 00 44 4a"
        )
        decoded = decode_history_packet(packet)
        self.assertIsNotNone(decoded)
        self.assertEqual(
            decoded[2],
            [(9.5, 64), (9.6, 65), (9.7, 66), (9.8, 67), (9.9, 68)],
        )

    def test_wrong_packet_length_is_rejected(self):
        packet = bytes.fromhex(
            "00 24 cf 00 2e cd 00 2f cb 00 30 ca 00 30 c9 00 31 31"
        )
        self.assertIsNone(decode_history_packet(packet[:-1]))
        self.assertIsNone(decode_history_packet(packet + bytes([0])))


    def test_captured_channel_1_packet_with_0x4a(self):
        """Decode a real channel 1 packet from the 2026-11-18 0x4A capture."""
        packet = bytes.fromhex(
            "10 01 6e 00 40 6e 00 40 70 00 40 71 00 40 71 00 40 4a"
        )
        decoded = decode_history_packet(packet)
        self.assertIsNotNone(decoded)
        channel, start_index, samples = decoded
        self.assertEqual(channel, 0x10)
        self.assertEqual(start_index, 1)
        self.assertEqual(
            samples,
            [(11.0, 64), (11.0, 64), (11.2, 64), (11.3, 64), (11.3, 64)],
        )

if __name__ == "__main__":
    unittest.main()
