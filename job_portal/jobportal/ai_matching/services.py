import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from jobs.models import Job
from users.models import UserProfile
from .models import JobRecommendation

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

class JobMatchingService:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer()
    
    def preprocess_text(self, text):
        if not text:
            return ""
        tokens = word_tokenize(text.lower())
        filtered_tokens = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        return " ".join(filtered_tokens)
    
    def get_job_features(self, job):
        # Combine relevant job fields
        job_text = f"{job.title} {job.description} {job.requirements} {job.responsibilities} {job.skills_required}"
        return self.preprocess_text(job_text)
    
    def get_user_features(self, user_profile):
        # Combine relevant user profile fields
        user_text = f"{user_profile.skills} {user_profile.experience} {user_profile.education} {user_profile.bio}"
        return self.preprocess_text(user_text)
    
    def calculate_similarity(self, job_features, user_features):
        # Combine texts for vectorization
        texts = [job_features, user_features]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity
    
    def generate_recommendations(self, user, max_recommendations=10):
        user_profile = user.profile
        user_features = self.get_user_features(user_profile)
        
        # Get active jobs
        active_jobs = Job.objects.filter(is_active=True)
        
        recommendations = []
        for job in active_jobs:
            job_features = self.get_job_features(job)
            similarity_score = self.calculate_similarity(job_features, user_features)
            
            # Store recommendation if score is above threshold
            if similarity_score > 0.1:  # Adjust threshold as needed
                recommendations.append((job, similarity_score))
        
        # Sort by similarity score and take top N
        recommendations.sort(key=lambda x: x[1], reverse=True)
        top_recommendations = recommendations[:max_recommendations]
        
        # Save recommendations to database
        JobRecommendation.objects.filter(user=user).delete()  # Clear old recommendations
        for job, score in top_recommendations:
            JobRecommendation.objects.create(
                user=user,
                job=job,
                score=score
            )
        
        return top_recommendations

