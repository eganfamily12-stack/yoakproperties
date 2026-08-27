#!/usr/bin/env python3
"""
Yoak Properties — build script.

Takes the five Claude Design mockup exports in src/ and produces a
deployable static site in site/.

What it fixes, and why:
  * {{DATA:SCREEN:SCREEN_n}} placeholder hrefs never resolved to anything.
  * One href pointed at C:\\Users\\eganj\\... on Joshua's desktop.
  * Every hero / card image pointed at temporary lh3.googleusercontent.com
    URLs that are already dead. Swapped for local files in assets/img.
  * The mobile menu button had no panel and no JS: phones had no nav.
  * The Tenant Portal control was a <button>, so it did nothing.
  * Nav order and footer contents differed on all five pages.
  * Barberton zip was 44302 (that's Akron); correct is 44203.
  * Copyright read 2024.
  * rounded-DEFAULT is not a class Tailwind emits, so those corners were square.
  * Icon <span>s were read aloud by screen readers as "real_estate_agent".
  * Home page showed invented rents and invented tenant testimonials.
  * Properties page advertised open houses that happened in June and July.
"""

import json
import os
import re
import sys

SRC = 'src'
OUT = 'site'

# --------------------------------------------------------------------------
# Single source of truth for every fact that appears on more than one page.
# --------------------------------------------------------------------------
BRAND       = 'Yoak Properties &amp; Construction Co.'
BRAND_SHORT = 'Yoak Properties'
SITE_URL    = 'https://www.yoakproperties.com'
STREET      = '1361 Wooster Road W, Suite A'
CITY_LINE   = 'Barberton, OH 44203'
ADDRESS     = f'{STREET}, {CITY_LINE}'
PHONE_TEXT  = '330-794-7156'
PHONE_HREF  = 'tel:+13307947156'
EMAIL       = 'info@yoakproperties.com'
YEAR        = '2026'
LEGAL_DATE  = 'August 27, 2026'

# Resident portal — Yoak's live Buildium tenant portal.
PORTAL_URL  = 'https://yoakproperties.managebuilding.com/Resident/public/home'

# Leasing hub. Yoak's own FAQ says open house times and full details live on
# the Zillow listing, reached through the per-agent docs on this page.
# TODO(Joshua): if Yoak has a Zillow *profile* URL, put it here — it is used
# in every "apply / see current listings" call to action on the site.
APPLY_URL   = 'https://linktr.ee/derekanders'

# Google Maps search that resolves to the office listing. Swap for the
# place-ID review link if you want the "write a review" dialog to open.
MAPS_URL    = ('https://www.google.com/maps/search/?api=1&amp;query='
               'Yoak+Properties+and+Construction+1361+Wooster+Rd+W+Barberton+OH+44203')
REVIEWS_URL = MAPS_URL

PAGES = [
    # src stem,      output,             nav key,      title, description
    ('home', 'index.html', 'home',
     f'{BRAND_SHORT} | Affordable Rental Homes in Akron, Canton &amp; Barberton, OH',
     'Affordable, well-managed rental homes across Akron, Canton, Barberton, '
     'Massillon and the surrounding Ohio communities. On-staff maintenance, '
     'responsive tenant support and an online resident portal.'),
    ('about', 'about.html', 'about',
     f'About Us | {BRAND_SHORT}',
     'Yoak Properties &amp; Construction Co. provides affordable, quality housing '
     'and expert property management across Summit and Stark County, Ohio.'),
    ('properties', 'properties.html', 'properties',
     f'Our Properties | {BRAND_SHORT}',
     'Browse rental homes managed by Yoak Properties in Akron, Barberton and '
     'the surrounding areas. Current open house times and applications are on Zillow.'),
    ('privacy', 'privacy.html', None,
     f'Privacy Policy | {BRAND_SHORT}',
     'How Yoak Properties &amp; Construction Co. collects, uses and protects '
     'applicant and tenant information.'),
    ('terms', 'terms.html', None,
     f'Terms of Service | {BRAND_SHORT}',
     'Terms governing use of the Yoak Properties website, resident portal and '
     'rental application process.'),
    ('404', '404.html', None,
     f'Page Not Found | {BRAND_SHORT}',
     'That page could not be found. Browse current Yoak Properties rentals instead.'),
]

NAV = [('home', 'Home', 'index.html'),
       ('properties', 'Our Properties', 'properties.html'),
       ('about', 'About Us', 'about.html')]


# --------------------------------------------------------------------------
# Inline SVGs. Used for the few icons that must render before the icon font
# arrives (the hamburger) or that carry meaning on their own.
# --------------------------------------------------------------------------
SVG_MENU = ('<svg data-icon="open" class="w-6 h-6" fill="none" viewBox="0 0 24 24" '
            'stroke="currentColor" stroke-width="2" aria-hidden="true">'
            '<path stroke-linecap="round" stroke-linejoin="round" d="M4 7h16M4 12h16M4 17h16"/></svg>')
SVG_CLOSE = ('<svg data-icon="close" class="w-6 h-6 hidden" fill="none" viewBox="0 0 24 24" '
             'stroke="currentColor" stroke-width="2" aria-hidden="true">'
             '<path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M18 6L6 18"/></svg>')


def header(active):
    """Canonical sticky header with a working mobile panel."""
    def links(mobile):
        out = []
        for key, label, href in NAV:
            on = (key == active)
            if mobile:
                cls = ('block px-margin-mobile py-4 font-label-bold text-label-bold border-b '
                       'border-outline-variant/20 ' +
                       ('text-heritage-gold font-bold' if on
                        else 'text-deep-navy hover:bg-surface-container-low'))
            else:
                cls = ('font-label-bold text-label-bold transition-colors ' +
                       ('text-heritage-gold font-bold border-b-2 border-heritage-gold pb-1' if on
                        else 'text-slate-gray hover:text-deep-navy'))
            cur = ' aria-current="page"' if on else ''
            out.append(f'<a class="{cls}" href="{href}"{cur}>{label}</a>')
        return '\n'.join(out)

    return f'''<a class="skip-link" href="#main">Skip to main content</a>
<header class="bg-surface-off-white/95 backdrop-blur-md sticky top-0 z-50 border-b border-outline-variant/30 shadow-sm">
<div class="flex justify-between items-center gap-4 w-full px-margin-mobile md:px-gutter max-w-container-max mx-auto h-20">
<a class="flex items-center gap-3 shrink-0 hover:opacity-80 transition-opacity" href="index.html">
<img alt="" class="w-10 h-10 rounded object-cover shrink-0" height="40" src="assets/img/logo-yoak.png" width="40"/>
<span class="font-headline-md text-headline-md font-bold text-deep-navy tracking-tight leading-none">{BRAND_SHORT}</span>
</a>
<nav aria-label="Main navigation" class="hidden md:flex items-center gap-8">
{links(False)}
</nav>
<div class="hidden md:flex shrink-0">
<a class="bg-deep-navy text-surface-off-white px-6 py-2 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors" href="{PORTAL_URL}" rel="noopener" target="_blank">Tenant Portal</a>
</div>
<button aria-controls="mobile-nav" aria-expanded="false" aria-label="Open menu" class="md:hidden text-deep-navy p-2 -mr-2 hover:bg-surface-container-low rounded-lg transition-colors" id="nav-toggle" type="button">
{SVG_MENU}{SVG_CLOSE}
</button>
</div>
<div class="md:hidden hidden border-t border-outline-variant/30 bg-surface-off-white shadow-lg" id="mobile-nav">
<nav aria-label="Mobile navigation" class="flex flex-col">
{links(True)}
<a class="block px-margin-mobile py-4 font-label-bold text-label-bold text-heritage-gold" href="{PORTAL_URL}" rel="noopener" target="_blank">Tenant Portal &#8599;</a>
</nav>
</div>
</header>'''


FOOTER = f'''<footer class="bg-deep-navy text-surface-off-white border-t border-slate-gray/20 mt-auto">
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-gutter px-margin-mobile md:px-gutter py-section-gap-mobile md:py-16 max-w-container-max mx-auto">
<div class="space-y-4">
<div class="font-headline-md text-headline-md text-heritage-gold">{BRAND_SHORT}</div>
<p class="font-body-md text-body-md text-surface-variant/80 max-w-xs">Affordable homes for families. Expert property management and quality construction across Northeast Ohio.</p>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Contact</h2>
<address class="not-italic font-body-md text-body-md text-surface-variant/80 space-y-2">
<a class="block hover:text-heritage-gold transition-colors" href="{MAPS_URL}" rel="noopener" target="_blank">{STREET}<br/>{CITY_LINE}</a>
<a class="block hover:text-heritage-gold transition-colors" href="{PHONE_HREF}">{PHONE_TEXT}</a>
<a class="block hover:text-heritage-gold transition-colors" href="mailto:{EMAIL}">{EMAIL}</a>
</address>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Quick Links</h2>
<nav aria-label="Footer navigation" class="flex flex-col gap-2 font-body-md text-body-md text-surface-variant/80">
<a class="hover:text-heritage-gold transition-colors" href="index.html">Home</a>
<a class="hover:text-heritage-gold transition-colors" href="properties.html">Our Properties</a>
<a class="hover:text-heritage-gold transition-colors" href="about.html">About Us</a>
<a class="hover:text-heritage-gold transition-colors" href="about.html#contact">Contact Us</a>
<a class="hover:text-heritage-gold transition-colors" href="{PORTAL_URL}" rel="noopener" target="_blank">Tenant Portal</a>
</nav>
</div>
<div class="space-y-3">
<h2 class="font-label-bold text-label-bold uppercase text-heritage-gold">Legal</h2>
<nav aria-label="Legal navigation" class="flex flex-col gap-2 font-body-md text-body-md text-surface-variant/80">
<a class="hover:text-heritage-gold transition-colors" href="privacy.html">Privacy Policy</a>
<a class="hover:text-heritage-gold transition-colors" href="terms.html">Terms of Service</a>
</nav>
<p class="font-caption text-caption text-surface-variant/60 pt-2">Equal Housing Opportunity.<br/>We do not discriminate on the basis of race, color, religion, sex, disability, familial status or national origin.</p>
</div>
</div>
<div class="px-margin-mobile md:px-gutter py-6 max-w-container-max mx-auto border-t border-slate-gray/20">
<p class="font-caption text-caption text-surface-variant/60">&#169; {YEAR} {BRAND} All rights reserved.</p>
</div>
</footer>'''


def head(title, desc, canonical, page_key):
    og_type = 'website'
    jsonld = ''
    if page_key == 'home':
        jsonld = f'''
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "RealEstateAgent",
  "name": "Yoak Properties and Construction Co.",
  "url": "{SITE_URL}",
  "image": "{SITE_URL}/assets/img/og-banner.jpg",
  "logo": "{SITE_URL}/assets/img/logo-yoak.png",
  "telephone": "+1-330-794-7156",
  "email": "{EMAIL}",
  "address": {{
    "@type": "PostalAddress",
    "streetAddress": "1361 Wooster Road W, Suite A",
    "addressLocality": "Barberton",
    "addressRegion": "OH",
    "postalCode": "44203",
    "addressCountry": "US"
  }},
  "areaServed": [
    {{"@type": "City", "name": "Akron"}},
    {{"@type": "City", "name": "Canton"}},
    {{"@type": "City", "name": "Barberton"}},
    {{"@type": "City", "name": "Massillon"}}
  ]
}}
</script>'''
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{title}</title>
<meta content="{desc}" name="description"/>
<link href="{SITE_URL}/{canonical}" rel="canonical"/>
<meta content="{og_type}" property="og:type"/>
<meta content="{title}" property="og:title"/>
<meta content="{desc}" property="og:description"/>
<meta content="{SITE_URL}/{canonical}" property="og:url"/>
<meta content="{SITE_URL}/assets/img/og-banner.jpg" property="og:image"/>
<meta content="{BRAND_SHORT}" property="og:site_name"/>
<meta content="summary_large_image" name="twitter:card"/>
<meta content="#0F172A" name="theme-color"/>
<link href="assets/img/favicon-32.png" rel="icon" sizes="32x32" type="image/png"/>
<link href="assets/img/favicon-64.png" rel="icon" sizes="64x64" type="image/png"/>
<link href="assets/img/apple-touch-icon.png" rel="apple-touch-icon"/>
<link as="font" crossorigin href="assets/fonts/inter-latin-400-normal.woff2" rel="preload" type="font/woff2"/>
<link as="font" crossorigin href="assets/fonts/montserrat-latin-700-normal.woff2" rel="preload" type="font/woff2"/>
<link as="font" crossorigin href="assets/fonts/yoak-icons.woff2" rel="preload" type="font/woff2"/>
<link href="assets/css/site.css" rel="stylesheet"/>{jsonld}
</head>'''


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def read(stem):
    with open(os.path.join(SRC, stem + '.html'), encoding='utf-8') as f:
        return f.read()


def grab_main(html):
    m = re.search(r'(?s)<main\b[^>]*>(.*)</main>', html)
    if not m:
        sys.exit('no <main> found')
    return m.group(1)


def split_sections(main):
    """Split into top-level <section> blocks, tracking nesting depth."""
    parts, i = [], 0
    for m in re.finditer(r'<(/?)section\b[^>]*>', main):
        pass
    depth, start = 0, None
    for m in re.finditer(r'<(/?)section\b[^>]*>', main):
        if not m.group(1):
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start is not None:
                parts.append(main[start:m.end()])
                start = None
    return parts


def img(src, alt, cls, eager=False, w=None, h=None):
    load = ('fetchpriority="high" loading="eager"' if eager
            else 'decoding="async" loading="lazy"')
    dims = f' height="{h}" width="{w}"' if w else ''
    return f'<img alt="{alt}" class="{cls}" {load} src="{src}"{dims}/>'


# --------------------------------------------------------------------------
# global cleanups applied to every page's <main>
# --------------------------------------------------------------------------
SCREEN_MAP = {
    'SCREEN_2': 'index.html',
    'SCREEN_9': 'properties.html',
    'SCREEN_10': 'about.html',
    'SCREEN_6': 'privacy.html',
    'SCREEN_8': 'terms.html',
}


ICON_CP = json.load(open(os.path.join('build', 'icons.json'), encoding='utf-8'))


def icons_to_entities(html):
    """Address icons by codepoint, not by ligature name.

    The mockups wrote the icon name as the element's text ("real_estate_agent").
    If the icon font fails to load, that name is what the visitor reads. Using
    the codepoint means a failed load renders nothing at all.
    """
    unknown = set()

    def sub(m):
        name = m.group(2)
        cp = ICON_CP.get(name)
        if cp is None:
            unknown.add(name)
            return m.group(0)
        return f'{m.group(1)}&#x{cp:X};{m.group(3)}'

    html = re.sub(r'(<span[^>]*material-symbols-outlined[^>]*>)\s*([a-z_0-9]+)\s*(</span>)',
                  sub, html)
    if unknown:
        print('  !! unmapped icons:', sorted(unknown))
    return html


def clean(html):
    for k, v in SCREEN_MAP.items():
        html = html.replace('{{DATA:SCREEN:' + k + '}}', v)
    # the stray absolute path to Joshua's desktop
    html = re.sub(r'href="[A-Za-z]:\\\\?[^"]*"', 'href="index.html"', html)
    html = re.sub(r'href="[A-Za-z]:\\[^"]*"', 'href="index.html"', html)
    # Tailwind never emits `rounded-DEFAULT`; `rounded` is the DEFAULT key.
    html = re.sub(r'\brounded-DEFAULT\b', 'rounded', html)
    # leftovers from the design tool that mean nothing in CSS
    html = re.sub(r'\b(docked|full-width)\b\s*', '', html)
    # wrong zip: 44302 is Akron, the office is in Barberton 44203
    html = html.replace('OH 44302', 'OH 44203').replace('44302', '44203')
    html = html.replace('&copy; 2024', f'&copy; {YEAR}').replace('© 2024', f'© {YEAR}')
    # icon spans are decorative; stop screen readers reading "real_estate_agent"
    html = re.sub(r'<span class="([^"]*material-symbols-outlined[^"]*)"(?![^>]*aria-hidden)',
                  r'<span aria-hidden="true" class="\1"', html)
    # phone numbers should be tappable
    html = html.replace('href="tel:330-794-7156"', f'href="{PHONE_HREF}"')
    # external links need rel=noopener
    html = re.sub(r'<a ([^>]*href="https?://(?!www\.yoakproperties)[^"]*")((?![^>]*rel=)[^>]*)>',
                  r'<a \1 rel="noopener" target="_blank"\2>', html)
    html = html.replace('fill-icon', '')
    html = icons_to_entities(html)
    return html


def strip_dates(html):
    """Remove past open-house dates and times from listing copy."""
    # e.g. "Open House is Thursday, June 25th 5:00-5:30 PM"
    html = re.sub(r'\s*Open [Hh]ouse is [A-Z][a-z]+day,\s*[A-Z][a-z]+\s*\d+(st|nd|rd|th)?'
                  r'\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    # e.g. "Open House Tue, Jun 16, 6:00-6:15 PM"
    html = re.sub(r'\s*Open House\s+[A-Z][a-z]{2},\s*[A-Z][a-z]{2}\s*\d+,\s*'
                  r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    # e.g. "Mon, July 20th • 5:00 - 5:30 PM"  /  "Mon, July 20th"
    html = re.sub(r'\s*[A-Z][a-z]{2},\s*[A-Z][a-z]+\s*\d+(st|nd|rd|th)?'
                  r'(\s*(&#8226;|•|\|)\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M)?', '', html)
    html = re.sub(r'\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*[AP]M', '', html)
    return html


# ==========================================================================
# HOME
# ==========================================================================
CARD = ('bg-surface-container-lowest rounded-xl shadow-card overflow-hidden group '
        'hover:-translate-y-2 hover:shadow-card-hover transition-all duration-300 '
        'border-b border-transparent hover:border-heritage-gold flex flex-col')

AREAS = [
    ('Canton &amp; Massillon', 'area-canton.jpg',
     'Front exterior of a renovated two-storey Yoak Properties rental home',
     'Modern, affordable single-family homes and duplexes in Canton, Massillon '
     'and the surrounding Stark County communities.'),
    ('Akron', 'area-akron.jpg',
     'Front exterior of a single-storey Yoak Properties rental home',
     'Comfortable rentals across Akron, close to schools, transit and everyday '
     'amenities, all managed by our in-house team.'),
    ('Barberton', 'area-massillon.jpg',
     'Front porch and exterior of a Yoak Properties rental home',
     'Our home base. Barberton and the surrounding Summit County neighbourhoods, '
     'with maintenance crews minutes away.'),
]


def home_hero():
    return f'''<section class="relative min-h-[80vh] flex items-center justify-center px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop bg-deep-navy">
<div class="absolute inset-0 z-0">
{img('assets/img/hero-home.jpg',
     'A renovated two-storey family home managed by Yoak Properties',
     'w-full h-full object-cover', eager=True, w=1600, h=900)}
<div class="absolute inset-0 bg-deep-navy/75"></div>
</div>
<div class="relative z-10 max-w-container-max mx-auto grid grid-cols-1 md:grid-cols-12 gap-gutter w-full">
<div class="col-span-1 md:col-span-8 lg:col-span-7 flex flex-col justify-center space-y-6">
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-surface-off-white text-balance drop-shadow-sm">
Affordable Homes <br/><span class="text-heritage-gold">for Families</span>
</h1>
<p class="font-body-lg text-body-lg text-surface-container-low max-w-2xl text-balance">
Expertly managed rentals in Akron, Canton, Barberton, Massillon and the surrounding areas. On-staff maintenance, responsive support, and a resident portal that actually works.
</p>
<div class="flex flex-wrap gap-4 pt-4">
<a class="bg-heritage-gold text-deep-navy px-8 py-3 rounded hover:-translate-y-1 hover:shadow-lg transition-all font-label-bold text-label-bold" href="properties.html">View Listings</a>
<a class="bg-transparent border-2 border-surface-off-white text-surface-off-white px-8 py-3 rounded hover:bg-surface-off-white/10 transition-colors font-label-bold text-label-bold" href="about.html">Learn More</a>
</div>
</div>
</div>
</section>'''


def home_areas():
    cards = []
    for name, f, alt, body in AREAS:
        cards.append(f'''<article class="{CARD}">
<a class="relative h-64 overflow-hidden bg-surface-dim block" href="properties.html">
{img('assets/img/' + f, alt,
     'w-full h-full object-cover group-hover:scale-105 transition-transform duration-700',
     w=800, h=600)}
</a>
<div class="p-6 flex flex-col flex-grow">
<h3 class="font-headline-md text-headline-md text-deep-navy mb-2">{name}</h3>
<p class="font-body-md text-body-md text-slate-gray mb-6 flex-grow">{body}</p>
<div class="pt-4 border-t border-surface-container-highest">
<a class="text-heritage-gold font-label-bold text-label-bold hover:underline inline-flex items-center gap-1" href="properties.html">View homes in this area <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_forward</span></a>
</div>
</div>
</article>''')
    return f'''<section class="px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop bg-surface-bright">
<div class="max-w-container-max mx-auto">
<div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
<div>
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-deep-navy mb-2">Where We Manage</h2>
<p class="font-body-md text-body-md text-slate-gray max-w-2xl">Quality rental homes across Summit and Stark County. Availability changes weekly, so the properties page is always the current list.</p>
</div>
<a class="text-heritage-gold font-label-bold text-label-bold flex items-center gap-1 hover:opacity-80 transition-opacity shrink-0" href="properties.html">
View All Listings <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_forward</span>
</a>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">
{''.join(cards)}
</div>
</div>
</section>'''


def home_reviews():
    """Replaces three invented tenant testimonials with a link to the real thing."""
    return f'''<section class="px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop bg-surface-bright">
<div class="max-w-container-max mx-auto">
<div class="bg-soft-gold rounded-xl p-8 md:p-12 border border-outline-variant/10 relative overflow-hidden">
<div class="absolute top-0 right-0 -mr-12 -mt-12 w-64 h-64 bg-heritage-gold/10 rounded-full blur-3xl pointer-events-none"></div>
<div class="relative z-10 flex flex-col md:flex-row md:items-center gap-8 justify-between">
<div class="max-w-2xl">
<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold text-4xl">format_quote</span>
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-deep-navy mt-2 mb-3">What Our Tenants Say</h2>
<p class="font-body-lg text-body-lg text-on-surface-variant">Our residents leave reviews on our Google Business profile. Read what they have to say, or add your own if you rent with us.</p>
</div>
<div class="shrink-0 flex flex-col sm:flex-row md:flex-col gap-3">
<a class="bg-deep-navy text-surface-off-white px-8 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors inline-flex items-center justify-center gap-2" href="{REVIEWS_URL}" rel="noopener" target="_blank">Read our reviews <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></a>
<a class="bg-transparent border border-heritage-gold text-deep-navy px-8 py-3 rounded font-label-bold text-label-bold hover:bg-heritage-gold/10 transition-colors inline-flex items-center justify-center gap-2" href="about.html#contact">Contact our team</a>
</div>
</div>
</div>
</div>
</section>'''


def build_home():
    secs = split_sections(grab_main(read('home')))
    offer = clean(secs[2])          # "What We Offer" — keep as designed
    body = ('<main id="main">'
            + home_hero() + home_areas() + offer + home_reviews()
            + '</main>')
    return body


# ==========================================================================
# ABOUT
# ==========================================================================
def build_about():
    main = clean(grab_main(read('about')))

    # hero photo
    main = re.sub(
        r'<img[^>]*src="https://lh3\.googleusercontent\.com/aida-public/AB6AXuBdgR9q[^"]*"[^>]*>',
        img('assets/img/about-hero.jpg',
            'A renovated kitchen in a Yoak Properties rental home',
            'w-full h-[400px] object-cover', eager=True, w=1200, h=600),
        main)

    # The second image was a made-up "map illustration" of Barberton. A real
    # link to the office on Google Maps is more use to a visitor than a drawing.
    main = re.sub(
        r'<img[^>]*src="https://lh3\.googleusercontent\.com/aida-public/AB6AXuDUS113[^"]*"[^>]*>',
        f'''<a class="group flex flex-col items-center justify-center text-center w-full h-full min-h-[18rem] bg-soft-gold text-deep-navy p-8 gap-3 hover:bg-secondary-fixed/40 transition-colors" href="{MAPS_URL}" rel="noopener" target="_blank">
<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold" style="font-size:56px">location_on</span>
<span class="font-headline-md text-headline-md">Visit the office</span>
<span class="font-body-md text-body-md text-on-surface-variant">{STREET}<br/>{CITY_LINE}</span>
<span class="font-label-bold text-label-bold text-secondary inline-flex items-center gap-1 mt-2 group-hover:underline">Get directions <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></span>
</a>''',
        main)

    # footer link points at about.html#contact, so give the section that id
    main = main.replace('id="contact-section"', 'id="contact"')
    main = main.replace('href="#contact-section"', 'href="#contact"')

    # dead buttons -> real links
    main = re.sub(r'<button([^>]*)>\s*Explore Our Services\s*</button>',
                  r'<a\1 href="#services">Explore Our Services</a>', main)
    main = re.sub(r'<button([^>]*)>\s*View Our Listings\s*</button>',
                  r'<a\1 href="properties.html">View Our Listings</a>', main)
    return f'<main id="main">{main}</main>'


# ==========================================================================
# PROPERTIES
# ==========================================================================
LISTING_PHOTOS = [
    ('interior-living-fireplace.jpg', 'Living room with original fireplace in a Yoak Properties rental home'),
    ('interior-bath.jpg', 'Updated bathroom in a Yoak Properties rental home'),
    ('interior-sunroom.jpg', 'Sunroom with wraparound windows in a Yoak Properties rental home'),
    ('interior-kitchen-white.jpg', 'Kitchen with white cabinetry in a Yoak Properties rental home'),
    ('interior-kitchen-classic.jpg', 'Kitchen with full-size appliances in a Yoak Properties rental home'),
    ('interior-living-carpet.jpg', 'Carpeted living room in a Yoak Properties rental home'),
]

ZILLOW_NOTE = f'''<div class="bg-soft-gold border-l-4 border-heritage-gold rounded p-6 md:p-8 mb-12 flex flex-col md:flex-row md:items-center gap-6 justify-between">
<div class="max-w-3xl">
<h2 class="font-headline-md text-headline-md text-deep-navy mb-2 flex items-center gap-2"><span aria-hidden="true" class="material-symbols-outlined text-heritage-gold">event</span>Open house times and applications are on Zillow</h2>
<p class="font-body-md text-body-md text-on-surface-variant">The homes below are a sample of what we manage. Availability, current open house dates and the application for every property are kept on the Zillow listing, so always check there before you visit. Photographs show representative Yoak Properties homes rather than a specific unit.</p>
</div>
<a class="shrink-0 bg-deep-navy text-surface-off-white px-6 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors inline-flex items-center justify-center gap-2" href="{APPLY_URL}" rel="noopener" target="_blank">See all current listings <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></a>
</div>'''


def build_properties():
    raw = read('properties')
    # This page's <h1> intro sits *outside* <main> in the mockup, so take
    # everything between the header and the footer instead.
    seg = re.search(r'(?s)</header>(.*?)<footer', raw)
    body = seg.group(1)
    intro = re.search(r'(?s)(<section\b(?:(?!</section>).)*?<h1\b.*?</section>)', body)
    intro_html = clean(intro.group(1)) if intro else ''
    main = clean(grab_main(raw))
    main = strip_dates(main)

    # After the stale dates come out, "6/2" and "3/1" are left stranded next to
    # a calendar icon. They are bed/bath counts, so say so and swap the icon.
    main = main.replace('>event<', '>bed<')
    main = re.sub(r'(?<![\d/.])(\d)\s*/\s*(\d(?:\.\d)?)\s*(?:Layout Details)?(?![\d/])',
                  r'\1 bed / \2 bath', main)

    # Replace the six dead listing photos, in document order.
    photos = list(LISTING_PHOTOS)

    def swap(m):
        if not photos:
            return m.group(0)
        f, alt = photos.pop(0)
        return img('assets/img/' + f, alt,
                   'w-full h-full object-cover group-hover:scale-105 transition-transform duration-700',
                   w=800, h=600)

    # the agent avatar comes first in the document; handle it before the rest
    main = re.sub(
        r'<img[^>]*alt="Aaliyah"[^>]*>',
        '<span aria-hidden="true" class="w-full h-full flex items-center justify-center '
        'bg-deep-navy text-heritage-gold font-headline-md text-headline-md">A</span>',
        main)
    main = re.sub(r'<img[^>]*src="https://lh3\.googleusercontent\.com/[^"]*"[^>]*>', swap, main)

    # bare zillow.com homepage links -> the leasing hub
    main = main.replace('href="https://www.zillow.com/"', f'href="{APPLY_URL}"')

    # dead buttons -> links
    main = re.sub(r'<button([^>]*)>\s*(Submit Zillow App|Apply on Zillow|Submit Application on Zillow)([^<]*)</button>',
                  rf'<a\1 href="{APPLY_URL}" rel="noopener" target="_blank">\2\3</a>', main)

    # "Interested in a private tour?" pointed at href="#"
    main = main.replace('href="#"', f'href="{APPLY_URL}" rel="noopener" target="_blank"')
    main = re.sub(r'(Interested in a private tour\?)\s*\n?\s*<span aria-hidden',
                  r'Book a private tour\n<span aria-hidden', main)

    # strip_dates leaves empty elements where a date used to be. Rather than
    # delete them (which would leave a card with no call to action at all),
    # turn each into a link to where the live time actually lives.
    tour_link = (f'<a class="font-caption text-caption text-heritage-gold font-bold '
                 f'hover:underline inline-flex items-center gap-1" href="{APPLY_URL}" '
                 f'rel="noopener" target="_blank">Open house times on Zillow '
                 f'<span aria-hidden="true" class="material-symbols-outlined text-[14px]">arrow_outward</span></a>')

    # Aaron's cards: clock icon followed by an emptied <p>
    main = re.sub(
        r'<p class="font-caption text-caption text-slate-gray flex items-center gap-2">\s*'
        r'<span aria-hidden="true" class="material-symbols-outlined[^"]*">[^<]*</span>\s*</p>',
        tour_link, main)

    # Trent's rows: "Open House" label above an emptied <p>
    main = re.sub(
        r'(<p class="font-caption text-caption text-heritage-gold font-bold uppercase tracking-wider mb-1">Open House</p>)\s*'
        r'<p class="font-body-md text-deep-navy font-medium">\s*</p>',
        r'\1' + tour_link, main)

    # any other element emptied by the date strip
    main = re.sub(r'<(span|p)([^>]*)>\s*</\1>', '', main)

    return ('<main class="w-full px-margin-mobile md:px-gutter max-w-container-max mx-auto '
            'pb-section-gap-desktop space-y-section-gap-mobile md:space-y-24" id="main">'
            + intro_html + ZILLOW_NOTE + main + '</main>')


# ==========================================================================
# LEGAL PAGES
# ==========================================================================
def build_legal(stem):
    main = clean(grab_main(read(stem)))
    # These documents have never been published; dating them 2024 would claim a
    # history they do not have. Set to first-publication date.
    main = re.sub(r'Last Updated:\s*[A-Z][a-z]+\s+\d{1,2},\s*\d{4}',
                  f'Last Updated: {LEGAL_DATE}', main)
    main = re.sub(r'<button([^>]*)>\s*Contact Us\s*</button>',
                  r'<a\1 href="about.html#contact">Contact Us</a>', main)
    # tag the sidebar table of contents so site.js can highlight it
    main = re.sub(r'(<(?:nav|div|ul)[^>]*>)(\s*(?:<[^>]+>\s*)?(?:Contents))',
                  r'\1\2', main)
    cls = ('flex-grow pt-12 pb-section-gap-desktop' if stem == 'terms' else 'w-full')
    return f'<main class="{cls}" id="main">{main}</main>'


# ==========================================================================
# 404 — GitHub Pages serves this for any unknown path
# ==========================================================================
def build_404():
    return f'''<main class="flex-grow flex items-center justify-center px-margin-mobile md:px-gutter py-section-gap-mobile md:py-section-gap-desktop" id="main">
<div class="max-w-2xl text-center">
<p class="font-label-bold text-label-bold uppercase text-heritage-gold mb-4">Error 404</p>
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-deep-navy mb-4">We could not find that page</h1>
<p class="font-body-lg text-body-lg text-slate-gray mb-10">The link may be out of date, or the page may have moved. Here is where most visitors are heading.</p>
<div class="flex flex-wrap gap-4 justify-center">
<a class="bg-deep-navy text-surface-off-white px-8 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors" href="/properties.html">Browse our properties</a>
<a class="bg-transparent border border-heritage-gold text-deep-navy px-8 py-3 rounded font-label-bold text-label-bold hover:bg-heritage-gold/10 transition-colors" href="/">Back to the home page</a>
</div>
<p class="font-body-md text-body-md text-slate-gray mt-10">Looking for something specific? Call us on <a class="text-deep-navy font-bold hover:text-heritage-gold" href="{PHONE_HREF}">{PHONE_TEXT}</a>.</p>
</div>
</main>'''


# ==========================================================================
# assemble
# ==========================================================================
BUILDERS = {'home': build_home, 'about': build_about, 'properties': build_properties,
            'privacy': lambda: build_legal('privacy'), 'terms': lambda: build_legal('terms'),
            '404': build_404}

BODY_CLASS = ('bg-surface-off-white text-on-background font-body-md antialiased '
              'min-h-screen flex flex-col selection:bg-heritage-gold/30 selection:text-deep-navy')


def main():
    os.makedirs(OUT, exist_ok=True)
    for stem, outname, navkey, title, desc in PAGES:
        body = BUILDERS[stem]()
        page = (head(title, desc, outname, stem) + '\n'
                + f'<body class="{BODY_CLASS}">\n'
                + header(navkey) + '\n'
                + body + '\n'
                + FOOTER + '\n'
                + '<script src="assets/js/site.js" defer></script>\n'
                + '</body>\n</html>\n')
        page = icons_to_entities(page)
        if outname == '404.html':
            page = page.replace('href="assets/', 'href="/assets/')
            page = page.replace('src="assets/', 'src="/assets/')
            page = re.sub(r'href="(index|about|properties|privacy|terms)\.html"',
                          r'href="/\1.html"', page)
            page = page.replace('href="about.html#contact"', 'href="/about.html#contact"')
        with open(os.path.join(OUT, outname), 'w', encoding='utf-8') as f:
            f.write(page)
        print(f'  wrote {outname:18s} {len(page)//1024}KB')

    leftovers = 0
    for _, outname, *_ in PAGES:
        s = open(os.path.join(OUT, outname), encoding='utf-8').read()
        stray = re.findall(r'material-symbols-outlined[^>]*>\s*([a-z][a-z_0-9]{2,})\s*<', s)
        if stray:
            print(f'  !! {outname}: icon names left as text {sorted(set(stray))}')
            leftovers += len(stray)
        for bad, label in [('DATA:SCREEN', 'screen placeholder'),
                           ('lh3.googleusercontent', 'dead image URL'),
                           ('cdn.tailwindcss.com', 'tailwind CDN'),
                           ('C:\\', 'windows path'),
                           ('44302', 'wrong zip'),
                           ('rounded-DEFAULT', 'bad radius class'),
                           ('2024 Yoak', 'stale copyright')]:
            n = s.count(bad)
            if n:
                print(f'  !! {outname}: {n}x {label}')
                leftovers += n
    print('  leftovers:', leftovers)
    return 0 if leftovers == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
