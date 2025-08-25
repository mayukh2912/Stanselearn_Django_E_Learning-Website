from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.core.validators import MinValueValidator, MaxValueValidator
from embed_video.fields import EmbedVideoField
from django.utils import timezone
from django.core.exceptions import ValidationError



class User(AbstractUser):
    """Extended user model with role-based access control."""
    is_learner = models.BooleanField(default=False, help_text="Designates whether this user is a learner")
    is_instructor = models.BooleanField(default=False, help_text="Designates whether this user is an instructor")
    is_admin = models.BooleanField(default=False, help_text="Designates whether this user is an admin")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or 'No name'})"


class Profile(models.Model):
    """User profile model with additional personal information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profiles/avatars/', default='no-img.jpg', blank=True)
    first_name = models.CharField(max_length=255, default='', blank=True)
    last_name = models.CharField(max_length=255, default='', blank=True)
    email = models.EmailField(unique=True)
    phonenumber = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(default='2000-01-01')
    bio = models.TextField(default='', blank=True)
    city = models.CharField(max_length=255, default='', blank=True)
    state = models.CharField(max_length=255, default='', blank=True)
    country = models.CharField(max_length=255, default='', blank=True)
    favorite_animal = models.CharField(max_length=255, default='', blank=True)
    hobby = models.CharField(max_length=255, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ['user__username']

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def clean(self):
        if self.email and Profile.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError("Email already exists")


class Announcement(models.Model):
    """System announcements for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255, default='Announcement')
    content = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['-posted_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class Course(models.Model):
    """Course model for organizing tutorials and quizzes."""
    COURSE_CHOICES = [
        ('programming', 'Programming'),
        ('design', 'Design'),
        ('business', 'Business'),
        ('marketing', 'Marketing'),
        ('science', 'Science'),
        ('language', 'Language'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#007bff')
    description = models.TextField(default='', blank=True)
    category = models.CharField(max_length=20, choices=COURSE_CHOICES, default='programming')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    def get_html_badge(self):
        name = escape(self.name)
        color = escape(self.color)
        html = '<span class="badge badge-primary" style="background-color: %s">%s</span>' % (color, name)
        return mark_safe(html)


class Tutorial(models.Model):
    """Tutorial model for course content."""
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    thumb = models.ImageField(upload_to='tutorials/thumbnails/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tutorials')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tutorials')
    video = EmbedVideoField(blank=True, null=True)
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_minutes = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    is_published = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tutorial"
        verbose_name_plural = "Tutorials"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_published']),
        ]

    def __str__(self):
        return f"{self.title} ({self.course.name})"


class Notes(models.Model):
    """Notes model for additional course materials."""
    title = models.CharField(max_length=500)
    file = models.FileField(upload_to='notes/files/', null=True, blank=True)
    cover = models.ImageField(upload_to='notes/covers/', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.course.name}"

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        if self.cover:
            self.cover.delete(save=False)
        super().delete(*args, **kwargs)


class Quiz(models.Model):
    """Quiz model for assessments."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    description = models.TextField(default='', blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=30, validators=[MinValueValidator(1), MaxValueValidator(180)])
    passing_score = models.FloatField(default=70.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_attempts = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.course.name})"


class Question(models.Model):
    """Question model for quizzes."""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField('Question', max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    points = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]

    def __str__(self):
        return f"{self.text[:50]}... ({self.quiz.name})"


class Answer(models.Model):
    """Answer model for questions."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField('Answer', max_length=255)
    is_correct = models.BooleanField('Correct answer', default=False)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['question', 'order']),
        ]

    def __str__(self):
        return f"{self.text[:50]}... ({'Correct' if self.is_correct else 'Incorrect'})"


class Learner(models.Model):
    """Learner profile model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    quizzes = models.ManyToManyField(Quiz, through='TakenQuiz', related_name='learners')
    interests = models.ManyToManyField(Course, related_name='interested_learners')
    total_score = models.FloatField(default=0.0)
    quizzes_completed = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Learner"
        verbose_name_plural = "Learners"
        ordering = ['user__username']

    def __str__(self):
        return f"Learner: {self.user.username}"

    def get_unanswered_questions(self, quiz):
        """Get questions that the learner hasn't answered for a specific quiz."""
        answered_questions = self.quiz_answers \
            .filter(answer__question__quiz=quiz) \
            .values_list('answer__question__pk', flat=True)
        questions = quiz.questions.exclude(pk__in=answered_questions).order_by('order', 'id')
        return questions


class Instructor(models.Model):
    """Instructor profile model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    expertise = models.ManyToManyField(Course, related_name='instructors')
    bio = models.TextField(default='', blank=True)
    years_experience = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Instructor"
        verbose_name_plural = "Instructors"
        ordering = ['user__username']

    def __str__(self):
        return f"Instructor: {self.user.username}"


class TakenQuiz(models.Model):
    """Model to track quiz attempts by learners."""
    learner = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='taken_quizzes')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='taken_quizzes')
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    date = models.DateTimeField(auto_now_add=True)
    time_taken_minutes = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=True)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Taken Quiz"
        verbose_name_plural = "Taken Quizzes"
        ordering = ['-date']
        unique_together = ['learner', 'quiz', 'attempt_number']
        indexes = [
            models.Index(fields=['learner', '-date']),
            models.Index(fields=['quiz', '-date']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.learner.user.username} - {self.quiz.name} ({self.score}%)"


class LearnerAnswer(models.Model):
    """Model to track learner answers."""
    student = models.ForeignKey(Learner, on_delete=models.CASCADE, related_name='quiz_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='learner_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='learner_answers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Learner Answer"
        verbose_name_plural = "Learner Answers"
        unique_together = ['student', 'question']
        indexes = [
            models.Index(fields=['student', 'question']),
            models.Index(fields=['answer']),
        ]

    def __str__(self):
        return f"{self.student.user.username} - {self.question.text[:30]}..."
