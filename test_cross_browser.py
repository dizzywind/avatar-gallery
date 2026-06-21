import asyncio
from playwright.async_api import async_playwright

async def test_cross_browser():
    async with async_playwright() as p:
        for browser_type in [p.chromium, p.firefox, p.webkit]:
            browser_name = browser_type.name
            print(f"\n=== Testing {browser_name} ===")
            browser = await browser_type.launch()
            page = await browser.new_page()
            
            try:
                page.on("console", lambda msg: print(f"  CONSOLE [{msg.type}]: {msg.text}"))
                page.on("pageerror", lambda err: print(f"  PAGE ERROR: {err}"))
                
                # Test all viewports
                for width, name in [(375, "Mobile"), (768, "Tablet"), (1280, "Desktop")]:
                    await page.set_viewport_size({"width": width, "height": 800})
                    await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
                    await page.wait_for_timeout(2000)
                    
                    # Grid check
                    grid = page.locator("#lotusGalleryGrid")
                    items = await grid.locator(".gallery-item").all()
                    
                    # Get grid columns via JS that works cross-browser
                    col_count = await grid.evaluate("""el => {
                        const style = window.getComputedStyle(el);
                        const cols = style.gridTemplateColumns || style.getPropertyValue('grid-template-columns');
                        return cols === '1fr' ? 1 : cols.split(' ').length;
                    }""")
                    
                    # Lightbox check
                    await page.locator(".gallery-item").first.click()
                    await page.wait_for_timeout(500)
                    lightbox = page.locator("#lightbox")
                    hidden = await lightbox.get_attribute("hidden")
                    opens = hidden is None
                    
                    if opens:
                        await page.locator("#lightboxClose").click(force=True)
                        await page.wait_for_timeout(500)
                        hidden = await lightbox.get_attribute("hidden")
                        closes = hidden is not None
                    else:
                        closes = False
                    
                    print(f"  {name} ({width}px): {col_count} cols, lightbox open={opens}, close={closes}")
                
            except Exception as e:
                print(f"  ERROR: {e}")
            finally:
                await browser.close()

asyncio.run(test_cross_browser())
