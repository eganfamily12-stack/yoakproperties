# Yoak Properties &amp; Construction Co. — website

Static site for **www.yoakproperties.com**. No framework, no build step required to
serve it: every file in the repository root is the deployed site exactly as it ships.

| | |
|---|---|
| Host | GitHub Pages, served from the repository root |
| Custom domain | `www.yoakproperties.com` (see [DNS](#dns-cutover)) |
| Pages | `index.html`, `about.html`, `properties.html`, `privacy.html`, `terms.html`, `404.html` |
| Third-party runtime requests | **none** — fonts, icons, CSS, JS and images are all local |
| Total weight, home page | ~330 KB first visit, ~30 KB on repeat visits |

---

## Before this goes live — open items

These need a decision from someone at Yoak. Nothing here blocks deployment, but
each one is visible to the public once the DNS is switched.

1. **`APPLY_URL` in `tools/transform.py`** currently points at the leasing
   Linktree (`linktr.ee/derekanders`). Every "apply", "see current listings" and
   "open house times" link on the site uses it. If Yoak has a Zillow *profile*
   URL, put it there instead and rebuild — it is one constant in one file.
2. **The three listing sections are hardcoded** (Aaliyah, Aaron, Trent). The
   leasing Linktree lists eight agents — Ashley, Derek, Harrison, Danny, Adam are
   missing here. The addresses shown were accurate as of June/July 2026. Stale
   dates have been removed and every card now points at Zillow for live details,
   but the addresses themselves will still drift. Longer term this section should
   be generated from whatever holds the real inventory rather than typed in.
3. **Listing photographs are representative, not per-address.** The photos are
   genuine Yoak interiors pulled from the current Wix site, but there is no record
   of which unit each one shows, so the properties page says so in print rather
   than implying a photo belongs to the address above it. Replace with real
   per-address photos when available and delete that sentence from
   `ZILLOW_NOTE` in `tools/transform.py`.
4. **Google reviews link** uses a Maps *search* URL that resolves to the office.
   Swapping in the place-ID review link (`MAPS_URL` / `REVIEWS_URL`) makes the
   "write a review" dialog open directly.
5. **`privacy.html` and `terms.html` have not been reviewed by counsel.** They
   were generated as part of the design mockups. Two specific claims do not match
   how Yoak actually operates:
   - Both describe a first-party "Tenant Portal" and application flow *on this
     website*. In reality the portal is Buildium and applications go through
     Zillow. The documents should either describe those third parties or be
     narrowed to cover only this website.
   - "Last Updated" was `October 2024` in the mockups. Since these pages have
     never been published, that date would assert a history they do not have; it
     is now the first-publication date (27 August 2026). Change it to whatever
     counsel decides is correct.
6. **Testimonials.** The mockup shipped three invented tenant quotes attributed
   to named people ("Liam Smith", "Ava Brown", "Noah Garcia"). Those are gone,
   replaced by a link to the real Google Business profile. If Yoak wants quotes
   on the page, they need to be real ones with permission to publish.

---

## Deploying

### First time

1. **Settings → Pages → Build and deployment**
   - Source: *Deploy from a branch*
   - Branch: `main`, folder: `/ (root)`
2. Wait for the green check. Because `CNAME` is present, Pages will immediately
   claim `www.yoakproperties.com` — so until DNS is switched, the
   `eganfamily12-stack.github.io/yoakproperties` URL will redirect to a domain
   that still points at Wix.
   **To preview before cutting over, delete `CNAME`, push, look at the
   `github.io` URL, then add `CNAME` back.** Every internal link is relative, so
   the site works correctly at either address.
3. Tick **Enforce HTTPS** once the certificate is issued (can take ~15 minutes
   after DNS propagates).

### DNS cutover

The domain is on Wix today. Nothing on GitHub's side breaks while that is true.
When ready, at the registrar:

| Record | Name | Value |
|---|---|---|
| CNAME | `www` | `eganfamily12-stack.github.io` |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

The four A records let the bare `yoakproperties.com` redirect to `www`. Remove the
old Wix records for the same names. Allow up to 48 hours, though it is usually
minutes. **Keep the Wix site paid up until the new one resolves and looks right** —
that is the rollback.

### Every time after

Edit, commit, push to `main`. Pages redeploys in about a minute.

---

## Editing content

Most copy lives directly in the page HTML — open the file, change the words.

Anything that appears on **more than one page** is generated, and editing the HTML
by hand will be overwritten on the next build. That includes the header, the
footer, the address, the phone number, and every page's `<title>` and meta tags.
Those live at the top of `tools/transform.py`:

```python
STREET     = '1361 Wooster Road W, Suite A'
CITY_LINE  = 'Barberton, OH 44203'
PHONE_TEXT = '330-794-7156'
EMAIL      = 'info@yoakproperties.com'
PORTAL_URL = 'https://yoakproperties.managebuilding.com/Resident/public/home'
APPLY_URL  = 'https://linktr.ee/derekanders'
```

Change one, rebuild, and it updates on all six pages at once.

### Rebuilding

```bash
cd tools && npm install && cd ..
python3 tools/transform.py     # mockups in tools/src/ -> the six page files
npm --prefix tools run css     # recompile assets/css/site.css
node tools/verify.mjs          # render every page and check it
```

`transform.py` fails loudly if a page still contains a placeholder link, a dead
image URL, the wrong zip code, or an icon name left as text.

`verify.mjs` loads all six pages at 1440px and 390px in headless Chromium and
fails on: broken images, horizontal overflow, links that go nowhere, buttons
with no behaviour, a page without exactly one `<h1>`, any 4xx response, or a
console error. It also opens and closes the mobile menu. Screenshots land in
`shots/`. **Run it before pushing.**

---

## How this repository is laid out

```
index.html  about.html  properties.html      the deployed pages
privacy.html  terms.html  404.html
assets/css/site.css                          compiled Tailwind, 32 KB minified
assets/js/site.js                            mobile menu + table-of-contents highlight
assets/fonts/                                7 text faces + a 3 KB icon subset
assets/img/                                  photographs, logo, favicons, OG image
CNAME  robots.txt  sitemap.xml  .nojekyll    hosting metadata
tools/                                       build tooling, not served
tools/src/                                   the original design mockups
```

`.nojekyll` stops GitHub from running the files through Jekyll, which would
otherwise ignore any future directory beginning with an underscore.

---

## What changed from the mockups, and why

The five files in `tools/src/` are the original Claude Design exports. They looked
right in a screenshot but were not a working website. For the record:

**Would have been broken on arrival**

- Every internal link was an unresolved `{{DATA:SCREEN:SCREEN_n}}` token, so no
  page reached any other page.
- One header link pointed at `C:\Users\eganj\OneDrive\Desktop\...` — a path on
  one specific laptop.
- All 13 hero and card images pointed at temporary `lh3.googleusercontent.com`
  URLs. Those are already dead; every image on the site would have been a broken
  icon. They are now local files in `assets/img/`.
- **On a phone there was no navigation at all.** The menu button had no panel
  behind it and the site shipped no JavaScript. Since most rental search traffic
  is mobile, this alone made the site unusable for the majority of visitors.
- The hero's "View Listings" and "Learn More", the "Tenant Portal" control, and
  "View All Listings" were `<button>` elements with no handler — they looked
  clickable and did nothing. All are now links.
- Two "Interested in a private tour?" links were `href="#"`.
- `rounded-DEFAULT` was used in several places. Tailwind emits that key as
  `rounded`, so those corners were silently square.

**Wrong facts**

- The Barberton office zip was `44302` on four of the five pages. `44302` is
  Akron; the office is `44203`. Confirmed against the LoopNet and Zillow listings
  for 1361 Wooster Rd W and the chamber of commerce record for the phone number.
- Copyright read 2024.
- The properties page advertised open houses on dates in June and July.

**Things that were not true**

- Three tenant testimonials attributed to invented people.
- The home page showed "$950/mo", "$1,100/mo" and "$850/mo" against *cities*
  rather than units, with "Available" and "Newly Renovated" badges. Those cards
  are now what they always were — area descriptions — and link to the listings
  page.
- An agent headshot generated for a real named employee. Replaced with a monogram.
- A drawn "map illustration" of Barberton. Replaced with a link that opens the
  real office location in Google Maps.

**Made faster and more robust**

- Tailwind was loaded from `cdn.tailwindcss.com`, which compiles CSS in the
  visitor's browser and which Tailwind documents as not for production. Replaced
  with 32 KB of precompiled CSS.
- Icons came from Google's Material Symbols variable font, about 4 MB, and were
  addressed *by ligature* — the element's text was the literal string
  `real_estate_agent`. When that font is slow or blocked, the visitor reads icon
  names as words all over the page. They now come from a **3 KB local subset**
  containing only the 29 glyphs this site uses, addressed by codepoint, so a
  failed load renders nothing instead of gibberish.
- Montserrat and Inter are self-hosted (156 KB for all 8 faces), so the site
  makes no third-party requests at all. It renders identically on networks that
  block Google Fonts, and nothing about visitors is shared with a third party.
- Images are sized, `loading="lazy"` below the fold, and the hero is
  `fetchpriority="high"`.

**Accessibility and SEO**

- Every icon is `aria-hidden`. Screen readers were previously announcing
  "real_estate_agent" and "support_agent" as content.
- Added a skip link, visible keyboard focus rings, `aria-expanded` /
  `aria-controls` on the menu button, `aria-current` on the active nav item, and
  a `prefers-reduced-motion` block.
- Every image has real alt text describing the photograph. The mockups had put
  the image-generation prompt in a `data-alt` attribute and left `alt` empty.
- Added per-page titles and meta descriptions, canonical URLs, Open Graph and
  Twitter card tags, favicons, `RealEstateAgent` structured data with the
  corrected address, `sitemap.xml`, and `robots.txt`.
- Added an Equal Housing Opportunity notice to the footer.
- Nav order and footer contents differed on all five pages; both are now
  generated once.

---

## Contact details, in one place

| | |
|---|---|
| Office | 1361 Wooster Road W, Suite A, Barberton, OH 44203 |
| Phone | 330-794-7156 |
| Email | info@yoakproperties.com |
| Resident portal | https://yoakproperties.managebuilding.com/Resident/public/home |
