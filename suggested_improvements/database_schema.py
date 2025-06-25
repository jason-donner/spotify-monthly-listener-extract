# Suggested database schema using SQLAlchemy

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artists'
    
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(22), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    listener_data = db.relationship('ListenerData', backref='artist', lazy='dynamic')
    suggestions = db.relationship('Suggestion', backref='artist', lazy='dynamic')

class ListenerData(db.Model):
    __tablename__ = 'listener_data'
    
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    monthly_listeners = db.Column(db.Integer, nullable=False)
    date_recorded = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('artist_id', 'date_recorded'),)

class Suggestion(db.Model):
    __tablename__ = 'suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=True)
    artist_name = db.Column(db.String(255), nullable=False)
    spotify_url = db.Column(db.String(500))
    spotify_id = db.Column(db.String(22))
    status = db.Column(db.String(50), default='pending')  # pending, approved, processed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Migration benefits:
# - Better data integrity
# - Faster queries with proper indexing
# - Concurrent access support
# - Better relationship management
# - Easier data analysis and reporting
