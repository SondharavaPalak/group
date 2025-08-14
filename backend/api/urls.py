from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
	SubjectViewSet, TopicViewSet, ChapterViewSet, ResourceViewSet, ResourceVersionViewSet,
	QuizViewSet, QuestionViewSet, QuizAttemptViewSet, HomeworkViewSet, HomeworkSubmissionViewSet,
	BookmarkViewSet, NotificationViewSet, TopicProgressViewSet, me, search, dashboard, generate_questions, ai_chat
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'topics', TopicViewSet)
router.register(r'chapters', ChapterViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'resource-versions', ResourceVersionViewSet)
router.register(r'quizzes', QuizViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'attempts', QuizAttemptViewSet)
router.register(r'homeworks', HomeworkViewSet)
router.register(r'submissions', HomeworkSubmissionViewSet)
router.register(r'bookmarks', BookmarkViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'progress', TopicProgressViewSet)

urlpatterns = [
	path('auth/me/', me, name='me'),
	path('auth/token/', obtain_auth_token),
	path('search/', search),
	path('dashboard/', dashboard),
	path('ai/generate-questions/', generate_questions),
	path('ai/chat/', ai_chat),
	path('', include(router.urls)),
]