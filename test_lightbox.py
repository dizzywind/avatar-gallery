import asyncio
from playwright.async_api import async_playwright

async def test_lightbox():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        # Test lightbox on mobile
        await page.set_viewport_size({"width": 375, "height": 800})
        await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Click first gallery item
        first_item = page.locator(".gallery-item").first
        await first_item.click()
        await page.wait_for_timeout(500)
        
        lightbox = page.locator("#lightbox")
        is_visible = await lightbox.is_visible()
        print(f"Mobile lightbox visible: {is_visible}")
        
        if is_visible:
            # Check image loaded
            img = page.locator("#lightboxImage")
            src = await img.get_attribute("src")
            print(f"  Lightbox image src: {src}")
            
            # Close lightbox
            await page.locator("#lightboxClose").click()
            await page.wait_for_timeout(300)
            is_visible = await lightbox.is_visible()
            print(f"  Lightbox closed: {not is_visible}")
        
        # Test lightbox on desktop
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.wait_for_timeout(500)
        
        first_item = page.locator(".gallery-item").first
        await first_item.click()
        await page.wait_for_timeout(500)
        
        lightbox = page.locator("#lightbox")
        is_visible = await lightbox.is_visible()
        print(f"\nDesktop lightbox visible: {is_visible}")
        
        if is_visible:
            img = page.locator("#lightboxImage")
            src = await img.get_attribute("src")
            print(f"  Lightbox image src: {src}")
            
            # Test navigation
            await page.locator("#lightboxNext").click()
            await page.wait_for_timeout(300)
            src2 = await img.get_attribute("src")
            print(f"  After next click: {src2}")
            
            await page.locator("#lightboxClose").click()
            await page.wait_for_timeout(300)
            is_visible = await lightbox.is_visible()
            print(f"  Lightbox closed: {not is_visible}")
        
        await browser.close()

asyncio.run(test_lightbox())
