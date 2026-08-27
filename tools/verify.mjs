import { chromium } from 'playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve('site');
const MIME = {'.html':'text/html','.css':'text/css','.js':'text/javascript','.png':'image/png','.jpg':'image/jpeg','.xml':'application/xml','.txt':'text/plain'};
const server = http.createServer((req,res)=>{
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(ROOT,p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404,{'Content-Type':'text/html'});
    return res.end(fs.readFileSync(path.join(ROOT,'404.html')));
  }
  res.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});
  res.end(fs.readFileSync(f));
});
await new Promise(r=>server.listen(8899,r));

const PAGES=['index.html','about.html','properties.html','privacy.html','terms.html','404.html'];
const browser = await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
let problems = [];

for (const view of [{name:'desktop',width:1440,height:1000},{name:'mobile',width:390,height:844}]) {
  const ctx = await browser.newContext({viewport:{width:view.width,height:view.height}, deviceScaleFactor:1});
  for (const pg of PAGES) {
    const page = await ctx.newPage();
    const consoleErrs=[], failed=[];
    page.on('console', m=>{ if(m.type()==='error') consoleErrs.push(m.text()); });
    page.on('requestfailed', r=>failed.push(r.url()));
    const resp = [];
    page.on('response', r=>{ if(r.status()>=400) resp.push(r.status()+' '+r.url()); });

    await page.goto(`http://127.0.0.1:8899/${pg}`, {waitUntil:'networkidle', timeout:30000});
    // scroll the whole page so loading="lazy" images actually fetch
    await page.evaluate(async () => {
      const step = window.innerHeight * 0.6;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2500);

    // broken images
    const brokenImgs = await page.$$eval('img', els => els.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.getAttribute('src')));
    // horizontal overflow
    const overflow = await page.evaluate(()=> document.documentElement.scrollWidth - document.documentElement.clientWidth);
    // dead controls: buttons with no handler & no form, links with empty/# href
    const deadLinks = await page.$$eval('a', els => els.filter(a=>{
      const h=a.getAttribute('href'); return !h || h==='#' || h.startsWith('{{') || h.startsWith('C:');
    }).map(a=>a.textContent.trim().slice(0,40)));
    const bareButtons = await page.$$eval('button', els => els.filter(b=>!b.id&&b.type!=='submit').map(b=>b.textContent.trim().slice(0,40)));
    // visible raw ligature text (icon font failed AND text showing)
    const h1 = await page.$$eval('h1', e=>e.length);

    const tag = `${view.name}/${pg}`;
    if (brokenImgs.length) problems.push(`${tag}: broken images ${JSON.stringify(brokenImgs)}`);
    if (overflow > 1) problems.push(`${tag}: horizontal overflow ${overflow}px`);
    if (deadLinks.length) problems.push(`${tag}: dead links ${JSON.stringify(deadLinks)}`);
    if (bareButtons.length) problems.push(`${tag}: non-functional buttons ${JSON.stringify(bareButtons)}`);
    if (h1 !== 1) problems.push(`${tag}: ${h1} <h1> elements (want exactly 1)`);
    if (resp.length) problems.push(`${tag}: bad responses ${JSON.stringify(resp)}`);
    if (failed.filter(u=>!u.includes('fonts.g')).length) problems.push(`${tag}: request failed ${JSON.stringify(failed.filter(u=>!u.includes('fonts.g')))}`);
    const realErrs = consoleErrs.filter(e => !/ERR_TUNNEL_CONNECTION_FAILED|fonts\.g/.test(e));
    if (realErrs.length) problems.push(`${tag}: console ${JSON.stringify(realErrs)}`);

    await page.screenshot({path:`shots/${view.name}-${pg.replace('.html','')}.png`, fullPage:true});

    // mobile menu behaviour
    if (view.name==='mobile' && pg==='index.html') {
      const t = await page.$('#nav-toggle');
      await t.click(); await page.waitForTimeout(350);
      const open = await page.$eval('#mobile-nav', e=>!e.classList.contains('hidden'));
      if (!open) problems.push('mobile menu did not open');
      const visible = await page.$eval('#mobile-nav', e=>e.getBoundingClientRect().height>0);
      if (!visible) problems.push('mobile menu has zero height when open');
      await page.screenshot({path:'shots/mobile-menu-open.png'});
      await page.keyboard.press('Escape'); await page.waitForTimeout(300);
      const closed = await page.$eval('#mobile-nav', e=>e.classList.contains('hidden'));
      if (!closed) problems.push('mobile menu did not close on Escape');
    }
    await page.close();
  }
  await ctx.close();
}
await browser.close();
server.close();
console.log(problems.length ? 'PROBLEMS:\n'+problems.join('\n') : 'ALL CHECKS PASSED');
