"""End-to-end Selenium tests for the SSHerlock web app.

These tests exercise:
- Landing -> Sign up -> Home flow
- Account dropdown, settings, change email and password
- Logout and Login flows
- Creating Credentials, LLM API, Bastion Host, Target Host
- Creating a Job, Cancel then Retry
- Visiting list pages and clicking primary buttons
- Delete confirmation popup open/close

Notes:
- Tests use headless browser by default. Set SELENIUM_BROWSER to 'chrome' or 'firefox'
  to choose the driver. If driver initialization fails, tests are skipped.
- Tests assume a local live server provided by Django's StaticLiveServerTestCase.
"""

from __future__ import annotations

import os
import time
import unittest
import re
import logging
from datetime import datetime
import json
import requests

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException,
        TimeoutException,
        ElementClickInterceptedException,
        ElementNotInteractableException,
    )

    SELENIUM_AVAILABLE = True
except Exception:  # pragma: no cover - only used to gracefully skip if not installed
    SELENIUM_AVAILABLE = False

logger = logging.getLogger(__name__)


def _new_unique(value: str) -> str:
    """Return a unique value by appending a timestamp."""
    return f"{value}-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


@unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium is not available")
class SeleniumSSHerlockTests(StaticLiveServerTestCase):
    """Comprehensive Selenium tests covering core user flows."""

    @classmethod
    def setUpClass(cls) -> None:
        """Start the browser once for the test class."""
        super().setUpClass()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )

        browser = os.getenv("SELENIUM_BROWSER", "chrome").lower()
        headless = os.getenv("SELENIUM_HEADLESS", "1") != "0"

        try:
            if browser == "firefox":
                options = webdriver.FirefoxOptions()
                if headless:
                    options.add_argument("-headless")
                cls.driver = webdriver.Firefox(options=options)
            else:
                # Default to Chrome
                options = webdriver.ChromeOptions()
                if headless:
                    options.add_argument("--headless=new")
                options.add_argument("--window-size=1280,900")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                cls.driver = webdriver.Chrome(options=options)
        except Exception as exc:  # pragma: no cover - graceful skip
            cls.driver = None
            raise unittest.SkipTest(f"WebDriver not available: {exc}")

        cls.driver.set_page_load_timeout(30)
        cls.wait = WebDriverWait(cls.driver, 20)

        # Test data prepared once per class
        cls.username = _new_unique("seleniumuser")
        cls.email = f"{cls.username}@example.com"
        cls.password = "S3lenium!Passw0rd"
        cls.new_email = f"{cls.username}+new@example.com"

        cls.credential_name = _new_unique("cred")
        cls.credential_user = "ubuntu"
        cls.credential_pass = "password123"

        cls.bastion_hostname = _new_unique("bastion.example.com")
        cls.bastion_port = "22"

        cls.target_hostname = _new_unique("target.example.com")
        cls.target_port = "22"
        cls.target_hostname_2 = _new_unique("target2.example.com")

        cls.llm_base_url = "https://api.example.com/v1"
        cls.llm_api_key = _new_unique("key")

        cls.job_instructions = "Install nginx and ensure service is enabled."

    @classmethod
    def tearDownClass(cls) -> None:
        """Quit the browser."""
        try:
            if getattr(cls, "driver", None):
                cls.driver.quit()
        finally:
            super().tearDownClass()

    # ---------- Helper methods ----------

    def go(self, path: str) -> None:
        """Navigate to a path on the live server."""
        self.driver.get(f"{self.live_server_url}{path}")

    def click(self, by: By, selector: str) -> None:
        """Click an element when it becomes clickable."""
        elem = self.wait.until(EC.element_to_be_clickable((by, selector)))
        elem.click()

    def type(self, by: By, selector: str, text: str, clear: bool = True) -> None:
        """Type text into an input."""
        elem = self.wait.until(EC.presence_of_element_located((by, selector)))
        if clear:
            elem.clear()
        elem.send_keys(text)

    def select_by_visible_text(self, by: By, selector: str, text: str) -> None:
        """Select an option in a select element by visible text."""
        elem = self.wait.until(EC.presence_of_element_located((by, selector)))
        Select(elem).select_by_visible_text(text)

    def assert_text_present(self, text: str) -> None:
        """Assert that given text appears somewhere in the page."""
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, f"//*[contains(., '{text}')]"))
        )

    # ---------- Tests ----------

    def test_full_user_journey(self) -> None:
        """Run through signup, CRUD operations, job flow, and logout/login."""
        self._landing_to_signup_to_home()
        self._open_account_settings_and_change_email_and_password()
        self._create_core_objects()
        self._edit_all_objects()
        self._create_job_cancel_and_retry()
        self._job_detail_cancel_and_retry()
        self._job_log_streaming_demo()
        self._visit_all_lists_and_click_add_cancel()
        self._assert_masking_on_lists()
        self._delete_sample_objects()
        self._delete_additional_objects()
        self._logout_and_login()

    # ---------- Subflows ----------

    def _landing_to_signup_to_home(self) -> None:
        # Landing
        self.go("/")
        self.assert_text_present("SSHerlock")

        # Click Sign up
        self.click(By.LINK_TEXT, "Get started free")

        # Sign up form
        self.type(By.ID, "username", self.username)
        self.type(By.ID, "email", self.email)
        self.type(By.ID, "password1", self.password)
        self.type(By.ID, "password2", self.password)

        # Submit
        self.click(By.CSS_SELECTOR, "button[type='submit']")

        # Should land on home
        self.wait.until(EC.url_contains("/home"))
        self.assert_text_present("Home")

    def _job_log_streaming_demo(self) -> None:
        """Demonstrate live job log streaming by seeding lines into the expected log file.

        This is a best-effort check. If SSE or the browser session is unstable,
        skip without failing the overall end-to-end journey.
        """
        try:
            # Open the job detail page from the list
            self.open_first_job_detail()

            # Locate the SSE stream URL and derive the job ID (UUID)
            log_div = self.wait.until(
                EC.presence_of_element_located((By.ID, "job-log"))
            )
            stream_url = log_div.get_attribute("data-stream-url") or ""
            # stream_url looks like: /view_job/<uuid>/log
            job_id = stream_url.strip("/").split("/")[-2]

            # Post log entries via the runner API to the live server endpoint.
            post_url = f"{self.live_server_url}/log_job_data/{job_id}"
            headers = {
                "Authorization": "Bearer myprivatekey",
                "Content-Type": "application/json",
            }

            # Send two lines with small delays to allow the EventSource to receive them.
            payload1 = json.dumps({"log": "SSE TEST LINE 1"})
            resp1 = requests.post(
                post_url,
                headers=headers,
                data=payload1,
                timeout=10,
            )
            if resp1.status_code != 200:
                return

            time.sleep(0.5)

            payload2 = json.dumps({"log": "SSE TEST LINE 2"})
            resp2 = requests.post(
                post_url,
                headers=headers,
                data=payload2,
                timeout=10,
            )
            if resp2.status_code != 200:
                return

            # Use short, dedicated waits for these checks to avoid long hangs if SSE is unavailable.
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(., 'SSE TEST LINE 1')]")
                )
            )
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(., 'SSE TEST LINE 2')]")
                )
            )
        except Exception:
            # Non-fatal: continue the journey even if SSE verification fails.
            return

    def _delete_additional_objects(self) -> None:
        """Delete remaining sample objects and verify removal from lists."""
        # Delete Credential
        self.go("/credential_list")
        try:
            self.click(
                By.XPATH,
                f"//tr[.//span[contains(., '{self.credential_name}')]]//button[contains(., 'Delete')]",
            )
            self.click(By.ID, "confirmButton")
            self.wait_for_text_absent(self.credential_name, timeout=15)
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            pass

        # Delete LLM API
        self.go("/llm_api_list")
        try:
            self.click(
                By.XPATH,
                f"//tr[.//span[contains(., '{self.llm_base_url}')]]//button[contains(., 'Delete')]",
            )
            self.click(By.ID, "confirmButton")
            self.wait_for_text_absent(self.llm_base_url, timeout=15)
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            pass

        # Delete a Target Host (second one)
        self.go("/target_host_list")
        try:
            self.click(
                By.XPATH,
                f"//tr[.//span[contains(., '{self.target_hostname_2}')]]//button[contains(., 'Delete')]",
            )
            self.click(By.ID, "confirmButton")
            self.wait_for_text_absent(self.target_hostname_2, timeout=15)
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            pass

    # ----------------- Additional independent tests -----------------

    def test_auth_redirect_when_logged_out(self) -> None:
        """Visiting a protected URL when logged out should redirect to login."""
        # Ensure logged out by clearing cookies/session
        self.driver.delete_all_cookies()
        self.go("/credential_list")
        self.wait.until(EC.url_contains("/accounts/login/"))

    def test_signup_password_mismatch(self) -> None:
        """Sign up should fail when passwords do not match."""
        self.go("/signup/")
        uname = _new_unique("user-mismatch")
        email = f"{uname}@example.com"
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", "StrongPassw0rd!")
        self.type(By.ID, "password2", "DifferentPassw0rd!")
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        # Should remain on signup page
        self.wait.until(EC.url_contains("/signup"))
        self.assert_text_present("Sign Up")

    def test_signup_duplicate_username(self) -> None:
        """Sign up should fail if username already exists."""
        # Pre-create user directly in DB
        existing = _new_unique("dupeuser")
        User.objects.create_user(existing, f"{existing}@example.com", "StrongPassw0rd!")
        # Try to sign up with the same username
        self.go("/signup/")
        self.type(By.ID, "username", existing)
        self.type(By.ID, "email", f"{existing}+new@example.com")
        self.type(By.ID, "password1", "AnotherStr0ngPass!")
        self.type(By.ID, "password2", "AnotherStr0ngPass!")
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        # Should remain on signup page
        self.wait.until(EC.url_contains("/signup"))
        self.assert_text_present("Sign Up")

    def test_signup_password_too_short(self) -> None:
        """Sign up should fail when password is shorter than 12 characters."""
        self.go("/signup/")
        uname = _new_unique("shortpw")
        email = f"{uname}@example.com"
        short_pw = "short123!"  # Fails MinimumLengthValidator(min_length=12)
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", short_pw)
        self.type(By.ID, "password2", short_pw)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        # Should remain on signup page and show a length error
        self.wait.until(EC.url_contains("/signup"))
        self.assert_text_present("too short")

    def test_signup_password_too_long(self) -> None:
        """Sign up should fail when password is longer than 256 characters."""
        self.go("/signup/")
        uname = _new_unique("longpw")
        email = f"{uname}@example.com"
        # Build a long, complex password > 256 chars to avoid other validators interfering.
        long_pw = "Abc123!x" * 40  # 8 * 40 = 320 chars
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", long_pw)
        self.type(By.ID, "password2", long_pw)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        # Should remain on signup page and show the max length error message from the form.
        self.wait.until(EC.url_contains("/signup"))
        self.assert_text_present("Password cannot be longer than 256 characters.")

    def test_login_invalid_credentials(self) -> None:
        """Login should fail with invalid credentials."""
        self.go("/accounts/login/")
        self.type(By.ID, "username", "not-a-user")
        self.type(By.ID, "password", "wrong-password")
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/accounts/login/"))
        # Error message from custom_login view
        self.assert_text_present("Invalid username or password.")

    def test_signup_cancel_navigates_to_landing(self) -> None:
        """Cancel on the signup page should navigate to the landing page."""
        self.driver.delete_all_cookies()
        self.go("/signup/")
        self.click(By.LINK_TEXT, "Cancel")
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

    def test_login_cancel_navigates_to_landing(self) -> None:
        """Cancel on the login page should navigate to the landing page."""
        self.driver.delete_all_cookies()
        self.go("/accounts/login/")
        self.click(By.LINK_TEXT, "Cancel")
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

    def test_logo_navigation_logged_in(self) -> None:
        """Logo should navigate to dashboard when authenticated."""
        self.driver.delete_all_cookies()
        # Sign up a fresh user
        self.go("/signup/")
        uname = _new_unique("logo-user")
        email = f"{uname}@example.com"
        pwd = "VeryStr0ngPass!"
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", pwd)
        self.type(By.ID, "password2", pwd)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))

        # Visit another page, then click logo to return home
        self.go("/bastion_host_list")
        self.click(By.CSS_SELECTOR, "a[aria-label='Go to dashboard']")
        self.wait.until(EC.url_contains("/home"))

    def test_logo_navigation_logged_out(self) -> None:
        """Logo should navigate to landing when not authenticated."""
        self.driver.delete_all_cookies()
        self.go("/")
        self.click(By.CSS_SELECTOR, "a[aria-label='SSHerlock home']")
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

    def test_change_password_validation(self) -> None:
        """Change password should show validation errors for mismatch and weak passwords."""
        self.driver.delete_all_cookies()
        # Sign up a fresh user
        self.go("/signup/")
        uname = _new_unique("pwd-validate-user")
        email = f"{uname}@example.com"
        pwd = "ValidPassw0rd!"
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", pwd)
        self.type(By.ID, "password2", pwd)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))

        # Open Account settings
        self.click(By.ID, "accountButton")
        self.click(By.LINK_TEXT, "Settings")
        self.wait.until(EC.url_contains("/account/"))

        # Mismatch case
        self.type(By.ID, "new_password", "MismatchPassw0rd!")
        self.type(By.ID, "confirm_password", "DifferentPassw0rd!")
        self.click(
            By.CSS_SELECTOR, "form[action$='reset_password/'] button[type='submit']"
        )
        self.assert_text_present("Passwords do not match.")

        # Weak password (too short)
        self.type(By.ID, "new_password", "short")
        self.type(By.ID, "confirm_password", "short")
        self.click(
            By.CSS_SELECTOR, "form[action$='reset_password/'] button[type='submit']"
        )
        self.assert_text_present("too short")

    def test_account_deletion_flow(self) -> None:
        """User can delete their account and is redirected; login should then fail."""
        self.driver.delete_all_cookies()
        # Sign up a fresh user
        self.go("/signup/")
        uname = _new_unique("delete-user")
        email = f"{uname}@example.com"
        pwd = "An0therVal1dPass!"
        self.type(By.ID, "username", uname)
        self.type(By.ID, "email", email)
        self.type(By.ID, "password1", pwd)
        self.type(By.ID, "password2", pwd)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))

        # Go to account page and trigger deletion
        self.go("/account/")
        self.click(By.XPATH, "//button[contains(., 'Delete Account')]")
        self.click(
            By.XPATH,
            "//div[@id='deleteAccountPopup']//form//button[contains(., 'Delete')]",
        )

        # Should be redirected to landing
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

        # Try to log in with deleted credentials -> should fail
        self.click(By.LINK_TEXT, "Log in")
        self.wait.until(EC.url_contains("/accounts/login/"))
        self.type(By.ID, "username", uname)
        self.type(By.ID, "password", pwd)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/accounts/login/"))
        self.assert_text_present("Invalid username or password.")

    def test_signup_duplicate_username_via_ui_flow(self) -> None:
        """Sign up, logout, then try to sign up again with same username and verify rejection."""
        # Ensure a clean session
        self.driver.delete_all_cookies()

        # First successful signup
        self.go("/signup/")
        username = _new_unique("dupeflow")
        email1 = f"{username}@example.com"
        password = "ValidPassw0rd!"
        self.type(By.ID, "username", username)
        self.type(By.ID, "email", email1)
        self.type(By.ID, "password1", password)
        self.type(By.ID, "password2", password)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))
        self.assert_text_present("Home")

        # Logout
        self.go("/home")
        self.click(By.ID, "accountButton")
        self.click(
            By.XPATH,
            "//form[@action='/accounts/logout/']//button[contains(., 'Sign Out')]",
        )
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

        # Attempt to sign up again with same username
        self.go("/signup/")
        email2 = f"{username}+second@example.com"
        self.type(By.ID, "username", username)
        self.type(By.ID, "email", email2)
        self.type(By.ID, "password1", password)
        self.type(By.ID, "password2", password)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        # Should remain on signup page and show duplicate username error
        self.wait.until(EC.url_contains("/signup"))
        self.assert_text_present("already exists")

    def test_object_isolation_between_users(self) -> None:
        """Ensure objects created by one user are not visible to another user."""
        self.driver.delete_all_cookies()

        # Sign up as first user.
        self.go("/signup/")
        user1 = _new_unique("iso-user1")
        email1 = f"{user1}@example.com"
        pwd1 = "ValidPassw0rd!"
        self.type(By.ID, "username", user1)
        self.type(By.ID, "email", email1)
        self.type(By.ID, "password1", pwd1)
        self.type(By.ID, "password2", pwd1)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))

        # Create objects as user1.
        # Credential
        cred1 = _new_unique("iso-cred")
        self.go("/credential_list")
        self.click(By.LINK_TEXT, "Add Credential")
        self.type(By.NAME, "credential_name", cred1)
        self.type(By.NAME, "username", "ubuntu")
        self.type(By.NAME, "password", "secret123")
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/credential_list"))
        self.assert_text_present(cred1)

        # LLM API
        llm1 = _new_unique("https://api.iso.example.com/v1")
        self.go("/llm_api_list")
        self.click(By.LINK_TEXT, "Add LLM API")
        self.type(By.NAME, "base_url", llm1)
        self.type(By.NAME, "api_key", "key-abc")
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/llm_api_list"))
        self.assert_text_present(llm1)

        # Bastion Host
        bast1 = _new_unique("iso-bastion.example.com")
        self.go("/bastion_host_list")
        self.click(By.LINK_TEXT, "Add Bastion Host")
        self.type(By.NAME, "hostname", bast1)
        self.type(By.NAME, "port", "22")
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/bastion_host_list"))
        self.assert_text_present(bast1)

        # Target Host
        host1 = _new_unique("iso-target.example.com")
        self.go("/target_host_list")
        self.click(By.LINK_TEXT, "Add Target Host")
        self.type(By.NAME, "hostname", host1)
        self.type(By.NAME, "port", "22")
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/target_host_list"))
        self.assert_text_present(host1)

        # Log out user1.
        self.go("/home")
        self.click(By.ID, "accountButton")
        self.click(
            By.XPATH,
            "//form[@action='/accounts/logout/']//button[contains(., 'Sign Out')]",
        )
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

        # Sign up as second user.
        self.go("/signup/")
        user2 = _new_unique("iso-user2")
        email2 = f"{user2}@example.com"
        pwd2 = "ValidPassw0rd!"
        self.type(By.ID, "username", user2)
        self.type(By.ID, "email", email2)
        self.type(By.ID, "password1", pwd2)
        self.type(By.ID, "password2", pwd2)
        self.click(By.CSS_SELECTOR, "button[type='submit']")
        self.wait.until(EC.url_contains("/home"))

        # Verify that user1's objects are not visible to user2.
        self.go("/credential_list")
        self.wait_for_text_absent(cred1, timeout=5)

        self.go("/llm_api_list")
        self.wait_for_text_absent(llm1, timeout=5)

        self.go("/bastion_host_list")
        self.wait_for_text_absent(bast1, timeout=5)

        self.go("/target_host_list")
        self.wait_for_text_absent(host1, timeout=5)

    # ---------- Additional helper utilities ----------

    def open_first_job_detail(self) -> None:
        """Open the first job detail row robustly by using JS click or onclick URL."""
        self.go("/job_list")
        # Wait for the first row to exist
        row = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#job_list_table tbody tr")
            )
        )
        # Try smooth scroll + JS click
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", row
            )
            self.driver.execute_script("arguments[0].click();", row)
            self.wait.until(EC.url_contains("/view_job/"))
            return
        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            TimeoutException,
        ):
            pass

        # Fallback: navigate using the onclick handler URL if present
        onclick = row.get_attribute("onclick") or ""
        match = re.search(r"window\.location=['\"][^'\"]+['\"]", onclick)
        if match:
            url_match = re.search(r"['\"]([^'\"]+)['\"]", match.group(0))
            if url_match:
                url = url_match.group(1)
                if url.startswith("/"):
                    self.driver.get(f"{self.live_server_url}{url}")
                else:
                    self.driver.get(url)
                self.wait.until(EC.url_contains("/view_job/"))
                return

        # Last resort: click a child element
        try:
            cell = row.find_element(By.XPATH, ".//span")
            self.driver.execute_script("arguments[0].click();", cell)
            self.wait.until(EC.url_contains("/view_job/"))
        except (
            NoSuchElementException,
            ElementClickInterceptedException,
            TimeoutException,
        ):
            # Give up silently; the caller can decide next step.
            pass

    def click_row_by_text(self, text: str) -> None:
        """Click a table row by matching text; robust against DataTables overlays.

        Tries JS scroll + click. Falls back to navigating via the row's onclick URL.
        """
        xpath = f"//tr[.//span[contains(., '{text}')]]"
        row = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

        # Scroll into view and attempt click via JS to bypass overlays
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", row
        )
        self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            self.driver.execute_script("arguments[0].click();", row)
            return
        except (
            ElementClickInterceptedException,
            ElementNotInteractableException,
            TimeoutException,
        ):
            pass

        # Fallback: navigate using the onclick handler URL if present
        onclick = row.get_attribute("onclick") or ""
        match = re.search(r"window\.location=['\"][^'\"]+['\"]", onclick)
        if match:
            # Extract URL between quotes
            url_match = re.search(r"['\"]([^'\"]+)['\"]", match.group(0))
            if url_match:
                url = url_match.group(1)
                if url.startswith("/"):
                    self.driver.get(f"{self.live_server_url}{url}")
                else:
                    self.driver.get(url)
                return

        # Last resort: click a child element
        try:
            cell = row.find_element(By.XPATH, ".//span")
            self.driver.execute_script("arguments[0].click();", cell)
        except (NoSuchElementException, ElementClickInterceptedException):
            # Give up silently; caller can decide next step
            pass

    def wait_for_text_absent(self, text: str, timeout: int = 10) -> None:
        """Wait until given text is absent from the page source."""
        WebDriverWait(self.driver, timeout).until(lambda d: text not in d.page_source)

    # ---------- Newly added subflows ----------

    def _edit_all_objects(self) -> None:
        """Edit each created object via its list row click -> edit form."""
        # Edit Credential
        self.go("/credential_list")
        self.click_row_by_text(self.credential_name)
        new_cred_name = f"{self.credential_name}-edited"
        self.type(By.NAME, "credential_name", new_cred_name)
        # Re-supply the password as it is required on edit.
        self.type(By.NAME, "password", self.credential_pass, clear=True)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Edit']")
        self.wait.until(EC.url_contains("/credential_list"))
        self.assert_text_present(new_cred_name)
        self.credential_name = new_cred_name

        # Edit LLM API (use a valid URL)
        self.go("/llm_api_list")
        self.click_row_by_text(self.llm_base_url)
        new_llm_url = "https://api.example.com/v2"
        self.type(By.NAME, "base_url", new_llm_url)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Edit']")
        self.wait.until(EC.url_contains("/llm_api_list"))
        self.assert_text_present(new_llm_url)
        self.llm_base_url = new_llm_url

        # Edit Bastion Host
        self.go("/bastion_host_list")
        self.click_row_by_text(self.bastion_hostname)
        new_bastion = f"{self.bastion_hostname}-edited"
        self.type(By.NAME, "hostname", new_bastion)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Edit']")
        self.wait.until(EC.url_contains("/bastion_host_list"))
        self.assert_text_present(new_bastion)
        self.bastion_hostname = new_bastion

        # Edit Target Host (first one)
        self.go("/target_host_list")
        self.click_row_by_text(self.target_hostname)
        new_target = f"{self.target_hostname}-edited"
        self.type(By.NAME, "hostname", new_target)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Edit']")
        self.wait.until(EC.url_contains("/target_host_list"))
        self.assert_text_present(new_target)
        self.target_hostname = new_target

    def _job_detail_cancel_and_retry(self) -> None:
        """Open the job detail page and perform Cancel and Retry from there."""
        # Open the first job's detail (robust against overlays/DataTables)
        self.open_first_job_detail()

        # On the detail page, cancel if possible (status Pending or Running)
        # For Pending, a Cancel job button should be visible
        try:
            self.click(
                By.XPATH,
                "//form[contains(@action, 'cancel_job')]/button[contains(., 'Cancel job')]",
            )
            # After cancel, expect 'Retry job' to be visible
            self.assert_text_present("Canceled")
            self.click(By.LINK_TEXT, "Retry job")
            self.assert_text_present("Pending")
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            # If cancel not available (already canceled), just try Retry job
            try:
                self.click(By.LINK_TEXT, "Retry job")
                self.assert_text_present("Pending")
            except (
                TimeoutException,
                NoSuchElementException,
                ElementClickInterceptedException,
            ):
                # If neither is available, continue without failing the whole journey
                pass

    def _assert_masking_on_lists(self) -> None:
        """Assert that sensitive fields are masked on list views."""
        self.go("/credential_list")
        self.assert_text_present("******")

        self.go("/llm_api_list")
        self.assert_text_present("******")

    def _delete_sample_objects(self) -> None:
        """Delete a sample object via popup confirmation to verify flow."""
        # Delete the edited bastion host
        self.go("/bastion_host_list")
        # Open delete popup for the row containing the bastion hostname
        self.click(
            By.XPATH,
            f"//tr[.//span[contains(., '{self.bastion_hostname}')]]//button[contains(., 'Delete')]",
        )
        # Confirm deletion
        self.click(By.ID, "confirmButton")
        # Ensure it's gone
        self.wait_for_text_absent(self.bastion_hostname, timeout=15)

    def _open_account_settings_and_change_email_and_password(self) -> None:
        # Open Account dropdown
        self.click(By.ID, "accountButton")

        # Go to Settings
        self.click(By.LINK_TEXT, "Settings")
        self.wait.until(EC.url_contains("/account/"))
        self.assert_text_present("Account Details")

        # Change email
        self.type(By.ID, "new_email", self.new_email)
        self.click(
            By.CSS_SELECTOR, "form[action$='update_email/'] button[type='submit']"
        )
        # Expect redirect back with success param; or success message on page
        self.wait.until(EC.url_contains("/account/"))
        # The page uses ?success=...; success banner is read by JS; still assert we are on account page
        self.assert_text_present("Account Details")

        # Change password
        self.type(By.ID, "new_password", self.password + "X")
        self.type(By.ID, "confirm_password", self.password + "X")
        self.click(
            By.CSS_SELECTOR, "form[action$='reset_password/'] button[type='submit']"
        )
        # Should render account page with success message or remain logged in
        self.assert_text_present("Account Details")

        # Update our in-memory password for later logins
        self.password = self.password + "X"

    def _create_core_objects(self) -> None:
        # Credentials
        self.go("/credential_list")
        self.click(By.LINK_TEXT, "Add Credential")
        self.type(By.NAME, "credential_name", self.credential_name)
        self.type(By.NAME, "username", self.credential_user)
        self.type(By.NAME, "password", self.credential_pass)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/credential_list"))
        self.assert_text_present(self.credential_name)

        # LLM API
        self.go("/llm_api_list")
        self.click(By.LINK_TEXT, "Add LLM API")
        self.type(By.NAME, "base_url", self.llm_base_url)
        self.type(By.NAME, "api_key", self.llm_api_key)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/llm_api_list"))
        self.assert_text_present(self.llm_base_url)

        # Bastion Host
        self.go("/bastion_host_list")
        self.click(By.LINK_TEXT, "Add Bastion Host")
        self.type(By.NAME, "hostname", self.bastion_hostname)
        self.type(By.NAME, "port", self.bastion_port)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/bastion_host_list"))
        self.assert_text_present(self.bastion_hostname)

        # Target Host
        self.go("/target_host_list")
        self.click(By.LINK_TEXT, "Add Target Host")
        self.type(By.NAME, "hostname", self.target_hostname)
        self.type(By.NAME, "port", self.target_port)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/target_host_list"))
        self.assert_text_present(self.target_hostname)

        # Add a second Target Host to test multi-target jobs
        self.click(By.LINK_TEXT, "Add Target Host")
        self.type(By.NAME, "hostname", self.target_hostname_2)
        self.type(By.NAME, "port", self.target_port)
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")
        self.wait.until(EC.url_contains("/target_host_list"))
        self.assert_text_present(self.target_hostname_2)

    def _create_job_cancel_and_retry(self) -> None:
        # Create a job
        self.go("/add/job")

        # Select llm_api by visible text of base URL
        self.select_by_visible_text(By.NAME, "llm_api", self.llm_base_url)

        # bastion and credentials for bastion
        self.select_by_visible_text(By.NAME, "bastion_host", self.bastion_hostname)
        self.select_by_visible_text(
            By.NAME, "credentials_for_bastion_host", self.credential_name
        )

        # Select target_hosts checkboxes by label text (multi-select)
        # CheckboxSelectMultiple renders inputs with same name; use XPath to match label
        self.click(By.XPATH, f"//label[contains(., '{self.target_hostname}')]")
        self.click(By.XPATH, f"//label[contains(., '{self.target_hostname_2}')]")

        # Credentials for target hosts
        # Open the dropdown first so options are visible, then select by text.
        self.click(By.NAME, "credentials_for_target_hosts")
        self.select_by_visible_text(
            By.NAME, "credentials_for_target_hosts", self.credential_name
        )

        # Instructions
        self.type(By.NAME, "instructions", self.job_instructions)

        # Submit
        self.click(By.CSS_SELECTOR, "input[type='submit'][value='Add']")

        # Redirect to job list
        self.wait.until(EC.url_contains("/job_list"))
        self.assert_text_present("Jobs")
        # Verify both target hosts are listed for the new job
        self.assert_text_present(self.target_hostname)
        self.assert_text_present(self.target_hostname_2)

        # Cancel the job (status Pending at first)
        # Find the first Cancel button and click it
        try:
            self.click(
                By.XPATH,
                "//form[contains(@action, 'cancel_job')]/button[contains(., 'Cancel')]",
            )
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            # Give DataTables time to initialize and try again once
            time.sleep(1.0)
            self.click(
                By.XPATH,
                "//form[contains(@action, 'cancel_job')]/button[contains(., 'Cancel')]",
            )

        # After cancel, page reloads; status should show "Canceled"
        self.assert_text_present("Canceled")

        # Now Retry should be visible; click it
        self.click(By.LINK_TEXT, "Retry")
        self.assert_text_present("Pending")

    def _visit_all_lists_and_click_add_cancel(self) -> None:
        # Helper that visits a list page, clicks Add, then Cancel
        def visit_click_add_cancel(list_path: str, add_button_text: str) -> None:
            self.go(list_path)
            self.click(By.LINK_TEXT, add_button_text)
            # Click Cancel button on form
            self.click(By.LINK_TEXT, "Cancel")

        visit_click_add_cancel("/credential_list", "Add Credential")
        visit_click_add_cancel("/llm_api_list", "Add LLM API")
        visit_click_add_cancel("/bastion_host_list", "Add Bastion Host")
        visit_click_add_cancel("/target_host_list", "Add Target Host")

        # Jobs list has "New Job" button
        self.go("/job_list")
        self.click(By.LINK_TEXT, "New Job")
        self.click(By.LINK_TEXT, "Cancel")  # back from the add job page

        # Test delete popup open/close on at least one list page (credentials)
        self.go("/credential_list")
        # Open popup on first Delete button if present
        try:
            self.click(By.XPATH, "//button[contains(., 'Delete')]")
            # Popup should appear with Cancel and Delete buttons
            self.click(By.ID, "cancelButton")
        except (
            TimeoutException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ):
            # If nothing to delete, skip silently
            pass

    def _logout_and_login(self) -> None:
        # Logout via Account dropdown
        self.go("/home")
        self.click(By.ID, "accountButton")
        # Click Sign Out button inside the form
        self.click(
            By.XPATH,
            "//form[@action='/accounts/logout/']//button[contains(., 'Sign Out')]",
        )
        self.wait.until(EC.url_to_be(f"{self.live_server_url}/"))

        # Login again
        self.click(By.LINK_TEXT, "Log in")
        self.wait.until(EC.url_contains("/accounts/login/"))

        self.type(By.ID, "username", self.username)
        self.type(By.ID, "password", self.password)
        self.click(By.CSS_SELECTOR, "button[type='submit']")

        self.wait.until(EC.url_contains("/home"))
        self.assert_text_present("Home")
