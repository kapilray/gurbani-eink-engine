from dataclasses import dataclass


@dataclass
class DeviceProfile:
    slug: str
    name: str
    width: int       # physical pixels (portrait)
    height: int      # physical pixels (portrait)
    ppi: int
    size_in: float   # screen diagonal in inches
    brand: str       # 'kindle' or 'kobo'
    color: bool = False  # color e-ink display

    @property
    def font_size_px(self) -> int:
        # ~1.7% of height gives comfortable reading size at device PPI
        return max(18, int(self.height * 0.017))

    @property
    def margin_px(self) -> int:
        return max(30, int(self.width * 0.05))


KINDLE_DEVICES = [
    DeviceProfile('kindle-11-2024',            'Kindle (11th gen, 2024)',           1072, 1448, 300,  6.0, 'kindle'),
    DeviceProfile('kindle-paperwhite-11-2021', 'Kindle Paperwhite (11th gen, 2021)', 1236, 1648, 300, 6.8, 'kindle'),
    DeviceProfile('kindle-paperwhite-12-2024', 'Kindle Paperwhite (12th gen, 2024)', 1264, 1680, 300, 7.0, 'kindle'),
    DeviceProfile('kindle-colorsoft-2024',     'Kindle Colorsoft (2024)',            1264, 1680, 300,  7.0, 'kindle', color=True),
    DeviceProfile('kindle-colorsoft-se-2025',  'Kindle Colorsoft SE (2025)',         1264, 1680, 300,  7.0, 'kindle', color=True),
    DeviceProfile('kindle-oasis-10-2019',      'Kindle Oasis (10th gen, 2019)',      1264, 1680, 300,  7.0, 'kindle'),
    DeviceProfile('kindle-scribe-2-2024',      'Kindle Scribe (2nd gen, 2024)',      1860, 2480, 300, 10.2, 'kindle'),
    DeviceProfile('kindle-scribe-3-2025',      'Kindle Scribe (3rd gen, 2025)',      1980, 2640, 300, 11.0, 'kindle'),
    DeviceProfile('kindle-scribe-colorsoft-2025', 'Kindle Scribe Colorsoft (2025)', 1980, 2640, 300, 11.0, 'kindle', color=True),
]

KOBO_DEVICES = [
    DeviceProfile('kobo-clara-bw-2024',     'Kobo Clara BW (2024)',      1072, 1448, 300,  6.0, 'kobo'),
    DeviceProfile('kobo-clara-colour-2024', 'Kobo Clara Colour (2024)',  1072, 1448, 300,  6.0, 'kobo', color=True),
    DeviceProfile('kobo-libra-2',           'Kobo Libra 2',              1264, 1680, 300,  7.0, 'kobo'),
    DeviceProfile('kobo-libra-colour-2024', 'Kobo Libra Colour (2024)', 1264, 1680, 300,  7.0, 'kobo', color=True),
    DeviceProfile('kobo-sage',              'Kobo Sage',                 1440, 1920, 300,  8.0, 'kobo'),
    DeviceProfile('kobo-forma',             'Kobo Forma',                1440, 1920, 300,  8.0, 'kobo'),
    DeviceProfile('kobo-elipsa-2e',         'Kobo Elipsa 2E',           1404, 1872, 227, 10.3, 'kobo'),
]

ALL_DEVICES = KINDLE_DEVICES + KOBO_DEVICES
