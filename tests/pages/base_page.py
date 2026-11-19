from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    path = "/"

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 5)

    def open(self):
        self.driver.get(self.base_url + self.path)
        return self

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def type(self, element_id, text):
        el = self.find(By.ID, element_id)
        el.clear()
        el.send_keys(text)

    def click(self, element_id):
        self.wait.until(EC.element_to_be_clickable((By.ID, element_id))).click()

    def submit_and_wait(self, element):
        """Click a submit button and wait until the browser has loaded the next page.

        Without this, the test can move on (or navigate away) while the POST is
        still in flight, which cancels it - a classic flaky-test cause.
        """
        old_page = self.driver.find_element(By.TAG_NAME, "html")
        element.click()
        try:
            self.wait.until(EC.staleness_of(old_page))
        except Exception:
            pass  # page did not reload (e.g. blocked by HTML5 validation)

    def submit(self, element_id):
        self.submit_and_wait(self.wait.until(EC.element_to_be_clickable((By.ID, element_id))))

    def flash(self, kind):
        """Text of the 'success' or 'error' flash message, or '' if none is shown."""
        els = self.driver.find_elements(By.ID, "flash-" + kind)
        return els[0].text if els else ""

    def current_path(self):
        return self.driver.current_url.replace(self.base_url, "").split("?")[0]
