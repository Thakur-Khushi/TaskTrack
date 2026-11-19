from .base_page import BasePage


class RegisterPage(BasePage):
    path = "/register"

    def register(self, username, password, confirm):
        self.type("username", username)
        self.type("password", password)
        self.type("confirm", confirm)
        self.submit("register-btn")
        return self
