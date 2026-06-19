import asyncio
from playwright.async_api import async_playwright

async def test_lightbox():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        # Test lightbox on desktop
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Click first gallery item
        first_item = page.locator(".gallery-item").first
        await first_item.click()
        await page.wait_for_timeout(500)
        
        lightbox = page.locator("#lightbox")
        is_visible = await lightbox.is_visible()
        print(f"Lightbox visible: {is_visible}")
        
        if is_visible:
            # Check close button
            close_btn = page.locator("#lightboxClose")
            btn_visible = await close_btn.is_visible()
            btn_enabled = await close_btn.is_enabled()
            print(f"Close button - visible: {btn_visible}, enabled: {btn_enabled}")
            
            # Get bounding boxes
            lb_box = await lightbox.bounding_box()
            btn_box = await close_btn.bounding_box()
            print(f"Lightbox box: {lb_box}")
            print(f"Close button box: {btn_box}")
            
            # Try clicking with force
            await close_btn.click(force=True)
            await page.wait_for_timeout(500)
            
            is_visible = await lightbox.is_visible()
            print(f"After click - Lightbox visible: {is_visible}")
            
            # Check if hidden attribute is set
            hidden = await lightbox.get_attribute("hidden")
            print(f"Hidden attribute: {hidden}")
        
        await browser.close()

asyncio.run(test_lightbox())
