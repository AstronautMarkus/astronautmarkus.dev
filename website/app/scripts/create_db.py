import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app
from app.models.models import db
from app.models.models import (
    TechStack,
    PortfolioProject,
    TechTag,
    ProjectTechTag,
    WorkExperience,
    ExperienceTechnology,
    WorkExperienceTechnology,
    ExtraYoutubeSong,
    ExtraYoutubeVideo,
)

def load_techstack_data():
    json_path = os.path.join(os.path.dirname(__file__), 'techstack_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_portfolio_data():
    json_path = os.path.join(os.path.dirname(__file__), 'portfolio_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_working_experience_data():
    json_path = os.path.join(os.path.dirname(__file__), 'working_experience_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_extras_data():
    json_path = os.path.join(os.path.dirname(__file__), 'extras.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == '')

def init_database():
    """Initialize the database by creating tables and inserting tech stack and portfolio data."""
    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Tables created successfully")
        # Insert tech stack data
        techstack_data = load_techstack_data()
        for item in techstack_data:
            exists = TechStack.query.filter_by(name=item['name'], type=item['type']).first()
            if not exists:
                db.session.add(TechStack(**item))
        db.session.commit()
        print("Tech stack data inserted.")
        # Insert portfolio projects and tags
        portfolio_data = load_portfolio_data()
        tag_cache = {}
        for project in portfolio_data:
            # Insert tags if not exist
            tag_ids = []
            for tag_name in project['tags']:
                tag = TechTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = TechTag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()  # Get tag.id
                tag_ids.append(tag.id)
            db.session.flush()
            p = PortfolioProject(
                title=project['title'],
                description=project['description'],
                spanish_description=project['spanish_description'],
                project_url=project['project_url'],
                image_url=project.get('image_url')
            )
            db.session.add(p)
            db.session.flush()
            for tag_id in tag_ids:
                db.session.add(ProjectTechTag(project_id=p.id, tech_tag_id=tag_id))
        db.session.commit()
        print("Portfolio projects and tags inserted.")
        # Insert working experience and technologies
        working_experience_data = load_working_experience_data()
        for experience in working_experience_data:
            if is_blank(experience.get('name')) and is_blank(experience.get('description')):
                continue

            work_experience = WorkExperience.query.filter_by(
                name=experience['name'],
                type_of_project=experience['type_of_project']
            ).first()

            if not work_experience:
                work_experience = WorkExperience(
                    name=experience['name'],
                    spanish_name=experience['spanish_name'],
                    description=experience['description'],
                    spanish_description=experience['spanish_description'],
                    type_of_project=experience['type_of_project'],
                    spanish_type_of_project=experience['spanish_type_of_project'],
                    role_that_i_had=experience['role_that_i_had'],
                    spanish_role_that_i_had=experience['spanish_role_that_i_had']
                )
                db.session.add(work_experience)
                db.session.flush()

            for tech in experience.get('technologies_used', []):
                tech_name = (tech.get('name') or '').strip()
                if not tech_name:
                    continue

                technology = ExperienceTechnology.query.filter_by(name=tech_name).first()
                if not technology:
                    technology = ExperienceTechnology(name=tech_name)
                    db.session.add(technology)
                    db.session.flush()

                relation_exists = WorkExperienceTechnology.query.filter_by(
                    work_experience_id=work_experience.id,
                    experience_technology_id=technology.id
                ).first()

                if not relation_exists:
                    db.session.add(
                        WorkExperienceTechnology(
                            work_experience_id=work_experience.id,
                            experience_technology_id=technology.id
                        )
                    )

        db.session.commit()
        print("Working experience data inserted.")

        # Insert extras songs and videos
        extras_data = load_extras_data()

        for song in extras_data.get('youtube_songs', []):
            title = (song.get('title') or '').strip()
            youtube_url = (song.get('youtube_url') or '').strip()
            if not title or not youtube_url:
                continue

            exists = ExtraYoutubeSong.query.filter_by(
                title=title,
                youtube_url=youtube_url
            ).first()
            if not exists:
                db.session.add(ExtraYoutubeSong(title=title, youtube_url=youtube_url))

        for video in extras_data.get('youtube_videos', []):
            title = (video.get('title') or '').strip()
            youtube_url = (video.get('youtube_url') or '').strip()
            if not title or not youtube_url:
                continue

            exists = ExtraYoutubeVideo.query.filter_by(
                title=title,
                youtube_url=youtube_url
            ).first()
            if not exists:
                db.session.add(ExtraYoutubeVideo(title=title, youtube_url=youtube_url))

        db.session.commit()
        print("Extras songs and videos inserted.")

def reset_database():
    """Delete all tables and recreate them."""
    app = create_app()
    with app.app_context():
        print("Deleting tables...")
        db.drop_all()
        print("Tables deleted")
        init_database()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == "--reset":
            reset_database()
        else:
            print(f"Invalid flag: {flag}")
            print("Valid flag: --reset")
            print("No action was performed.")
    else:
        init_database()