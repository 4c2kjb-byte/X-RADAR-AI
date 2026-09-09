import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
)

from .config import (
    COLLECT_INTERVAL_SECONDS,
    COLLECT_SCROLLS,
    DATA_DIR,
    X_HOME_URL,
)
from .database import add_post


PROFILE_DIR = DATA_DIR / "x-profile"


# =========================
# HELPERS
# =========================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# =========================
# EXTRACT POST
# =========================

async def extract_post(article) -> Dict[str, str]:

    text = ""

    try:
        text = await article.locator(
            '[data-testid="tweetText"]'
        ).inner_text()

    except Exception:
        try:
            text = await article.inner_text()

        except Exception:
            text = ""

    text = clean_text(text)

    author = ""
    username = ""
    url = ""
    post_id = ""

    # -------------------------
    # Author / Username
    # -------------------------

    try:

        links = await article.locator("a").all()

        for link in links:

            href = await link.get_attribute("href")

            if not href:
                continue

            match = re.match(
                r"^/([^/]+)/status/(\d+)",
                href
            )

            if match:

                username = match.group(1)

                post_id = match.group(2)

                url = f"https://x.com{href}"

                break

    except Exception:
        pass


    # -------------------------
    # Display name
    # -------------------------

    try:

        spans = await article.locator(
            '[data-testid="User-Name"]'
        ).inner_text()

        parts = [
            clean_text(x)
            for x in spans.split("\n")
            if clean_text(x)
        ]

        if parts:
            author = parts[0]

        if len(parts) > 1 and not username:
            possible = parts[1]

            if possible.startswith("@"):
                username = possible[1:]

    except Exception:
        pass


    # -------------------------
    # Fallback ID
    # -------------------------

    if not post_id:

        if url:

            match = re.search(
                r"/status/(\d+)",
                url
            )

            if match:
                post_id = match.group(1)


    return {
        "post_id": post_id,
        "author": author,
        "username": username,
        "text": text,
        "url": url,
        "created_at": "",
        "collected_at": utc_now(),
        "source": "x_for_you",
    }


# =========================
# COLLECT PAGE
# =========================

async def collect_page(
    page: Page
) -> int:

    collected = 0

    seen_ids = set()


    # -------------------------
    # Open X
    # -------------------------

    await page.goto(
        X_HOME_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    await page.wait_for_timeout(5000)


    # -------------------------
    # Try For You tab
    # -------------------------

    try:

        buttons = page.get_by_text(
            "For you",
            exact=True
        )

        if await buttons.count() > 0:

            await buttons.first.click()

            await page.wait_for_timeout(3000)

    except Exception:
        pass


    # -------------------------
    # Scroll + collect
    # -------------------------

    for _ in range(COLLECT_SCROLLS):

        articles = page.locator(
            'article[data-testid="tweet"]'
        )

        count = await articles.count()

        for index in range(count):

            try:

                article = articles.nth(index)

                post = await extract_post(
                    article
                )

                post_id = post["post_id"]

                text = post["text"]

                if not post_id:
                    continue

                if not text:
                    continue

                if post_id in seen_ids:
                    continue

                seen_ids.add(post_id)


                inserted = add_post(
                    post_id=post["post_id"],
                    author=post["author"],
                    username=post["username"],
                    text=post["text"],
                    url=post["url"],
                    created_at=post["created_at"],
                    collected_at=post["collected_at"],
                    source=post["source"],
                )

                if inserted:
                    collected += 1

            except Exception as error:

                print(
                    "Post extraction error:",
                    error
                )


        # Scroll down

        await page.mouse.wheel(
            0,
            1800
        )

        await page.wait_for_timeout(
            2000
        )


    return collected


# =========================
# LOGIN MODE
# =========================

async def login_mode() -> None:

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    async with async_playwright() as playwright:

        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={
                "width": 1440,
                "height": 900
            }
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(
            X_HOME_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print()
        print("=" * 60)
        print("X LOGIN MODE")
        print("=" * 60)
        print()
        print("Log in to your X account in the browser.")
        print("When finished, return to this terminal.")
        print()
        print("Press ENTER to save the session.")
        print("=" * 60)
        print()

        await asyncio.to_thread(input)

        await context.close()

        print()
        print("X session saved.")
        print(f"Profile: {PROFILE_DIR}")
        print()


# =========================
# CONTINUOUS COLLECTOR
# =========================

async def collector_loop() -> None:

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    async with async_playwright() as playwright:

        context: BrowserContext = (
            await playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=True,
                viewport={
                    "width": 1440,
                    "height": 900
                }
            )
        )

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        while True:

            try:

                print(
                    "Collecting X For You..."
                )

                count = await collect_page(
                    page
                )

                print(
                    f"Collected {count} new posts."
                )

            except Exception as error:

                print(
                    "Collector error:",
                    error
                )

            await asyncio.sleep(
                COLLECT_INTERVAL_SECONDS
            )
