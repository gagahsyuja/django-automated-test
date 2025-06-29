from ninja import Schema
from typing import Optional
from datetime import datetime

from django.contrib.auth.models import User

class LoginIn(Schema):
    username: str
    password: str

class TokenOut(Schema):
    access: str
    refresh: str

class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str


class CourseSchemaOut(Schema):
    id: int
    name: str
    description: str
    price: int
    image : Optional[str]
    teacher: UserOut
    created_at: datetime
    updated_at: datetime

class CourseMemberIn(Schema):
    course_id: int
    user_id: int

class CourseMemberOut(Schema):
    id: int 
    course_id: CourseSchemaOut
    user_id: UserOut
    roles: str
    # created_at: datetime


class CourseSchemaIn(Schema):
    name: str
    description: str
    price: int

class CourseContentIn(Schema):
    name: str
    description: str
    video_url: str
    course_id: int
    parent_id: Optional[int] = None

class CourseContentMini(Schema):
    id: int
    name: str
    description: str
    course_id: CourseSchemaOut
    created_at: datetime
    updated_at: datetime


class CourseContentFull(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str]
    file_attachment: Optional[str]
    course_id: CourseSchemaOut
    created_at: datetime
    updated_at: datetime

class CourseCommentOut(Schema):
    id: int
    content_id: CourseContentMini
    member_id: CourseMemberOut
    comment: str
    created_at: datetime
    updated_at: datetime

class CourseCommentIn(Schema):
    comment: str


class FeedbackOut(Schema):
    id: int
    feedback: str
    created_at: datetime
    updated_at: datetime

class FeedbackIn(Schema):
    feedback: str
