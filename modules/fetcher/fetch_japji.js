/**
 * Fetches the full Japji Sahib from the Shabad OS SQLite database,
 * converts ASCII Gurmukhi → Unicode, and writes japji_full.json.
 *
 * Usage: node fetch_japji.js
 */

const Database   = require('better-sqlite3')
const { toUnicode } = require('@shabados/gurmukhi-utils')
const path       = require('path')
const fs         = require('fs')

const DB_PATH  = path.join(__dirname, 'database.sqlite')
const OUT_PATH = path.join(__dirname, 'japji_full.json')

const db = new Database(DB_PATH, { readonly: true })

// Normalize legacy oora/ira+matra forms → standard independent vowels
// e.g. ੳੁ → ਉ, ੲਿ → ਇ, ਅਾ → ਆ
function normalizeVowels(text) {
  return text
    // Oora-based independent vowels
    .replace(/ੳੁ/g, 'ਉ')   // oora + u matra  → ਉ
    .replace(/ੳੂ/g, 'ਊ')   // oora + uu matra → ਊ
    .replace(/ੳੋ/g, 'ਓ')   // oora + o matra  → ਓ
    .replace(/ੳੌ/g, 'ਔ')   // oora + au matra → ਔ
    // Ira-based independent vowels
    .replace(/ੲਿ/g, 'ਇ')   // ira  + i matra  → ਇ
    .replace(/ੲੀ/g, 'ਈ')   // ira  + ii matra → ਈ
    .replace(/ੲੇ/g, 'ਏ')   // ira  + e matra  → ਏ
    .replace(/ੲੈ/g, 'ਐ')   // ira  + ai matra → ਐ
    // Airaa-based
    .replace(/ਅਾ/g, 'ਆ')   // a    + aa matra → ਆ
    .replace(/ਅੈ/g, 'ਐ')   // a    + ai matra → ਐ
    .replace(/ਅੇ/g, 'ਏ')   // a    + e  matra → ਏ
}

// Strip vishraam (pause) markers: ; . , which are pronunciation guides, not text
function clean(ascii) {
  return normalizeVowels(
    toUnicode(ascii)
      .replace(/[;.,]/g, '')  // remove vishraam markers
      .replace(/\s+/g, ' ')  // collapse any double spaces
      .trim()
  )
}

const TYPE_NAMES = { 1: 'manglacharan', 2: 'sirlekh', 3: 'rahao', 4: 'pankti' }

const rows = db.prepare(`
  SELECT l.id, l.shabad_id, l.gurmukhi, l.type_id, l.order_id
  FROM bani_lines bl
  JOIN lines l ON bl.line_id = l.id
  WHERE bl.bani_id = 1
  ORDER BY l.order_id
`).all()

// Group into shabads preserving order
const shabadMap = new Map()
const shabadOrder = []

for (const row of rows) {
  if (!shabadMap.has(row.shabad_id)) {
    shabadMap.set(row.shabad_id, [])
    shabadOrder.push(row.shabad_id)
  }
  shabadMap.get(row.shabad_id).push({
    type: TYPE_NAMES[row.type_id] || 'pankti',
    text: clean(row.gurmukhi)
  })
}

const pauris = shabadOrder.map((shabadId, idx) => ({
  pauri: idx,          // 0 = Mool Mantar, 1–38 = Pauris, 39 = Mundavani/Salok
  shabad_id: shabadId,
  lines: shabadMap.get(shabadId)
}))

fs.writeFileSync(OUT_PATH, JSON.stringify(pauris, null, 2), 'utf8')

console.log(`Written ${pauris.length} pauris (${rows.length} lines) → ${OUT_PATH}`)

// Preview first and last pauri
console.log('\nFirst pauri lines:')
pauris[0].lines.forEach(l => console.log(`  [${l.type}] ${l.text.slice(0, 80)}`))
console.log('\nLast pauri lines:')
pauris[pauris.length - 1].lines.forEach(l => console.log(`  [${l.type}] ${l.text.slice(0, 80)}`))
