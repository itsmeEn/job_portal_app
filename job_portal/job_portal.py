from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from .models import Job, Application, Profile, Notification, Conversation, Message
from .forms import JobForm, ApplicationForm, ProfileForm, MessageForm
from .utils import send_notification, send_email
from .decorators import role_required
from .constants import APPLICATION_STATUS_CHOICES, JOB_TYPE_CHOICES, EXPERIENCE_LEVEL_CHOICES
from .services import job_matching_service, resume_parser_service, skill_analysis_service
from .tasks import process_job_application, send_application_notification
from .serializers import JobSerializer, ApplicationSerializer
from .permissions import IsRecruiter, IsApplicant
from .exceptions import JobNotFoundError, ApplicationError
from .validators import validate_job_data, validate_application_data
from .middleware import RequestLoggingMiddleware
from .signals import application_submitted
from .admin import JobAdmin, ApplicationAdmin
from .apps import JobPortalConfig
from .urls import urlpatterns
from .wsgi import application
from .asgi import application as asgi_application
from .settings import *
from .celery import app as celery_app

# ... existing code ... 