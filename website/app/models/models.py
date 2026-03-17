from .. import db

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    color = db.Column(db.Enum('hotpink', 'cyan', 'lime', 'gold', 'orchid', 'skyblue', 'khaki', 'plum', 'lightcoral', 'palegreen'), nullable=False, default='hotpink')
    ip_address = db.Column(db.String(45), nullable=False)
    language = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    language = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class TechStack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300), nullable=True)

class PortfolioProject (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    project_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    spanish_description = db.Column(db.String(500), nullable=False)
    project_url = db.Column(db.String(200), nullable=True)
    tech_tags = db.relationship('TechTag', secondary='project_tech_tag', backref='projects')
    image_url = db.Column(db.String(200), nullable=True)

class TechTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class ProjectTechTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('portfolio_project.id'), nullable=False)
    tech_tag_id = db.Column(db.Integer, db.ForeignKey('tech_tag.id'), nullable=False)

class WorkExperience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    spanish_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(1200), nullable=False)
    spanish_description = db.Column(db.String(1200), nullable=False)
    type_of_project = db.Column(db.String(300), nullable=False)
    spanish_type_of_project = db.Column(db.String(300), nullable=False)
    role_that_i_had = db.Column(db.String(200), nullable=False)
    spanish_role_that_i_had = db.Column(db.String(200), nullable=False)
    technologies = db.relationship('ExperienceTechnology', secondary='work_experience_technology', backref='work_experiences')

class ExperienceTechnology(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

class WorkExperienceTechnology(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    work_experience_id = db.Column(db.Integer, db.ForeignKey('work_experience.id'), nullable=False)
    experience_technology_id = db.Column(db.Integer, db.ForeignKey('experience_technology.id'), nullable=False)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=True)
    utm_source = db.Column(db.String(100), nullable=True)
    visited_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class ExtraYoutubeSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    youtube_url = db.Column(db.String(200), nullable=False)

class ExtraYoutubeVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    youtube_url = db.Column(db.String(200), nullable=False)