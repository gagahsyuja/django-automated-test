from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from .manager import UserManager
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.
class User(AbstractUser):
    email = models.EmailField("E-mail address", unique=True)
    phone_number = PhoneNumberField(blank=True)
    description = models.TextField("Description", default="")
    profile_image = models.ImageField("Profile Image", upload_to="user", blank=True, null=True)

    objects = UserManager()

    def __str__(self):
        return self.email

class Course(models.Model):
    name = models.CharField("Nama Kursus", max_length=255)
    description = models.TextField("Deskripsi")
    price = models.IntegerField("Harga")
    image = models.ImageField("Gambar", upload_to="course", blank=True, null=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Pengajar", on_delete=models.RESTRICT)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Data Mata Kuliah"
        ordering = ["-created_at"]

    def is_member(self, user):
        return CourseMember.objects.filter(course_id=self, user_id=user).exists()

ROLE_OPTIONS = [('std', "Siswa"), ('ast', "Asisten")]

class CourseMember(models.Model):
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="siswa", on_delete=models.RESTRICT)
    roles = models.CharField("peran", max_length=3, choices=ROLE_OPTIONS, default='std')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscriber Matkul"
        verbose_name_plural = "Subscriber Matkul"

    def __str__(self) -> str:
        return f"{self.id} {self.course_id} : {self.user_id}"

class CourseContent(models.Model):
    name = models.CharField("judul konten", max_length=200)
    description = models.TextField("deskripsi", default='-')
    video_url = models.CharField('URL Video', max_length=200, null=True, blank=True)
    file_attachment = models.FileField("File", null=True, blank=True)
    course_id = models.ForeignKey(Course, verbose_name="matkul", on_delete=models.RESTRICT)
    parent_id = models.ForeignKey("self", verbose_name="induk", 
                                on_delete=models.RESTRICT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konten Matkul"
        verbose_name_plural = "Konten Matkul"

    def __str__(self) -> str:
        return f'{self.course_id} {self.name}'

class CourseLimit(models.Model):
    course_id = models.ForeignKey(Course, verbose_name="course", on_delete=models.CASCADE)
    teacher_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="teacher", on_delete=models.CASCADE)
    limit = models.IntegerField("maximum student", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course Limit"
        verbose_name_plural = "Course Limits"

    def __str__(self) -> str:
        return "Course Limit: " + self.course_id.id + " - " + self.teacher_id.id + " - " + self.limit

class Comment(models.Model):
    content_id = models.ForeignKey(CourseContent, verbose_name="konten", on_delete=models.CASCADE)
    member_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="pengguna", on_delete=models.CASCADE)
    comment = models.TextField('komentar')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"

    def __str__(self) -> str:
        return "Komen: "+self.member_id.user_id+"-"+self.comment

class Feedback(models.Model):
    course_id = models.ForeignKey(Course, verbose_name="course", on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="user", on_delete=models.CASCADE)
    feedback = models.TextField('feedback')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def __str__(self) -> str:
        return "Feedback: " + str(self.user_id.id) + " - " + str(self.course_id.id) + " - " + self.feedback
