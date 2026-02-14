from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@dataclass(slots=True)
class BotResult:
    ok: bool
    message: str


class PlaytomicBot:
    """Infrastructure class for Selenium automation against Playtomic."""

    def __init__(self, logger: logging.Logger, timeout_seconds: int = 20) -> None:
        self.logger = logger
        self.timeout_seconds = timeout_seconds

    def _build_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--start-maximized")
        return webdriver.Chrome(options=options)

    def reserve(
        self,
        email: str,
        password: str,
        base_url: str,
        booking_fragment_url: str,
        play_datetime_local: datetime,
        booking_code: str,
        max_retries: int = 2,
    ) -> BotResult:
        for attempt in range(1, max_retries + 1):
            driver = None
            try:
                self.logger.info("Bot attempt %s for %s", attempt, email)
                driver = self._build_driver()
                wait = WebDriverWait(driver, self.timeout_seconds)

                driver.get("https://playtomic.io/users/login")
                wait.until(ec.visibility_of_element_located((By.NAME, "email"))).send_keys(email)
                wait.until(ec.visibility_of_element_located((By.NAME, "password"))).send_keys(password)
                wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

                date_path = play_datetime_local.strftime("%Y-%m-%d")
                target_url = f"{base_url.rstrip('/')}/{booking_fragment_url.strip('/')}?date={date_path}&time={booking_code}"
                self.logger.info("Opening booking URL %s", target_url)
                driver.get(target_url)

                wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='book-button']"))).click()
                wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='confirm-booking']"))).click()

                self.logger.info("Reservation succeeded for %s", email)
                return BotResult(ok=True, message="Reservation completed")
            except TimeoutException as exc:
                self.logger.warning("Timeout in attempt %s: %s", attempt, exc)
                if attempt == max_retries:
                    return BotResult(ok=False, message=f"Timeout: {exc}")
            except Exception as exc:  # noqa: BLE001
                self.logger.exception("Unhandled Selenium error")
                if attempt == max_retries:
                    return BotResult(ok=False, message=f"Unhandled error: {exc}")
            finally:
                if driver is not None:
                    driver.quit()
        return BotResult(ok=False, message="Unknown error")
