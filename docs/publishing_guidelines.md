# Publishing Plan — Japji Sahib EPUB

## What We Know (Confirmed)

| Fact | Source |
|------|--------|
| Japji Sahib text is public domain | Composed 1499–1539; Shabad OS source is open |
| Apple Books accepts $0.00 and has no restrictions on public domain scripture | Platform policy |
| Google Play Books accepts $0.00, no known restrictions | Platform policy |
| KDP minimum list price is $0.99 | Platform policy |
| KDP price-match to $0.00 requires a lower price on another store first | KDP documentation |
| Kobo Writing Life has restricted new public domain submissions | Reported policy change — not personally verified |
| Draft2Digital distributes to Kobo and Amazon, supports $0.00 | Platform documentation |
| The EPUB is 645KB, EPUB3-compliant, embedded Tiro Gurmukhi font | Verified in build |

---

## Hypotheses (Untested)

- [ ] **H1:** Kobo Writing Life will reject Japji Sahib as a public domain work — but an upload attempt hasn't been made. Religious scripture may be treated differently than literary reprints.
- [ ] **H2:** KDP will price-match to $0.00 after Apple Books publishes first. Works in most cases but not guaranteed for Punjabi-language content or all regions.
- [ ] **H3:** Our EPUB passes `epubcheck` (the industry validator). Not yet run — spine fix and cover format change are recent.
- [ ] **H4:** KDP's content pre-check will accept the file without requesting a public domain declaration form.
- [ ] **H5:** RAVINARTOOR will grant permission for cover art use. Reached out — no response yet.

---

## Blockers Before Publishing

| Blocker | Status | Owner |
|---------|--------|-------|
| Cover art permission from RAVINARTOOR | Waiting | Kanika |
| Run `epubcheck` on the EPUB | Not done | — |
| Write store metadata (description, keywords) | Not done | — |

---

## Recommended Publishing Sequence

```
Step 1 → Apple Books ($0.00)
          - No public domain restrictions
          - Establishes the $0.00 price reference for KDP price-match
          - Upload directly via Books for Authors (authors.apple.com)

Step 2 → Google Play Books ($0.00)
          - Second reference price
          - Backup if Amazon disputes Apple Books as a reference

Step 3 → Test Kobo Writing Life upload
          - If accepted: publish at $0.00
          - If rejected: use Draft2Digital → Kobo instead

Step 4 → KDP price-match request
          - Publish at $0.99 first (required)
          - Then use "Report a lower price" link on the Amazon product page
          - Reference: Apple Books or Google Play listing at $0.00
```

---

## Store Metadata (Use Consistently Across All Platforms)

| Field | Value |
|-------|-------|
| **Title** | Japji Sahib |
| **Gurmukhi Title** | ਜਪੁਜੀ ਸਾਹਿਬ |
| **Author** | Guru Nanak Dev Ji |
| **Category** | Religion & Spirituality → Sikhism |
| **Language** | Punjabi (`pa`) |
| **Price** | $0.00 |
| **ISBN** | Not required — platforms assign their own identifiers. Draft2Digital provides one free if needed. |

**Description (draft — needs review before use):**
> The complete Japji Sahib by Guru Nanak Dev Ji — in Unicode Gurmukhi, typeset for e-ink reading. Every word is rendered atomically using the Tiro Gurmukhi font, ensuring Gurmukhi vowel signs and conjuncts never break across lines. Formatted and tested on 16 Kindle and Kobo devices.

---

## Platform Notes

### Apple Books
- Upload via: authors.apple.com
- Accepts EPUB3 directly
- $0.00 available natively
- No public domain restrictions on scripture

### Google Play Books
- Upload via: play.google.com/books/publish
- $0.00 available
- May require a publisher name even for individuals

### Kobo Writing Life
- Upload via: kobowritinglife.com
- **Test first** — policy on public domain is unclear for religious texts
- Fallback: Draft2Digital → Kobo

### Kindle Direct Publishing (KDP)
- Upload via: kdp.amazon.com
- Must list at $0.99 initially
- Price-match request after Apple/Google publish at $0.00
- May require confirming public domain status during upload

### Draft2Digital
- Aggregator that distributes to Kobo, Amazon, Apple, Barnes & Noble, and others
- Supports $0.00 natively
- Simpler for public domain titles — handles platform-specific rules on your behalf
- Provides a free ISBN
