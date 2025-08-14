from django.db.models import Max, Q, Avg
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Subject, Topic, Chapter, Resource, ResourceVersion, Quiz, Question, Choice, QuizAttempt, AttemptAnswer, Homework, HomeworkSubmission, Bookmark, Notification, TopicProgress
from .serializers import (
	UserSerializer,
	SubjectSerializer,
	TopicSerializer,
	ChapterSerializer,
	ResourceSerializer,
	ResourceVersionSerializer,
	QuizSerializer,
	QuestionSerializer,
	QuizAttemptSerializer,
	HomeworkSerializer,
	HomeworkSubmissionSerializer,
	BookmarkSerializer,
	NotificationSerializer,
	TopicProgressSerializer,
)

try:
	from PyPDF2 import PdfReader
except Exception:
	PdfReader = None


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
	return Response(UserSerializer(request.user).data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def search(request):
	q = request.GET.get('q', '').strip()
	resources = Resource.objects.all()
	if q:
		resources = resources.filter(
			Q(title__icontains=q) |
			Q(description__icontains=q) |
			Q(tags__icontains=q) |
			Q(versions__extracted_text__icontains=q)
		).distinct()
	quizzes = Quiz.objects.filter(Q(title__icontains=q) | Q(questions__text__icontains=q)).distinct()
	return Response({
		"resources": ResourceSerializer(resources[:50], many=True).data,
		"quizzes": QuizSerializer(quizzes[:50], many=True).data,
	})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
	user = request.user
	attempts = QuizAttempt.objects.filter(student=user)
	avg_score = attempts.aggregate(s=Avg('score')).get('s') or 0
	by_subject = (
		attempts
		.values('quiz__subject__name')
		.annotate(avg=Avg('score'))
		.order_by('quiz__subject__name')
	)
	return Response({
		"avg_score": avg_score,
		"subjects": list(by_subject),
		"num_attempts": attempts.count(),
	})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def ai_chat(request):
	question = (request.data.get('question') or '').strip()
	subject_id = request.data.get('subject')
	topic_id = request.data.get('topic')
	chapter_id = request.data.get('chapter')
	if not question:
		return Response({"detail": "question is required"}, status=400)
	qs = Resource.objects.all()
	if subject_id:
		qs = qs.filter(subject_id=subject_id)
	if topic_id:
		qs = qs.filter(topic_id=topic_id)
	if chapter_id:
		qs = qs.filter(chapter_id=chapter_id)
	qs = qs.filter(
		Q(title__icontains=question) |
		Q(description__icontains=question) |
		Q(tags__icontains=question) |
		Q(versions__extracted_text__icontains=question)
	).distinct()
	best_resource = qs.prefetch_related('versions').first()
	if not best_resource:
		return Response({"answer": "I couldn't find anything relevant in your materials.", "resource_id": None, "resource_title": None})
	snippet = ""
	text = ""
	for v in best_resource.versions.all():
		if v.extracted_text:
			text = v.extracted_text
			break
	if not text:
		text = (best_resource.description or '')
	q_lower = question.lower()
	idx = text.lower().find(q_lower)
	if idx == -1:
		idx = 0
	start = max(0, idx - 200)
	end = min(len(text), idx + 200)
	snippet = text[start:end].strip()
	if start > 0:
		snippet = "... " + snippet
	if end < len(text):
		snippet = snippet + " ..."
	return Response({
		"answer": snippet or "I found a related resource but couldn't extract a preview.",
		"resource_id": best_resource.id,
		"resource_title": best_resource.title,
	})


class SubjectViewSet(viewsets.ModelViewSet):
	queryset = Subject.objects.all().order_by('name')
	serializer_class = SubjectSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TopicViewSet(viewsets.ModelViewSet):
	queryset = Topic.objects.select_related('subject').all()
	serializer_class = TopicSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ChapterViewSet(viewsets.ModelViewSet):
	queryset = Chapter.objects.select_related('topic', 'topic__subject').all()
	serializer_class = ChapterSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ResourceViewSet(viewsets.ModelViewSet):
	queryset = Resource.objects.select_related('uploader').all().order_by('-created_at')
	serializer_class = ResourceSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]
	parser_classes = [MultiPartParser, FormParser]

	def get_queryset(self):
		qs = super().get_queryset()
		subject = self.request.query_params.get('subject')
		topic = self.request.query_params.get('topic')
		chapter = self.request.query_params.get('chapter')
		difficulty = self.request.query_params.get('difficulty')
		q = self.request.query_params.get('q')
		filetype = self.request.query_params.get('filetype')
		if subject:
			qs = qs.filter(subject_id=subject)
		if topic:
			qs = qs.filter(topic_id=topic)
		if chapter:
			qs = qs.filter(chapter_id=chapter)
		if difficulty:
			qs = qs.filter(difficulty=difficulty)
		if q:
			qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q) | Q(versions__extracted_text__icontains=q)).distinct()
		if filetype:
			qs = qs.filter(versions__file_mime__icontains=filetype).distinct()
		return qs

	def perform_create(self, serializer):
		resource = serializer.save(uploader=self.request.user)
		file = self.request.data.get('file')
		if file:
			latest = resource.versions.aggregate(v=Max('version_number')).get('v') or 0
			version = ResourceVersion(resource=resource, version_number=latest + 1, file=file)
			mime = getattr(file, 'content_type', '') or ''
			version.file_mime = mime
			if mime and 'pdf' in mime.lower() and PdfReader is not None:
				try:
					reader = PdfReader(file)
					texts = []
					for page in reader.pages:
						texts.append(page.extract_text() or '')
					version.extracted_text = "\n".join(texts)
				except Exception:
					version.extracted_text = ''
			version.save()

	@action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
	def upload_version(self, request, pk=None):
		resource = self.get_object()
		latest_version = resource.versions.aggregate(v=Max('version_number')).get('v') or 0
		next_version = latest_version + 1
		file = request.data.get('file')
		notes = request.data.get('notes', '')
		if not file:
			return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
		mime = getattr(file, 'content_type', '') or ''
		version = ResourceVersion.objects.create(resource=resource, file=file, notes=notes, version_number=next_version, file_mime=mime)
		if mime and 'pdf' in mime.lower() and PdfReader is not None:
			try:
				reader = PdfReader(version.file)
				texts = []
				for page in reader.pages:
					texts.append(page.extract_text() or '')
				version.extracted_text = "\n".join(texts)
				version.save()
			except Exception:
				pass
		return Response(ResourceVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class ResourceVersionViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = ResourceVersion.objects.select_related('resource').all()
	serializer_class = ResourceVersionSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class QuizViewSet(viewsets.ModelViewSet):
	queryset = Quiz.objects.all().order_by('-created_at')
	serializer_class = QuizSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]

	def perform_create(self, serializer):
		serializer.save(creator=self.request.user)

	@action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
	def take(self, request, pk=None):
		quiz = self.get_object()
		questions = list(quiz.questions.all())
		if quiz.randomize_order:
			import random
			random.shuffle(questions)
		return Response(QuestionSerializer(questions, many=True).data)

	@action(detail=True, methods=['post'])
	def grade(self, request, pk=None):
		quiz = self.get_object()
		student_id = request.data.get('student')
		answers = request.data.get('answers', [])
		if not student_id or not isinstance(answers, list):
			return Response({"detail": "student and answers[] required"}, status=status.HTTP_400_BAD_REQUEST)
		student = User.objects.get(id=student_id)
		attempt = QuizAttempt.objects.create(quiz=quiz, student=student)
		correct_count = 0
		for answer in answers:
			question_id = answer.get('question')
			selected_choice_id = answer.get('selected_choice')
			text_answer = answer.get('text_answer', '')
			question = Question.objects.get(id=question_id, quiz=quiz)
			selected_choice = None
			is_correct = False
			if question.question_type in ['mcq', 'tf']:
				if selected_choice_id:
					selected_choice = Choice.objects.get(id=selected_choice_id, question=question)
					is_correct = selected_choice.is_correct
			else:
				is_correct = bool(text_answer and text_answer.strip())
			AttemptAnswer.objects.create(
				attempt=attempt,
				question=question,
				selected_choice=selected_choice,
				text_answer=text_answer,
				is_correct=is_correct,
			)
			if is_correct:
				correct_count += 1
		total_questions = quiz.questions.count()
		attempt.score = (correct_count / total_questions) * 100 if total_questions else 0
		attempt.save()
		return Response(QuizAttemptSerializer(attempt).data)


class QuestionViewSet(viewsets.ModelViewSet):
	queryset = Question.objects.select_related('quiz').prefetch_related('choices').all()
	serializer_class = QuestionSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class QuizAttemptViewSet(viewsets.ModelViewSet):
	queryset = QuizAttempt.objects.select_related('quiz', 'student').prefetch_related('answers').all()
	serializer_class = QuizAttemptSerializer
	permission_classes = [permissions.IsAuthenticated]


class HomeworkViewSet(viewsets.ModelViewSet):
	queryset = Homework.objects.select_related('teacher').all().order_by('-created_at')
	serializer_class = HomeworkSerializer
	permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class HomeworkSubmissionViewSet(viewsets.ModelViewSet):
	queryset = HomeworkSubmission.objects.select_related('homework', 'student').all().order_by('-created_at')
	serializer_class = HomeworkSubmissionSerializer
	permission_classes = [permissions.IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser]


class BookmarkViewSet(viewsets.ModelViewSet):
	queryset = Bookmark.objects.select_related('user').all()
	serializer_class = BookmarkSerializer
	permission_classes = [permissions.IsAuthenticated]


class NotificationViewSet(viewsets.ModelViewSet):
	queryset = Notification.objects.select_related('user').all().order_by('-created_at')
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=True, methods=['post'])
	def mark_read(self, request, pk=None):
		n = self.get_object()
		n.is_read = True
		n.save(update_fields=['is_read'])
		return Response({"status": "ok"})


class TopicProgressViewSet(viewsets.ModelViewSet):
	queryset = TopicProgress.objects.select_related('user', 'topic').all()
	serializer_class = TopicProgressSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=False, methods=['post'])
	def mark_complete(self, request):
		topic_id = request.data.get('topic')
		if not topic_id:
			return Response({"detail": "topic required"}, status=400)
		obj, _ = TopicProgress.objects.get_or_create(user=request.user, topic_id=topic_id)
		obj.is_completed = True
		obj.save(update_fields=['is_completed'])
		return Response(TopicProgressSerializer(obj).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def generate_questions(request):
	"""Naive AI-like generator: split text into sentences and craft MCQs."""
	text = request.data.get('text', '')
	file = request.data.get('file')
	if not text and file and PdfReader is not None:
		try:
			reader = PdfReader(file)
			texts = []
			for page in reader.pages:
				texts.append(page.extract_text() or '')
			text = "\n".join(texts)
		except Exception:
			text = ''
	if not text:
		return Response({"detail": "Provide text or PDF file"}, status=400)
	# naive sentence split
	sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
	questions = []
	for i, s in enumerate(sentences[:5]):
		stem = f"Which statement best matches: '{s[:80]}...' ?"
		correct = s[:100]
		distractors = []
		for ds in sentences[5:15]:
			if ds != s:
				distractors.append(ds[:100])
				if len(distractors) == 3:
					break
		while len(distractors) < 3:
			distractors.append(f"Option {len(distractors)+1}")
		questions.append({
			"text": stem,
			"question_type": "mcq",
			"choices": [
				{"text": correct, "is_correct": True},
				{"text": distractors[0], "is_correct": False},
				{"text": distractors[1], "is_correct": False},
				{"text": distractors[2], "is_correct": False},
			]
		})
	return Response({"questions": questions})
