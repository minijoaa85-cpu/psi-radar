"""Real-engine, real-DOM PSI Radar UI smoke checks (Chromium, Firefox, WebKit).

Runs a local static server over the actual site/ files. Desktop, tablet and
mobile viewports are emulations, not a guarantee for every hardware/browser.
"""
from __future__ import annotations
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import sys

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
VIEWPORTS={"desktop":(1440,900),"tablet":(820,1100),"mobile":(390,844),"small_phone":(360,740)}
SCREENS=ROOT/"ui-smoke-screenshots"

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt,*args):pass

def check_page(browser,engine,screen,width,height,url):
    context=browser.new_context(viewport={"width":width,"height":height},locale="ko-KR")
    page=context.new_page()
    page.set_default_timeout(9000)
    errors=[]
    page.on("pageerror",lambda err:errors.append(str(err)))
    try:
        res=page.goto(url,wait_until="domcontentloaded",timeout=30000)
        assert res is not None and res.status==200,f"HTTP {res.status if res else 'none'}"
        nav=page.locator("#nav")
        assert nav.is_visible()
        assert nav.locator(".nav-group").count()==4
        assert nav.locator('button[data-tab="overview"]').is_visible()
        assert not nav.locator('button[data-tab="watchlist"]').count()
        assert not nav.locator('button[data-tab="sources"]').count()
        # Check actual computed typography and horizontal clipping in the browser.
        sizes=page.evaluate("""() => {
          const h=document.querySelector('.nav-group-label');
          const b=document.querySelector('.nav-group button');
          return {heading:parseFloat(getComputedStyle(h).fontSize),
                  link:parseFloat(getComputedStyle(b).fontSize),
                  overflow:document.documentElement.scrollWidth-window.innerWidth};
        }""")
        assert sizes["heading"]>=13.5,sizes
        assert sizes["link"]>=12.5,sizes
        assert sizes["overflow"]<=4,f"Horizontal document overflow: {sizes}"
        nav.locator('button[data-tab="weekly"]').click()
        assert page.locator("#weekly").is_visible()
        nav.locator('button[data-tab="market"]').click()
        assert page.locator("#market").is_visible()
        page.locator(".finance-card").first.wait_for(timeout=12000)
        assert page.locator(".finance-card").count()==4
        page.locator("#finance-company").select_option("st")
        assert page.locator(".finance-card").count()==1
        assert "STMicroelectronics" in page.locator(".finance-card h3").first.inner_text()
        page.locator("#finance-company").select_option("rohm")
        assert "6개월 누적" in page.locator(".finance-card").first.inner_text()
        page.locator("#finance-metric").select_option("profitability")
        assert page.locator(".finance-bars").is_visible()
        page.locator("#finance-company").select_option("")
        assert page.locator(".finance-card").count()==4
        # IR observations are separate from verified financial metrics.
        page.locator("#finance-ir-status").wait_for(timeout=15000)
        assert "최근 IR 목록 점검" in page.locator("#finance-ir-status").inner_text()
        assert page.locator("#finance-ir-sources .finance-ir-source").count()==4
        page.locator("#finance-show-known").check()
        page.locator("#finance-show-known").uncheck()
        nav.locator('button[data-tab="integrated"]').click()
        assert page.locator("#integrated").is_visible()
        page.locator("#intel-categories button").first.wait_for(timeout=12000)
        page.locator("#intel-categories button").filter(has_text="SJ MOSFET").click()
        assert page.locator("#intel-physics-title").inner_text().startswith("SJ MOSFET")
        nav.locator('button[data-tab="competitors"]').click()
        assert page.locator("#competitors").is_visible()
        nav.locator('button[data-tab="benchmark"]').click()
        assert page.locator("#benchmark").is_visible()
        page.locator("#watch-quick-access").click()
        assert page.locator("#watchlist").is_visible()
        assert page.locator("#watch-techs input").count()==5
        page.locator('#watch-close').click()
        assert page.locator("#benchmark").is_visible()
        page.locator("#quality-quick-access").click()
        assert page.locator("#sources").is_visible()
        page.locator("#quality-close").click()
        assert page.locator("#benchmark").is_visible()
        nav.locator('button[data-tab="overview"]').click()
        assert page.locator("#overview").is_visible()
        if errors:raise AssertionError("JavaScript errors: "+"; ".join(errors[:5]))
        print(f"PASS {engine:8} {screen:11} {width}x{height} heading={sizes['heading']}px link={sizes['link']}px",flush=True)
    except Exception:
        SCREENS.mkdir(exist_ok=True)
        page.screenshot(path=str(SCREENS/f"{engine}-{screen}-failure.png"),full_page=True)
        raise
    finally:
        context.close()

def main():
    assert SITE.exists()
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(QuietHandler,directory=str(SITE)))
    thread=Thread(target=server.serve_forever,daemon=True)
    thread.start()
    url=f"http://127.0.0.1:{server.server_port}/index.html"
    failures=[]
    try:
        with sync_playwright() as p:
            for engine in ("chromium","firefox","webkit"):
                browser=getattr(p,engine).launch(headless=True)
                try:
                    for screen,(width,height) in VIEWPORTS.items():
                        try:check_page(browser,engine,screen,width,height,url)
                        except Exception as exc:
                            print(f"FAIL {engine} {screen}: {exc}",file=sys.stderr,flush=True)
                            failures.append(f"{engine}/{screen}: {exc}")
                finally:browser.close()
    finally:
        server.shutdown()
        server.server_close()
    if failures:
        raise SystemExit(f"{len(failures)} UI smoke checks failed")
    print("PASS 12 real-engine viewport smoke checks",flush=True)

if __name__=="__main__":main()
