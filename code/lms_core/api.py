import jwt
from django.conf import settings
from ninja import NinjaAPI, UploadedFile, File, Form, Schema, Router
from ninja.responses import Response
from lms_core.schema import CourseSchemaOut, CourseMemberOut, CourseSchemaIn
from lms_core.schema import CourseContentMini, CourseContentFull
from lms_core.schema import CourseCommentOut, CourseCommentIn
from lms_core.models import Course, CourseMember, CourseContent, Comment
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja.pagination import paginate, PageNumberPagination
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from ninja.security import HttpBearer
from datetime import datetime, timedelta
from rest_framework import status

from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja import Router

router = Router(auth=HttpJwtAuth())

from django.contrib.auth.models import User

class HelloResponse(Schema):
    msg: str

@router.get("/hello/", response=HelloResponse, auth=None)
def hello(request):
    return {"msg": "Hello World"}

def create_access_token(user):
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

class SignInSchema(Schema):
    username: str
    password: str


@router.get("/courses/", response=list[CourseSchemaOut], auth=None)
def list_courses(request):
    courses = Course.objects.all()
    return courses

@router.get("/courses/{course_id}", response=CourseSchemaOut, auth=None)
def list_course(request, course_id: int):
    course = Course.objects.filter(id=course_id).first()
    return course

@router.post("/courses/")
def create_course(request, name: str = Form(...), description: str = Form(...), price: int = Form(...), image: UploadedFile = File(None)):

    user, created = User.objects.get_or_create(username="user", defaults={"password": "password"}) # temporary fix

    course = Course.objects.create(
        name=name,
        description=description,
        price=price,
        teacher=user,
        image=image
    )
    return Response({"id": course.id, "name": course.name}, status=201)

@router.api_operation(["POST", "PATCH"], "/courses/{course_id}/")
def update_course(
    request,
    course_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    image: UploadedFile = File(None)
):
    course = get_object_or_404(Course, id=course_id)

    # user = request.user

    user, created = User.objects.get_or_create(username="user", defaults={"password": "password"}) # temporary fix

    if user != course.teacher:
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

    course.name = name
    course.description = description
    course.price = price

    if image:
        course.image = image
    course.save()

    return {"id": course.id, "name": course.name}

@router.post("/courses/{course_id}/enroll/")
def enroll_course(request, course_id: int):
    course = get_object_or_404(Course, id=course_id)

    user, created = User.objects.get_or_create(username="user", defaults={"password": "password"}) # temporary fix

    if CourseMember.objects.filter(course_id=course, user_id=user).exists():
        raise HttpError(400, "You are already enrolled in this course.")

    CourseMember.objects.create(course_id=course, user_id=user)
    return {"message": "Enrolled successfully"}

@router.post("/contents/{content_id}/comments/")
def create_comment(request, content_id: int, payload: CourseCommentIn):
    comment = payload.comment

    if not comment:
        return Response({"error": "Comment is required."}, status=status.HTTP_400_BAD_REQUEST)

    # user = request.user
    user, created = User.objects.get_or_create(username="user", defaults={"password": "password"}) # temporary fix

    content = get_object_or_404(CourseContent, id=content_id)
    course = get_object_or_404(Course, id=content.course_id.id)
    member = get_object_or_404(CourseMember, user_id=user, course_id=course)

    user, created = User.objects.get_or_create(username="userr", defaults={"password": "password"}) # temporary fix

    if user != member.user_id:
        return Response({'error': 'You are not authorized to create comment in this content'}, status=status.HTTP_401_UNAUTHORIZED)

    comment = Comment.objects.create(
        content_id=content,
        member_id=member,
        comment=comment
    )

    return Response({
        "id": comment.id,
        "comment": comment.comment,
        "content_id": content.id
    }, status=201)

@router.delete("/comments/{comment_id}/")
def delete_comment(request, comment_id: int):

    comment = get_object_or_404(Comment, id=comment_id)

    user, created = User.objects.get_or_create(username="user", defaults={"password": "password"}) # temporary fix

    # Only allow the comment author to delete
    if comment.member_id.user_id != user:
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    comment.delete()

    return {'detail': 'Comment deleted'}
