from django.db import models
from django.contrib.auth.models import User


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Subject(TimestampedModel):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return self.name


class Topic(TimestampedModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=128)

    class Meta:
        unique_together = ('subject', 'name')

    def __str__(self) -> str:
        return f"{self.subject.name} - {self.name}"


class Chapter(TimestampedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=128)

    class Meta:
        unique_together = ('topic', 'title')

    def __str__(self) -> str:
        return f"{self.topic.subject.name} - {self.topic.name} - {self.title}"


class Resource(TimestampedModel):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resources')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tags = models.TextField(blank=True, help_text='Comma-separated tags')
    difficulty = models.CharField(max_length=16, choices=DIFFICULTY_CHOICES, default='medium')

    def __str__(self) -> str:
        return self.title


class ResourceVersion(TimestampedModel):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='versions')
    file = models.FileField(upload_to='resources/')
    version_number = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    file_mime = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ['-version_number']


class Quiz(TimestampedModel):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    is_timed = models.BooleanField(default=False)
    time_limit_seconds = models.PositiveIntegerField(default=0)
    randomize_order = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class Question(TimestampedModel):
    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('tf', 'True/False'),
        ('short', 'Short Answer'),
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPES)
    difficulty = models.CharField(max_length=16, default='medium')
    explanation = models.TextField(blank=True)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)


class QuizAttempt(TimestampedModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.FloatField(default=0)
    time_taken_seconds = models.PositiveIntegerField(default=0)


class AttemptAnswer(TimestampedModel):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)


class Homework(TimestampedModel):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeworks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()


class HomeworkSubmission(TimestampedModel):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homework_submissions')
    text_response = models.TextField(blank=True)
    file = models.FileField(upload_to='homework_submissions/', blank=True, null=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)


class Bookmark(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, null=True, blank=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = (('user', 'resource'), ('user', 'quiz'))


class Notification(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)


class TopicProgress(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topic_progress')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'topic')
