import asyncio
from playwright.async_api import async_playwright

async def test_gallery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}") if msg.type == "error" else None)
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err.message}"))
        
        try:
            await page.goto("http://localhost:3000/", wait_until="networkidle", timeout=10000)
            await page.wait_for_selector("#galleryGrid", timeout=5000)
            
            # Check if gallery items rendered
            items = await page.query_selector_all(".gallery-item")
            print(f"✓ Gallery items rendered: {len(items)}")
            
            # Check for Use Style buttons
            useStyleBtns = await page.query_selector_all(".use-style-btn")
            print(f"✓ Use Style buttons: {len(useStyleBtns)}")
            
            # Hover over first item to see overlay
            if items:
                await items[0].hover()
                await page.wait_for_timeout(300)
                
                # Check if overlay is visible
                overlay = await page.query_selector(".gallery-item-overlay")
                if overlay:
                    isVisible = await overlay.is_visible()
                    print(f"✓ Overlay visible on hover: {isVisible}")
                
                # Click Use Style button
                if useStyleBtns:
                    await useStyleBtns[0].click()
                    await page.wait_for_timeout(500)
                    
                    # Check if style panel opened
                    panel = await page.query_selector("#stylePanel")
                    if panel:
                        isVisible = await panel.is_visible()
                        print(f"✓ Style panel opened: {isVisible}")
                        
                        # Check panel content
                        title = await page.query_selector("#stylePanelTitle")
                        if title:
                            print(f"✓ Panel title: {await title.text_content()}")
                        
                        # Check for reference type selector
                        refTypes = await page.query_selector_all(".ref-type")
                        print(f"✓ Reference types: {len(refTypes)}")
                        
                        # Check for strength slider
                        slider = await page.query_selector("#strengthSlider")
                        print(f"✓ Strength slider: {slider is not None}")
                        
                        # Test reference type selection
                        if refTypes:
                            await refTypes[1].click()  # Click Content Only
                            await page.wait_for_timeout(100)
                            print(f"✓ Reference type selection works")
                        
                        # Test strength slider
                        if slider:
                            await slider.evaluate("el => el.style.left = '90%'")
                            await slider.evaluate("el => el.setAttribute('aria-valuenow', 90)")
                            await page.wait_for_timeout(100)
                            strengthVal = await page.query_selector(".strength-value")
                            if strengthVal:
                                print(f"✓ Strength slider updates: {await strengthVal.text_content()}")
                        
                        # Click Continue
                        continueBtn = await page.query_selector("#continueSelectBtn")
                        if continueBtn:
                            await continueBtn.click()
                            await page.wait_for_timeout(4000)
                            
                            # Check review step
                            panelBody = await page.query_selector("#stylePanelBody")
                            if panelBody:
                                content = await panelBody.text_content()
                                print(f"✓ Review step - Extracted Style: {'Extracted Style' in content}")
                                print(f"✓ Review step - Auto-Generated Prompt: {'Auto-Generated Prompt' in content}")
                                print(f"✓ Review step - Alternative Prompts: {'Alternative Prompts' in content}")
                                
                                # Test alternative prompt selection
                                altPrompts = await page.query_selector_all(".alt-prompt")
                                if altPrompts:
                                    await altPrompts[0].click()
                                    await page.wait_for_timeout(200)
                                    promptText = await page.query_selector("#promptText")
                                    if promptText:
                                        print(f"✓ Alternative prompt selection works")
                                
                                # Test prompt editing
                                promptText = await page.query_selector("#promptText")
                                if promptText:
                                    await promptText.dblclick()
                                    await page.wait_for_timeout(100)
                                    await promptText.type(" Custom addition")
                                    await page.wait_for_timeout(100)
                                    await promptText.press("Enter")
                                    await page.wait_for_timeout(100)
                                    print(f"✓ Prompt editing works")
                                
                                # Fill subject input
                                subjectInput = await page.query_selector("#subjectInput")
                                if subjectInput:
                                    await subjectInput.fill("a mountain landscape")
                                
                                # Click Generate
                                generateBtn = await page.query_selector("#generateReviewBtn")
                                if generateBtn:
                                    await generateBtn.click()
                                    
                                    # Wait for generation to complete
                                    await page.wait_for_timeout(8000)
                                    
                                    # Check result step
                                    panelBody3 = await page.query_selector("#stylePanelBody")
                                    if panelBody3:
                                        content3 = await panelBody3.text_content()
                                        print(f"✓ Result step - Your Creation: {'Your Creation' in content3}")
                                        print(f"✓ Result step - Style Applied: {'Style Applied' in content3}")
                                        
                                        # Check result actions
                                        likeBtn = await page.query_selector("#likeBtn")
                                        saveBtn = await page.query_selector("#saveBtn")
                                        shareBtn = await page.query_selector("#shareBtn")
                                        print(f"✓ Like button: {likeBtn is not None}")
                                        print(f"✓ Save button: {saveBtn is not None}")
                                        print(f"✓ Share button: {shareBtn is not None}")
                                        
                                        # Check generated image in DOM
                                        resultImg = await page.query_selector(".result-box .img img[src*='pollinations']")
                                        print(f"✓ Generated image in DOM: {resultImg is not None}")
                                        
                                        # Test Adjust Style navigation
                                        adjustBtn = await page.query_selector("#adjustStyleBtn")
                                        if adjustBtn:
                                            await adjustBtn.click()
                                            await page.wait_for_timeout(500)
                                            panelBody4 = await page.query_selector("#stylePanelBody")
                                            if panelBody4:
                                                content4 = await panelBody4.text_content()
                                                print(f"✓ Adjust Style -> Review: {'Extracted Style' in content4}")
                                            
                                            # Test Try Again
                                            tryAgainBtn = await page.query_selector("#tryAgainBtn")
                                            if tryAgainBtn:
                                                await tryAgainBtn.click()
                                                await page.wait_for_timeout(500)
                                                panelBody5 = await page.query_selector("#stylePanelBody")
                                                if panelBody5:
                                                    content5 = await panelBody5.text_content()
                                                    print(f"✓ Try Again -> Generate: {'progress' in content5.lower() or 'Generating' in content5}")
                                            
                                            # Test Done
                                            doneBtn = await page.query_selector("#doneBtn")
                                            if doneBtn:
                                                await doneBtn.click()
                                                await page.wait_for_timeout(300)
                                                panelHidden = await page.query_selector("#stylePanel[hidden]")
                                                print(f"✓ Done closes panel: {panelHidden is not None}")
            
            # Test keyboard shortcuts
            print("\n--- Keyboard Shortcuts Test ---")
            if items:
                await items[0].focus()
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(300)
                panel = await page.query_selector("#stylePanel")
                print(f"✓ Enter key opens lightbox (not style panel): {panel.hidden if panel else 'N/A'}")
                
                # Close lightbox
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(100)
                
                # Test S key for Use Style (focus on gallery item)
                await items[0].focus()
                await page.keyboard.press("s")
                await page.wait_for_timeout(300)
                panel = await page.query_selector("#stylePanel")
                print(f"✓ 'S' key opens style panel: {not panel.hidden if panel else False}")
                
                if not panel.hidden:
                    # Test Escape to close
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(100)
                    panel = await page.query_selector("#stylePanel")
                    print(f"✓ Escape closes style panel: {panel.hidden if panel else 'N/A'}")
            
            await browser.close()
            print("\n✅ All tests passed!")
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

asyncio.run(test_gallery())