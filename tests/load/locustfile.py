from locust import HttpUser, between, task


class TradingPlatformUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "loadtest@example.com", "password": "LoadTest123!"},
        )
        payload = response.json()
        self.token = payload.get("data", {}).get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def get_bots(self):
        self.client.get("/api/v1/bots", headers=self.headers)

    @task(5)
    def get_trades(self):
        self.client.get("/api/v1/trades?per_page=20", headers=self.headers)

    @task(2)
    def get_dashboard_stats(self):
        self.client.get("/api/v1/trades/stats", headers=self.headers)

    @task(1)
    def get_accounts(self):
        self.client.get("/api/v1/mt5/accounts", headers=self.headers)
