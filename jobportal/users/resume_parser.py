import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import PyPDF2
import docx

nltk.download('punkt')
nltk.download('stopwords')

class ResumeParser:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def extract_text_from_pdf(self, pdf_path):
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        return text
    
    def extract_text_from_docx(self, docx_path):
        doc = docx.Document(docx_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def extract_text(self, file_path):
        if file_path.endswith('.pdf'):
            return self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def extract_skills(self, text):
        # Common skills to look for
        common_skills = [
            "python", "java", "javascript", "html", "css", "react", "angular", "vue", 
            "django", "flask", "node.js", "express", "sql", "nosql", "mongodb", 
            "postgresql", "mysql", "aws", "azure", "gcp", "docker", "kubernetes",
            "git", "agile", "scrum", "project management", "data analysis", "machine learning"
        ]
        
        # Tokenize and clean text
        tokens = word_tokenize(text.lower())
        cleaned_tokens = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        
        # Extract skills
        skills = []
        for skill in common_skills:
            if skill in text.lower():
                skills.append(skill)
        
        return skills
    
    def extract_education(self, text):
        education = []
        
        # Look for education keywords
        education_keywords = ["bachelor", "master", "phd", "degree", "university", "college", "school"]
        
        # Regular expressions for education
        education_patterns = [
            r'(bachelor|master|phd|b\.s\.|m\.s\.|b\.a\.|m\.a\.|ph\.d\.).*?(degree|in).*?([a-z\s]+)',
            r'(university|college|institute).*?of.*?([a-z\s]+)',
            r'(studied|graduated).*?(from|at).*?([a-z\s]+)'
        ]
        
        for pattern in education_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                education.append(match.group(0))
        
        return education
    
    def extract_experience(self, text):
        experience = []
        
        # Regular expressions for work experience
        experience_patterns = [
            r'(worked|work|employed).*?(at|for|with).*?([a-z\s]+)',
            r'(experience|position|role).*?(as|in).*?([a-z\s]+)',
            r'([0-9]+).*?(years|months).*?(experience|work)'
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                experience.append(match.group(0))
        
        return experience
    
    def parse_resume(self, file_path):
        text = self.extract_text(file_path)
        
        return {
            'skills': self.extract_skills(text),
            'education': self.extract_education(text),
            'experience': self.extract_experience(text)
        }

