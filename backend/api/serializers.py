from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Subject, Topic, Chapter, Resource, ResourceVersion, Quiz, Question, Choice, QuizAttempt, AttemptAnswer, Homework, HomeworkSubmission, Bookmark, Notification, TopicProgress


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = "__all__"


class ResourceVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceVersion
        fields = ["id", "file", "version_number", "notes", "extracted_text", "file_mime", "created_at"]
        read_only_fields = ["extracted_text", "file_mime"]


class ResourceSerializer(serializers.ModelSerializer):
    versions = ResourceVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = [
            "id",
            "uploader",
            "subject",
            "topic",
            "chapter",
            "title",
            "description",
            "tags",
            "difficulty",
            "created_at",
            "updated_at",
            "versions",
        ]
        read_only_fields = ["uploader"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]
        extra_kwargs = {"is_correct": {"write_only": True}}


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "question_type", "difficulty", "explanation", "choices"]

    def create(self, validated_data):
        choices_data = validated_data.pop("choices", [])
        question = Question.objects.create(**validated_data)
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)
        return question

    def update(self, instance, validated_data):
        choices_data = validated_data.pop("choices", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if choices_data is not None:
            instance.choices.all().delete()
            for choice in choices_data:
                Choice.objects.create(question=instance, **choice)
        return instance


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "creator",
            "title",
            "subject",
            "topic",
            "chapter",
            "is_timed",
            "time_limit_seconds",
            "randomize_order",
            "questions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["creator"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        for q in questions_data:
            choices = q.pop("choices", [])
            question = Question.objects.create(quiz=quiz, **q)
            for c in choices:
                Choice.objects.create(question=question, **c)
        return quiz


class AttemptAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ["id", "attempt", "question", "selected_choice", "text_answer", "is_correct"]
        read_only_fields = ["is_correct"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AttemptAnswerSerializer(many=True, required=False)

    class Meta:
        model = QuizAttempt
        fields = ["id", "quiz", "student", "score", "time_taken_seconds", "answers", "created_at"]
        read_only_fields = ["score"]


class HomeworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = "__all__"


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkSubmission
        fields = "__all__"


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class TopicProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicProgress
        fields = "__all__"