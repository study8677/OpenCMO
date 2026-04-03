"""Capture fresh screenshots of the local OpenCMO UI using Playwright."""
import asyncio
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:8080"
OUT = os.path.join(os.path.dirname(__file__), "video", "public", "screenshots")

PAGES = [
    ("01_dashboard",   "/",                          None),
    ("02_seo",         "/projects/{pid}/seo",         None),
    ("03_serp",        "/projects/{pid}/serp",        None),
    ("04_community",   "/projects/{pid}/community",   None),
    ("05_graph",       "/projects/{pid}/graph",       3000),  # extra wait for 3D render
    ("06_chat",        "/chat",                       None),
]


async def main():
    os.makedirs(OUT, exist_ok=True)

    # Find the first project with data
    import urllib.request, json
    with urllib.request.urlopen(f"{BASE}/api/v1/projects") as r:
        projects = json.loads(r.read())
    if not projects:
        print("No projects found, exiting.")
        return
    pid = projects[0]["id"]
    print(f"Using project {pid}: {projects[0].get('brand_name', projects[0].get('url'))}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        for name, path, extra_wait in PAGES:
            url = BASE + path.replace("{pid}", str(pid))
            print(f"  Capturing {name} → {url}")
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(extra_wait or 1500)
            await page.screenshot(
                path=os.path.join(OUT, f"{name}.png"),
                full_page=False,
            )
            print(f"    ✓ {name}.png saved")

        await browser.close()
    print(f"\nAll screenshots saved to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
