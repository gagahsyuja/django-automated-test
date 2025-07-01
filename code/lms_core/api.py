from ninja import NinjaAPI, UploadedFile, File, Form, Router
from ninja.security import HttpBearer, HttpBasicAuth
from ninja.responses import Response
from lms_core.schema import CourseSchemaOut, CourseMemberOut, CourseMemberIn, CourseSchemaIn
from lms_core.schema import CourseContentIn, CourseContentMini, CourseContentFull
from lms_core.schema import CourseCommentOut, CourseCommentIn
from lms_core.schema import FeedbackOut, FeedbackIn
from lms_core.schema import UserOut, UserIn
from lms_core.schema import TokenResponse, TokenRequest
from lms_core.models import Course, CourseMember, CourseContent, CourseLimit, Comment, Feedback
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja.pagination import paginate, PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from lms_core.models import User
from django.http import JsonResponse
from typing import Optional
from ninja.throttling import AnonRateThrottle, UserRateThrottle
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser


from ninja import Router, Schema
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class GlobalAuth(HttpBearer):
    def authenticate(self, request, token: str):
        user = User.objects.filter(auth_token=token).first()
        if not user:
             user = AnonymousUser()
        request.user = user
        return user

router = Router(auth=GlobalAuth())

@router.post("/signin/", response=TokenResponse, auth=None)
def sign_in(request, payload: TokenRequest):
    user = authenticate(username=payload.username, password=payload.password)
    if not user or not user.is_active:
        return { "message": "Invalid credentials" }

    token, _created = Token.objects.get_or_create(user=user)

    user.auth_token = token
    user.save()

    return {
        "token": token.key
    }

# Get everything
@router.get("/whoami/")
def whoami(request):
    if request.user:
        return { "authenticated": request.user.is_authenticated, "username": request.user.username}
    else:
        return { "authenticated": request.user.is_authenticated }

@router.get("/users/", auth=None, response=list[UserOut])
def get_users(request):
    try:
        users = User.objects.all()
        return users
    except:
        return { "message": "Failed to get users" }

@router.get("/courses/", auth=None, response=list[CourseSchemaOut])
def get_courses(request):
    courses = Course.objects.all()
    return courses

@router.get("/comments/", auth=None, response=list[CourseCommentOut])
def get_comments(request):
    comments = Comment.objects.all()
    return comments

# Register (+) Limit 5/d (+)
@router.post("/register/", auth=None, throttle=[AnonRateThrottle('5/d')])
def create_user(request, firstname: str, lastname: str, email: str, password: str, username: str):
    user, created = User.objects.get_or_create(username=username)

    if not created:
        return { "message": f"User {username} already registered" }
    else:
        user.set_password(password)
        user.first_name = firstname
        user.last_name = lastname
        user.email = email
        user.save()
        return { "message": f"User {username} registered successfully" }

# Dashboard (+)
@router.get("/user/dashboard/{username}")
def get_user_dashboard(request, username: str):

    try:
        user = User.objects.get(username=username)
        course_member = CourseMember.objects.filter(user_id=user)
        course = Course.objects.filter(teacher=user)
        comment = Comment.objects.filter(member_id=user)

        return {
            "user": user.username,
            "course_followed_count": course_member.count(),
            "course_created_count": course.count(),
            "comment_count": comment.count(),
        }

    except User.DoesNotExist:
        return { "message": "User does not exist!" }

# Course Stats (+)
@router.get("/course/{course_id}/stats/", auth=None)
def get_course_statistics(request, course_id: int):

    try:
        course = Course.objects.get(id=course_id)
        course_member = CourseMember.objects.filter(course_id=course)
        course_content = CourseContent.objects.filter(course_id=course)
        comment = Comment.objects.filter(content_id__in=course_content)
        feedback = Feedback.objects.filter(course_id=course)

        return {
            "course_member_count": course_member.count(),
            "course_content_count": course_content.count(),
            "course_comment_count": comment.count(),
            "course_feedback_count": feedback.count()
        }

    except User.DoesNotExist:
        return { "message": "User does not exist!" }

# Feedback (+)(+)(+)(+)
@router.post("/feedback/add/")
def add_feedback(request, course_id: int, feedback: str):

    try:
        user_id = request.user.id
        course = Course.objects.get(id=course_id)
        user = User.objects.get(id=user_id)

        Feedback.objects.create(
            course_id=course,
            user_id=user,
            feedback=feedback
        )
        return {
            "user_id": user_id,
            "course_id": course_id,
            "feedback": feedback
        }
    except:
        return { "message": "Failed to create feedback" }

@router.get("/feedback/{course_id}/show/", auth=None)
def show_feedback(request, course_id: int):

    try:
        course = Course.objects.get(id=course_id)
        feedback = Feedback.objects.filter(course_id=course).values()

        data = list(feedback)
        return JsonResponse(data, safe=False)
    except:
        return { "message": "Failed to show feedback" }

@router.put("/feedback/{feedback_id}/edit/", response=FeedbackOut)
def update_feedback(request, feedback_id: int, payload: FeedbackIn):

    try:
        feedback = get_object_or_404(Feedback, id=feedback_id)

        for attr, value in payload.dict().items():
            setattr(feedback, attr, value)

        feedback.save()

        return feedback

    except:
        return { "message": "Failed to update feedback" }


@router.post("/feedback/delete/")
def delete_feedback(request, feedback_id: int):

    try:
        feedback = Feedback.objects.get(id=feedback_id)
        feedback.delete()

        return { "message": "Feedback deleted successfully" }
    except:
        return { "message": "Failed to delete feedback" }


# Limit Course Enrollment (+)
@router.post("/courses/{course_id}/enroll/")
def enroll_course(request, course_id: int, user_id: Optional[int] = None):

    try:
        course = get_object_or_404(Course, id=course_id)

        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = User.objects.get(id=request.user.id)

        all_member = CourseMember.objects.filter(course_id=course)
        member = CourseMember.objects.filter(course_id=course, user_id=user)


        if member.exists():
            return { "message": f"User {request.user.username} already enrolled in this course" }
        else:
            teacher = course.teacher

            try:
                limit = CourseLimit.objects.get(course_id=course)
                print(f"there's a limit, it's {limit.limit}")
            except CourseLimit.DoesNotExist:
                limit = None
                print(f"theres no limit")

            if not limit or all_member.count() < limit.limit:
                new_member = CourseMember.objects.create(course_id=course, user_id=user)
                return {
                    "id": new_member.id,
                    "course_id": new_member.course_id.id,
                    "user_id": new_member.user_id.id,
                    "roles": new_member.roles
                }
            else:
                return { "message": f"Course is full" }
    except:
        return { "message": "Failed to enroll student" }

# Batch enroll for teacher (+)
@router.post("/courses/batch_enroll/")
def batch_enroll_course(request, payload: list[CourseMemberIn]):

    results = []

    try:
        for entry in payload:
            course_id = entry.course_id
            user_id = entry.user_id

            results.append(enroll_course(request, course_id, user_id))

        return JsonResponse(results, safe=False)
    except:
        return { "message": "Failed to batch enroll student" }

@router.post("/courses/{course_id}/set_limit/{limit}/")
def course_set_limit(request, course_id: int, limit: int):

    try:
        user = get_object_or_404(User, id=request.user.id)
        course = get_object_or_404(Course, id=course_id)
        teacher = get_object_or_404(User, id=course.teacher.id)

        course_limit, created = CourseLimit.objects.update_or_create(course_id=course, teacher_id=teacher, limit=limit)

        return { "message": "Limit set successfully" if created else "Limit updated successfully" }
    except:
        return { "message": "Failed to set course limit" }

@router.get("/courses/{course_id}/limit/", auth=None)
def course_show_limit(request, course_id: int):

    try:
        course = get_object_or_404(Course, id=course_id)
        limit = get_object_or_404(CourseLimit, course_id=course)

        return { "course_id": course_id, "limit": limit.limit }
    except:
        return { "message": "Course does not have limit" }

@router.delete("/courses/{course_id}/limit/", auth=None)
def course_remove_limit(request, course_id: int):

    try:
        course = get_object_or_404(Course, id=course_id)
        limits = CourseLimit.objects.filter(course_id=course)

        for limit in limits:
            limit.delete()


        return { "message": "Limit successfully removed"}
    except:
        return { "message": "Failed to remove course limit" }

# Course Limit 1/d (+)
@router.post("/courses/", response=CourseSchemaOut, throttle=[UserRateThrottle("1/d")])
def create_course(request, payload: CourseSchemaIn, image: UploadedFile = File(None)):

    try:
        user_id = request.user.id
        user = User.objects.get(id=user_id)

        course = Course.objects.create(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            image=image,
            teacher=user
        )

        return course
    except:
        return { "message": "Failed to create course" }

# Content Limit 10/h (+)
@router.post("/contents/", response=CourseContentFull, throttle=[UserRateThrottle("10/h")])
def create_content(request, payload: CourseContentIn, image: UploadedFile = File(None)):

    try:
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=payload.course_id)

        content = CourseContent.objects.create(
            name=payload.name,
            description=payload.description,
            video_url=payload.video_url,
            course_id=course,
        )

        if payload.parent_id is not None:
            content.parent_id = payload.parent_id
            content.save()

        return content
    except:
        return { "message": "Failed to create content" }

# Comment Limit 10/h (+)
@router.post("/contents/{content_id}/comment/add/", throttle=[UserRateThrottle("10/h")])
def post_comment(request, content_id: int, comment: str):

    try:
        user_id = request.user.id
        content = CourseContent.objects.get(id=content_id)
        user = User.objects.get(id=user_id)

        Comment.objects.create(
            content_id=content,
            member_id=user,
            comment=comment
        )
        return {
            "user_id": user_id,
            "content_id": content.id,
            "comment": comment
        }
    except:
        return { "message": "Failed to post comment" }

# Profiles (+)
@router.get("/profiles/", auth=None)
def list_profiles(request):

    results = []

    try:
        users = User.objects.all()

        for user in users:
            courses = Course.objects.filter(teacher=user)
            members = CourseMember.objects.filter(user_id=user)

            results.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": str(user.phone_number),
                "description": user.description,
                "profile_image": user.profile_image.url if user.profile_image else None,
                "course_created": list(courses.values()),
                "course_followed": list(members.values())
            })

        return results

    except:
        return { "message": "Failed to list profiles" }

# # Edit Profiles (+)
@router.put("/profiles/")
def update_profile(
    request,
    email: Form[str],
    first_name: Form[str],
    last_name: Form[str],
    phone_number: Form[str],
    description: Form[str],
    image: UploadedFile = File(None)
):
    try:
        user = get_object_or_404(User, id=request.user.id)

        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        user.description = description

        if image is not None:
            user.profile_image.save(image.name, image)

        user.save()

        return {
            **user.__dict__,
            "phone_number": str(user.phone_number),
            "username": user.username,
            "image_url": user.profile_image.url if user.profile_image else None
        }
    except:
        return { "message": "Failed to edit profile" }
