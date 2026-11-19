from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class TasksPage(BasePage):
    path = "/tasks"

    def add_task(self, title, priority="Medium", due=None):
        self.type("task-title", title)
        Select(self.find(By.ID, "task-priority")).select_by_visible_text(priority)
        if due:  # set ISO date via JS: typing into <input type=date> depends on OS locale
            self.driver.execute_script(
                "document.getElementById('task-due').value = arguments[0];", due)
        self.submit("add-btn")
        return self

    def rows(self):
        return self.driver.find_elements(By.CSS_SELECTOR, "#task-table tbody tr.task-row")

    def titles(self):
        return [r.find_element(By.CLASS_NAME, "task-title").text for r in self.rows()]

    def row_for(self, title):
        for r in self.rows():
            if r.find_element(By.CLASS_NAME, "task-title").text == title:
                return r
        raise AssertionError("task %r not found in %r" % (title, self.titles()))

    def toggle(self, title):
        self.submit_and_wait(self.row_for(title).find_element(By.CLASS_NAME, "toggle-btn"))
        return self

    def delete(self, title, accept=True):
        old_page = self.driver.find_element(By.TAG_NAME, "html")
        self.row_for(title).find_element(By.CLASS_NAME, "delete-btn").click()
        alert = self.wait.until(EC.alert_is_present())
        if accept:
            alert.accept()
            self.wait.until(EC.staleness_of(old_page))
        else:
            alert.dismiss()
        return self

    def search(self, text):
        self.type("search-box", text)
        self.submit("search-btn")
        return self

    def count(self, name):
        return int(self.find(By.ID, "count-" + name).text)

    def is_done(self, title):
        return "done" in self.row_for(title).get_attribute("class").split()

    def logout(self):
        self.submit("logout-link")
