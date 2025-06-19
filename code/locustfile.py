from locust import HttpUser, TaskSet, task, between
import json

class UserBehavior(TaskSet):
    token = None
    contents = None
    def on_start(self):
        # Login user dan mendapatkan token
        self.login()

    def login(self):
        response = self.client.post("/auth/sign-in", json={
            "username": "LarissaWylie", # Ganti dengan username yang valid
            "password": "RLS71GOH8GF" # Ganti dengan password yang valid
        })

        if response.status_code == 200:
            self.token = response.json().get("access") # Ambil token akses
        else:
            print("Login failed:", response.text)

    @task(1)
    def get_my_courses(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/courses/", headers=headers)

        if response.status_code == 200:
            self.courses = response.json() # Simpan daftar kursus
            # print("My Courses:", self.courses)

        if self.courses:
            self.course_id = self.courses[0]['id'] # Ambil ID kursus pertama

        self.get_course_contents(self.course_id)

    def get_course_contents(self, course_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(f"/courses/{course_id}", headers=headers)

        if response.status_code == 200:
            self.contents = response.json() # Simpan daftar konten
            # print("Course Contents:", self.contents)

        if isinstance(self.contents, list) and self.contents:
            self.content_id = self.contents[0]['id'] # Ambil ID konten pertama
            self.post_comment(self.content_id)

    def post_comment(self, content_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        comment_data = {"comment": "This is a test comment."}
        response = self.client.post(f"/contents/{content_id}/comments", json=comment_data, headers=headers)

        if response.status_code == 201:
            self.comment_id = response.json().get("id") # Ambil ID komentar
            # print("Comment posted:", response.json())
            self.delete_comment(self.comment_id)

    def delete_comment(self, comment_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.delete(f"/comments/{comment_id}", headers=headers)
        if response.status_code == 200:
            print("Comment deleted:", response.json())
        else:
            print("Failed to delete comment:", response.text)

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 2) # Waktu tunggu antara tugas
