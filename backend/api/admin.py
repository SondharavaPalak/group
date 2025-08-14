from django.contrib import admin
from .models import Subject, Topic, Chapter, Resource, ResourceVersion, Quiz, Question, Choice, QuizAttempt, AttemptAnswer, Homework, HomeworkSubmission, Bookmark, Notification, TopicProgress


admin.site.register([
	Subject,
	Topic,
	Chapter,
	Resource,
	ResourceVersion,
	Quiz,
	Question,
	Choice,
	QuizAttempt,
	AttemptAnswer,
	Homework,
	HomeworkSubmission,
	Bookmark,
	Notification,
	TopicProgress,
])
