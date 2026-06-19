import asyncio
from playwright.async_api import async_playwright

async def test_final():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        results = {
            "mobile": {"grid_cols": 0, "lightbox_works": False, "no_horiz_overflow": False},
            "tablet": {"grid_cols": 0, "lightbox_works": False},
            "desktop": {"grid_cols": 0, "lightbox_works": False}
        }
        
        for width, name in [(375, "mobile"), (768, "tablet"), (1280, "desktop")]:
            await page.set_viewport_size({"width": width, "height": 800})
            await page.goto("http://localhost:8888/lotus-gallery.html", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # Grid analysis
            grid = page.locator("#lotusGalleryGrid")
            items = await grid.locator(".gallery-item").all()
            
            grid_styles = await grid.evaluate("el => window.getComputedStyle(el)")
            cols = grid_styles['gridTemplateColumns']
            col_count = len(cols.split()) if cols != '1fr' else 1
            
            # Check for horizontal overflow
            page_width = await page.evaluate("() => document.documentElement.clientWidth")
            max_x = 0
            for item in items:
                box = await item.bounding_box()
                if box:
                    max_x = max(max_x, box['x'] + box['width'])
            
            no_overflow = max_x <= page_width + 10  # small tolerance
            
            print(f"{name.capitalize()} ({width}px):")
            print(f"  Grid columns: {cols}")
            print(f"  Col count: {col_count}")
            print(f"  Items: {len(items)}")
            print(f"  Max item right edge: {max_x:.0f}px (viewport: {page_width}px)")
            print(f"  No horizontal overflow: {no_overflow}")
            
            results[name]["grid_cols"] = col_count
            results[name]["no_horiz_overflow"] = no_overflow
            
            # Lightbox test
            first_item = page.locator(".gallery-item").first
            await first_item.click()
            await page.wait_for_timeout(500)
            
            lightbox = page.locator("#lightbox")
            hidden = await lightbox.get_attribute("hidden")
            lightbox_opens = hidden is None
            
            if lightbox_opens:
                img = page.locator("#lightboxImage")
                src = await img.get_attribute("src")
                print(f"  Lightbox opens: True, image: {src}")
                
                if name == "desktop":
                    # Test navigation
                    await page.locator("#lightboxNext").click()
                    await page.wait_for_timeout(300)
                    src2 = await img.get_attribute("src")
                    await page.locator("#lightboxPrev").click()
                    await page.wait_for_timeout(300)
                    src3 = await img.get_attribute("src")
                    nav_works = src3 == src
                    print(f"  Navigation works: {nav_works}")
                
                # Close
                await page.locator("#lightboxClose").click(force=True)
                await page.wait_for_timeout(500)  # wait for animation
                
                hidden = await lightbox.get_attribute("hidden")
                overflow = await page.evaluate("() => document.body.style.overflow")
                lightbox_closes = hidden is not None and overflow == ''
                print(f"  Lightbox closes: {lightbox_closes} (hidden={hidden is not None}, overflow={overflow})")
                
                results[name]["lightbox_works"] = lightbox_opens and lightbox_closes
            else:
                print(f"  Lightbox opens: False")
                results[name]["lightbox_works"] = False
        
        print("\n=== SUMMARY ===")
        print(f"Mobile (≤400px): {results['mobile']['grid_cols']} col, no overflow: {results['mobile']['no_horiz_overflow']}, lightbox: {results['mobile']['lightbox_works']}")
        print(f"Tablet (768px): {results['tablet']['grid_cols']} cols, lightbox: {results['tablet']['lightbox_works']}")
        print(f"Desktop (1280px): {results['desktop']['grid_cols']} cols, lightbox: {results['desktop']['lightbox_works']}")
        
        # Check criteria
        criteria = {
            "Desktop multi-column": results['desktop']['grid_cols'] >= 2,
            "Tablet 2-3 columns": 2 <= results['tablet']['grid_cols'] <= 3,
            "Mobile single column": results['mobile']['grid_cols'] == 1,
            "Mobile no horizontal overflow": results['mobile']['no_horiz_overflow'],
            "Lightbox works on all viewports": all(results[k]['lightbox_works'] for k in results)
        }
        
        print("\n=== ACCEPTANCE CRITERIA ===")
        all_pass = True
        for criterion, passed in criteria.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {criterion}")
            if not passed:
                all_pass = False
        
        print(f"\nAll criteria met: {all_pass}")
        
        await browser.close()
        return all_pass

asyncio.run(test_final())
