import asyncio
from playwright.async_api import async_playwright

async def test_lightbox():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        # Test at all three viewports
        for width, name in [(375, "Mobile"), (768, "Tablet"), (1280, "Desktop")]:
            print(f"\n=== {name} ({width}px) ===")
            await page.set_viewport_size({"width": width, "height": 800})
            await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Click first gallery item
            first_item = page.locator(".gallery-item").first
            await first_item.click()
            await page.wait_for_timeout(500)
            
            lightbox = page.locator("#lightbox")
            is_visible = await lightbox.is_visible()
            print(f"  Lightbox opens: {is_visible}")
            
            if is_visible:
                # Check image loaded
                img = page.locator("#lightboxImage")
                src = await img.get_attribute("src")
                print(f"  Lightbox image: {src}")
                
                # Test navigation on desktop
                if name == "Desktop":
                    await page.locator("#lightboxNext").click()
                    await page.wait_for_timeout(300)
                    src2 = await img.get_attribute("src")
                    print(f"  Next image: {src2}")
                    
                    await page.locator("#lightboxPrev").click()
                    await page.wait_for_timeout(300)
                    src3 = await img.get_attribute("src")
                    print(f"  Prev image: {src3}")
                
                # Close lightbox
                await page.locator("#lightboxClose").click(force=True)
                await page.wait_for_timeout(300)
                
                is_visible = await lightbox.is_visible()
                hidden = await lightbox.get_attribute("hidden")
                print(f"  Lightbox closes: {not is_visible}, hidden attr present: {hidden is not None}")
                
                # Verify body overflow restored
                overflow = await page.evaluate("() => document.body.style.overflow")
                print(f"  Body overflow restored: {overflow == ''}")
        
        await browser.close()

asyncio.run(test_lightbox())
