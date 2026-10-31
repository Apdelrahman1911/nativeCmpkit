"""One new lexical ownership regression; zero Android/Coil/bitmap execution."""
from pathlib import Path
import sys
import unittest
SOURCE = Path(sys.argv.pop(1))
METHODS = (
    'defaultPngDecodeStreamsUnknownSizeBinaryAndPreservesEveryPixel',
    'defaultJpegDecodeReplaysBoundsAndExifForRotationAndReflection',
)
class BitmapOwnershipSourceRegression(unittest.TestCase):
    def source(self):
        return SOURCE.read_text()

    def test_successful_native_bitmaps_are_owned_before_result_contract_assertions(self):
        source = self.source()
        marker = 'bitmap(assertIs<BitmapImage>(result.image).bitmap) { decoded ->'
        contract = 'assertEquals(DataSource.DISK, result.dataSource); assertFalse(result.isSampled)'
        for method in METHODS[:2]:
            with self.subTest(method=method):
                body = source.split('@Test fun ' + method, 1)[1].split('@Test fun ', 1)[0]
                start = body.index(marker) + len(marker)
                depth, end = 1, start
                while depth and end < len(body):
                    depth += (body[end] == '{') - (body[end] == '}')
                    end += 1
                self.assertEqual(0, depth, 'The concrete bitmap ownership block must close')
                self.assertIn(contract, body[start:end - 1],
                              'Any result-contract assertion must run inside deterministic bitmap recycling')

if __name__ == '__main__':
    unittest.main()
