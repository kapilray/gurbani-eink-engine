# fetcher

Pulls Gurbani from the Shabad OS SQLite database and outputs clean Unicode Gurmukhi JSON. The current implementation fetches the complete Japji Sahib (`bani_id = 1`). The architecture is designed to produce **any Bani** from the database — a single fetcher script per publication, all sharing the same normalization and output schema.

## Files

| File | Purpose |
|------|---------|
| `database.sqlite` | Shabad OS DB v4.8.7 — 151MB, source of truth |
| `fetch_japji.js` | Node.js script: queries DB → converts ASCII → normalizes → writes JSON |
| `japji_full.json` | Generated output: 39 pauris, 385 lines |
| `fetcher.py` | Python entry point: auto-regenerates JSON if DB is newer, returns list of pauris |

## Data Flow

```
database.sqlite
    ↓  better-sqlite3
bani_lines JOIN lines WHERE bani_id = 1 (Japji Sahib)
    ↓  ORDER BY order_id
ASCII Gurmukhi text (Shabad OS encoding)
    ↓  @shabados/gurmukhi-utils toUnicode()
Unicode Gurmukhi
    ↓  normalizeVowels()
Standard Unicode Gurmukhi (oora/ira forms → independent vowels)
    ↓  strip vishraam markers (; . ,)
japji_full.json
```

## Normalization

The Shabad OS database stores text in an ASCII encoding. After `toUnicode()` conversion, some vowels use legacy carrier forms that can render as two visible characters in some fonts:

| Raw form | Normalized | Meaning |
|----------|-----------|---------|
| `ੳੁ` | `ਉ` | independent u |
| `ੳੂ` | `ਊ` | independent uu |
| `ੳੋ` | `ਓ` | independent o |
| `ੳੌ` | `ਔ` | independent au |
| `ੲਿ` | `ਇ` | independent i |
| `ੲੀ` | `ਈ` | independent ii |
| `ੲੇ` | `ਏ` | independent e |
| `ੲੈ` | `ਐ` | independent ai |
| `ਅਾ` | `ਆ` | independent aa |
| `ਅੈ` | `ਐ` | independent ai (alternate) |

## JSON Schema

```json
[
  {
    "pauri": 0,
    "shabad_id": "DMP",
    "lines": [
      { "type": "manglacharan", "text": "ੴ ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ..." },
      { "type": "sirlekh",      "text": "॥ ਜਪੁ ॥" },
      { "type": "pankti",       "text": "ਆਦਿ ਸਚੁ ਜੁਗਾਦਿ ਸਚੁ ॥" }
    ]
  }
]
```

Line types: `manglacharan` · `sirlekh` · `rahao` · `pankti`

## Planned

Connect to the live Shabad OS API to fetch arbitrary Shabads by ID, enabling any Bani — not just Japji Sahib.
