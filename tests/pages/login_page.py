from .base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    def login(self, username, password):
        self.type("username", username)
        self.type("password", password)
        self.submit("login-btn")
        from .tasks_page import TasksPage
        return TasksPage(self.driver, self.base_url)
