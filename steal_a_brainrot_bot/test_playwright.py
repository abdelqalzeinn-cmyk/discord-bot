import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('https://www.roblox.com/games/109983668079237/Steal-a-Brainrot')
            title = await page.title()
            print(f"Success! Page title: {title}")
            await browser.close()
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_playwright())
    if result:
        print("Playwright is working correctly!")
    else:
        print("There was an issue with Playwright.")
