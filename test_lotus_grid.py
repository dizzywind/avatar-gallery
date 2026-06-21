import asyncio
from playwright.async_api import async_playwright

async def test_lotus_grid():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Capture console messages
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        # Test at mobile viewport (375px)
        await page.set_viewport_size({"width": 375, "height": 800})
        await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)  # wait for JS to render
        
        # Check grid layout
        grid = page.locator("#lotusGalleryGrid")
        items = await grid.locator(".gallery-item").all()
        print(f"Mobile (375px): {len(items)} items found")
        
        # Get grid computed styles
        grid_styles = await grid.evaluate("el => window.getComputedStyle(el)")
        print(f"  grid-template-columns: {grid_styles['gridTemplateColumns']}")
        print(f"  display: {grid_styles['display']}")
        
        # Check if items overflow
        for i, item in enumerate(items):
            box = await item.bounding_box()
            if box:
                print(f"  Item {i}: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
        
        # Test at tablet viewport (768px)
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.wait_for_timeout(500)
        
        items = await grid.locator(".gallery-item").all()
        print(f"\nTablet (768px): {len(items)} items found")
        
        grid_styles = await grid.evaluate("el => window.getComputedStyle(el)")
        print(f"  grid-template-columns: {grid_styles['gridTemplateColumns']}")
        
        for i, item in enumerate(items):
            box = await item.bounding_box()
            if box:
                print(f"  Item {i}: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
        
        # Test at desktop viewport (1280px)
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.wait_for_timeout(500)
        
        items = await grid.locator(".gallery-item").all()
        print(f"\nDesktop (1280px): {len(items)} items found")
        
        grid_styles = await grid.evaluate("el => window.getComputedStyle(el)")
        print(f"  grid-template-columns: {grid_styles['gridTemplateColumns']}")
        
        for i, item in enumerate(items):
            box = await item.bounding_box()
            if box:
                print(f"  Item {i}: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
        
        await browser.close()

asyncio.run(test_lotus_grid())
