from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(200), nullable=True)
    utm_source = db.Column(db.String(100), nullable=True)
    visited_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PortfolioProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # English content (required)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Spanish content (optional)
    title_es = db.Column(db.String(200), nullable=True)
    description_es = db.Column(db.Text, nullable=True)
    has_es = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    # Shared fields
    image_path = db.Column(db.String(200), nullable=True)
    project_url = db.Column(db.String(200), nullable=True)
    github_repo_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    extra_images = db.relationship(
        'ExtraPortfolioImage',
        backref='project',
        lazy=True,
        cascade='all, delete-orphan',
    )

class ExtraPortfolioImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('portfolio_project.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class CvFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())


class BlogCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # English (required)
    name = db.Column(db.String(100), nullable=False, unique=True)
    # Spanish (optional)
    name_es = db.Column(db.String(100), nullable=True)
    has_es = db.Column(db.Boolean, nullable=False, default=False, server_default='0')

    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    posts = db.relationship('BlogPost', backref='category', lazy=True)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), nullable=False, unique=True)

    # English content (required)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    markdown_path = db.Column(db.String(200), nullable=True)

    # Spanish content (optional)
    title_es = db.Column(db.String(200), nullable=True)
    description_es = db.Column(db.Text, nullable=True)
    markdown_path_es = db.Column(db.String(200), nullable=True)
    has_es = db.Column(db.Boolean, nullable=False, default=False, server_default='0')

    # Metadata
    category_id = db.Column(db.Integer, db.ForeignKey('blog_category.id'), nullable=True)
    published = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    # Cover image
    cover_image_path = db.Column(db.String(200), nullable=True)

    images = db.relationship(
        'BlogPostImage',
        backref='post',
        lazy=True,
        cascade='all, delete-orphan',
    )


class BlogPostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), nullable=False, default='en')
    is_read = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())


class MailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(10), nullable=False, default='en')
    description = db.Column(db.String(200), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint('slug', 'language', name='uq_mail_template_slug_lang'),
    )