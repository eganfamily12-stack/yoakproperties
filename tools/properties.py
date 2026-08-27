"""Properties page, generated from site/data/listings.json.

The mockup hard-coded three agents and their addresses directly into HTML, which
had already gone stale by the time it reached us: two of the six agent documents
on the leasing Linktree were advertising open houses that had passed. Driving the
page from a data file means updating inventory is one JSON edit, and the page can
be honest about staleness on its own.

Listing cards are deliberately text-first. There are 13 photographs available and
25 listings, so putting an image on every card would mean showing the same photo
against several different addresses — worse than no photo, because it implies the
picture is of that house. The real interiors appear once, in a labelled gallery.
"""

import calendar
import json
import os
import re

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

BEDBATH_CHIP = ('inline-flex items-center gap-1.5 bg-surface-container-low '
                'text-on-surface-variant font-caption text-caption px-2.5 py-1 rounded-full')

GALLERY = [
    ('interior-kitchen-white.jpg', 'Kitchen with white cabinetry in a Yoak Properties home'),
    ('interior-living-fireplace.jpg', 'Living room with an original fireplace'),
    ('interior-sunroom.jpg', 'Sunroom with wraparound windows'),
    ('interior-bath.jpg', 'Updated bathroom'),
    ('interior-kitchen-classic.jpg', 'Kitchen with full-size appliances'),
    ('interior-living-carpet.jpg', 'Carpeted living room'),
]


def load(outdir):
    with open(os.path.join(outdir, 'data', 'listings.json'), encoding='utf-8') as f:
        return json.load(f)


def addr_slug(l):
    bits = [l['address'], l['city'], l['state']]
    if l.get('zip'):
        bits.append(l['zip'])
    s = re.sub(r'[^A-Za-z0-9 ]', '', ' '.join(bits))
    return re.sub(r'\s+', '-', s.strip())


def fmt_12h(hhmm):
    h, m = (int(x) for x in hhmm.split(':'))
    return f'{h % 12 or 12}:{m:02d} ' + ('AM' if h < 12 else 'PM')


def fmt_open_house(iso, end):
    d, tm = iso.split('T')
    y, mo, dy = (int(x) for x in d.split('-'))
    wd = calendar.weekday(y, mo, dy)
    span = fmt_12h(tm)
    if end:
        span = f'{fmt_12h(tm)} &ndash; {fmt_12h(end)}'
    return f'{DAYS[wd]}, {dy} {MONTHS[mo - 1]} &middot; {span}'


def num(v):
    """4.0 -> 4, 1.5 -> 1.5"""
    return int(v) if float(v).is_integer() else v


def upcoming_listings(cfg, today, limit=None):
    """Listings whose open house is still ahead, soonest first."""
    data = load(cfg['OUT'])
    out = []
    for a in data['agents']:
        for l in a['listings']:
            if l.get('openHouse') and l['openHouse'][:10] >= today:
                out.append(dict(l, agent=a['name'], phone=a.get('phone')))
    out.sort(key=lambda l: l['openHouse'])
    return out[:limit] if limit else out


def build(cfg, img, today):
    """cfg carries the shared constants from transform.py; img is its <img> helper."""

    def is_past(iso):
        return iso is None or iso[:10] < today

    def card(l):
        zurl = cfg['ZILLOW_ADDR'].format(slug=addr_slug(l))
        where = f"{l['city']}, {l['state']}" + (f" {l['zip']}" if l.get('zip') else '')

        chips = []
        if l.get('beds') is not None:
            chips.append(f'<span class="{BEDBATH_CHIP}"><span aria-hidden="true" '
                         f'class="material-symbols-outlined text-[15px]">bed</span>'
                         f'{num(l["beds"])} bed</span>')
        if l.get('baths') is not None:
            chips.append(f'<span class="{BEDBATH_CHIP}"><span aria-hidden="true" '
                         f'class="material-symbols-outlined text-[15px]">plumbing</span>'
                         f'{num(l["baths"])} bath</span>')
        chips_html = (f'<div class="flex flex-wrap gap-2 mb-4">{"".join(chips)}</div>'
                      if chips else '')

        rent = ''
        if l.get('rent'):
            rent = (f'<p class="font-headline-md text-body-lg text-deep-navy mb-3">'
                    f'${l["rent"]:,}<span class="font-body-md text-body-md text-slate-gray">'
                    f'/mo</span></p>')

        note = ''
        if l.get('note'):
            note = (f'<span class="self-start bg-soft-gold text-deep-navy font-caption '
                    f'text-caption px-3 py-1 rounded-full font-semibold uppercase '
                    f'tracking-wider mb-3">{l["note"]}</span>')

        # When an open house has passed we show the Zillow link instead, so a
        # stale time is never presented as upcoming. site.js applies the same
        # swap in the browser for visitors arriving after this build ran.
        zrow = (f'<a class="font-label-bold text-label-bold text-heritage-gold hover:underline '
                f'inline-flex items-center gap-1.5" href="{zurl}" rel="noopener" target="_blank">'
                f'<span aria-hidden="true" class="material-symbols-outlined text-[17px]">event'
                f'</span>Open house times on Zillow</a>')

        if l.get('openHouse') and not is_past(l['openHouse']):
            when = fmt_open_house(l['openHouse'], l.get('openHouseEnd'))
            row = (f'<div class="mb-4" data-openhouse="{l["openHouse"]}">'
                   f'<p class="font-body-md text-body-md text-deep-navy flex items-start gap-2">'
                   f'<span aria-hidden="true" class="material-symbols-outlined text-[19px] '
                   f'text-heritage-gold shrink-0 mt-0.5">event</span>'
                   f'<span><span class="font-semibold">Open house</span><br/>{when}</span></p>'
                   f'<template data-openhouse-fallback>{zrow}</template></div>')
        else:
            row = f'<div class="mb-4">{zrow}</div>'

        return (
            f'<article class="bg-surface-container-lowest rounded-xl shadow-card '
            f'border border-outline-variant/20 p-6 flex flex-col hover:shadow-card-hover '
            f'hover:border-b-heritage-gold transition-all duration-300">{note}'
            f'<h4 class="font-headline-md text-headline-md text-deep-navy leading-snug mb-1">'
            f'{l["address"]}</h4>'
            f'<p class="font-body-md text-body-md text-slate-gray mb-4">{where}</p>'
            f'{chips_html}{rent}'
            f'<div class="mt-auto pt-4 border-t border-outline-variant/20">{row}'
            f'<a class="inline-flex items-center justify-center gap-2 w-full font-label-bold '
            f'text-label-bold bg-deep-navy text-surface-off-white px-5 py-2.5 rounded '
            f'hover:bg-primary-container transition-colors" href="{zurl}" rel="noopener" '
            f'target="_blank">View &amp; apply on Zillow <span aria-hidden="true" '
            f'class="material-symbols-outlined text-[17px]">arrow_outward</span></a></div></article>')

    data = load(cfg['OUT'])
    agents = data['agents']
    total = sum(len(a['listings']) for a in agents)
    upcoming = sum(1 for a in agents for l in a['listings']
                   if l.get('openHouse') and not is_past(l['openHouse']))

    sections = []
    for a in agents:
        ls = sorted(a['listings'],
                    key=lambda l: (is_past(l.get('openHouse')), l.get('openHouse') or 'z'))
        phone = ''
        if a.get('phone'):
            digits = a['phone'].replace('-', '')
            phone = (f'<a class="font-body-md text-body-md text-heritage-gold hover:underline '
                     f'inline-flex items-center gap-1.5" href="tel:+1{digits}">'
                     f'<span aria-hidden="true" class="material-symbols-outlined text-[17px]">'
                     f'call</span>{a["phone"]}</a>')
        sections.append(
            f'<section class="scroll-mt-28" id="{a["name"].lower()}">'
            f'<div class="flex flex-wrap items-center gap-4 mb-8 pb-4 border-b '
            f'border-outline-variant/30">'
            f'<span aria-hidden="true" class="w-14 h-14 shrink-0 rounded-full bg-deep-navy '
            f'text-heritage-gold font-headline-md text-headline-md flex items-center '
            f'justify-center border-2 border-heritage-gold">{a["name"][0]}</span>'
            f'<div class="min-w-0"><h3 class="font-headline-lg text-headline-lg-mobile '
            f'md:text-headline-lg text-deep-navy">{a["name"]}&#8217;s Listings</h3>'
            f'<p class="font-body-md text-body-md text-slate-gray">{a["area"]}</p></div>'
            f'<div class="ml-auto">{phone}</div></div>'
            f'<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-gutter">'
            f'{"".join(card(l) for l in ls)}</div></section>')

    gallery = ''.join(
        '<figure class="overflow-hidden rounded-xl bg-surface-container">'
        + img('assets/img/' + f, alt,
              'w-full h-56 object-cover hover:scale-105 transition-transform duration-700',
              w=800, h=600)
        + '</figure>'
        for f, alt in GALLERY)

    oh_word = 'open house' if upcoming == 1 else 'open houses'

    return f'''<main class="w-full px-margin-mobile md:px-gutter max-w-container-max mx-auto pb-section-gap-desktop" id="main">
<section class="w-full pt-16 pb-10 md:pt-24 md:pb-14 text-center">
<h1 class="font-headline-xl text-headline-lg-mobile md:text-headline-xl text-deep-navy mb-4">Our Properties</h1>
<p class="font-body-lg text-body-lg text-slate-gray max-w-2xl mx-auto">Rental homes across Akron, Canton, Barberton, Massillon and the surrounding communities, managed by our own leasing and maintenance teams.</p>
</section>

<div class="bg-soft-gold border-l-4 border-heritage-gold rounded p-6 md:p-8 mb-14 flex flex-col lg:flex-row lg:items-center gap-6 justify-between">
<div class="max-w-3xl">
<h2 class="font-headline-md text-headline-md text-deep-navy mb-2 flex items-center gap-2"><span aria-hidden="true" class="material-symbols-outlined text-heritage-gold">event</span>Open houses and applications run through Zillow</h2>
<p class="font-body-md text-body-md text-on-surface-variant">Applications are submitted on Zillow &mdash; {cfg['APP_FEE']}, valid 30 days across every Yoak property. Times below were accurate on {cfg['BUILD_DATE_TEXT']}, and the Zillow listing is always authoritative, so check there before you travel. <a class="text-secondary font-semibold hover:underline" href="faq.html">Full qualifying criteria and how to apply &rarr;</a></p>
</div>
<div class="shrink-0 flex flex-col gap-2">
<a class="bg-deep-navy text-surface-off-white px-6 py-3 rounded font-label-bold text-label-bold hover:bg-primary-container transition-colors inline-flex items-center justify-center gap-2" href="{cfg['APPLY_URL']}" rel="noopener" target="_blank">See all current listings <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></a>
<p class="font-caption text-caption text-on-surface-variant text-center">{upcoming} {oh_word} coming up</p>
</div>
</div>

<div class="space-y-20">{''.join(sections)}</div>

<section class="mt-24">
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-deep-navy mb-2">Inside our homes</h2>
<p class="font-body-md text-body-md text-slate-gray mb-8 max-w-3xl">A look at recent Yoak renovations. These show the standard of finish across the portfolio rather than any one address &mdash; photographs of a specific property are on its Zillow listing.</p>
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-gutter">{gallery}</div>
</section>

<section class="mt-24 py-16 bg-deep-navy rounded-2xl text-center px-6 relative overflow-hidden">
<div class="absolute inset-0 opacity-10" style="background-image: radial-gradient(circle at 50% 50%, #ffffff 1px, transparent 1px); background-size: 24px 24px;"></div>
<div class="relative z-10 max-w-2xl mx-auto">
<span aria-hidden="true" class="material-symbols-outlined text-heritage-gold" style="font-size:44px">real_estate_agent</span>
<h2 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-surface-off-white mt-3 mb-4">Ready to make a move?</h2>
<p class="font-body-lg text-body-lg text-surface-variant/80 mb-8">Come to any open house above, or apply on Zillow first &mdash; approved applicants can book a private tour of any property we manage.</p>
<div class="flex flex-wrap gap-4 justify-center">
<a class="bg-heritage-gold text-deep-navy px-8 py-3 rounded font-label-bold text-label-bold hover:-translate-y-1 hover:shadow-lg transition-all inline-flex items-center gap-2" href="{cfg['APPLY_URL']}" rel="noopener" target="_blank">Apply on Zillow <span aria-hidden="true" class="material-symbols-outlined text-base">arrow_outward</span></a>
<a class="border-2 border-surface-off-white text-surface-off-white px-8 py-3 rounded font-label-bold text-label-bold hover:bg-surface-off-white/10 transition-colors" href="faq.html">Read the requirements</a>
</div>
</div>
</section>
</main>'''
