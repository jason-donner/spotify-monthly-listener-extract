"""
Admin routes for the Spotify Listener Tracker app.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_admin_routes(spotify_service, data_service, job_service):
    """Create admin routes blueprint with injected services."""
    
    admin_bp = Blueprint('admin', __name__)
    
    @admin_bp.route("/")
    def admin():
        """Admin page to review and manage artist suggestions."""
        return render_template("admin.html")
    
    @admin_bp.route("/suggestions")
    def admin_suggestions():
        """API endpoint to get all suggestions for admin review."""
        try:
            suggestions = data_service.load_suggestions()
            
            # Add additional info for each suggestion
            for suggestion in suggestions:
                # Check if already followed
                suggestion["already_followed"] = data_service.is_artist_followed(
                    suggestion.get("artist_name", ""),
                    suggestion.get("spotify_id")
                )
            
            return jsonify({"suggestions": suggestions})
        
        except Exception as e:
            logger.error(f"Error loading suggestions: {e}")
            return jsonify({"error": str(e), "suggestions": []})
    
    @admin_bp.route("/approve_suggestion", methods=["POST"])
    def admin_approve_suggestion():
        """Admin endpoint to approve a suggestion."""
        try:
            data = request.get_json()
            suggestion_id = data.get("suggestion_id")  # Using timestamp as ID
            action = data.get("action")  # "approve_follow", "approve_track", "reject"
            
            suggestions = data_service.load_suggestions()
            
            # Find the suggestion to update
            suggestion_found = False
            for suggestion in suggestions:
                if suggestion.get("timestamp") == suggestion_id:
                    suggestion_found = True
                    
                    if action == "approve_follow":
                        suggestion["status"] = "approved_for_follow"
                        suggestion["admin_approved"] = True
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                    elif action == "approve_track":
                        suggestion["status"] = "approved_for_tracking"
                        suggestion["admin_approved"] = True
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                    elif action == "reject":
                        suggestion["status"] = "rejected"
                        suggestion["admin_approved"] = False
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                    
                    break
            
            if not suggestion_found:
                return jsonify({"success": False, "message": "Suggestion not found"})
            
            # Save updated suggestions
            if data_service.save_suggestions(suggestions):
                return jsonify({
                    "success": True, 
                    "message": f"Suggestion {action.replace('_', ' ')}d successfully"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save changes"})
        
        except Exception as e:
            logger.error(f"Error approving suggestion: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/follow_artist", methods=["POST"])
    def admin_follow_artist():
        """Admin endpoint to immediately follow an artist on Spotify."""
        try:
            data = request.get_json()
            artist_id = data.get("artist_id")
            artist_name = data.get("artist_name", "Unknown Artist")
            
            if not artist_id:
                return jsonify({"success": False, "message": "Artist ID is required"})
            
            # Check if authenticated
            if not spotify_service.get_token_from_session():
                return jsonify({
                    "success": False,
                    "message": "Spotify authentication required. Please log in with Spotify to follow artists.",
                    "auth_required": True
                })
            
            # Get current user info for logging
            user = spotify_service.get_current_user()
            if user:
                logger.info(f"Following artist as user: {user.get('display_name', user.get('id'))}")
            
            # Follow the artist
            success, error_message = spotify_service.follow_artist(artist_id)
            
            if not success:
                if "Authentication" in error_message:
                    return jsonify({
                        "success": False,
                        "message": error_message,
                        "auth_required": True
                    })
                else:
                    return jsonify({"success": False, "message": error_message})
            
            # Add to followed artists file
            followed_artists = data_service.load_followed_artists()
            
            # Check if already in list
            already_exists = any(
                followed.get("artist_id") == artist_id 
                for followed in followed_artists
            )
            
            if not already_exists:
                new_artist = {
                    "artist_name": artist_name,
                    "artist_id": artist_id,
                    "url": f"https://open.spotify.com/artist/{artist_id}",
                    "source": "admin_follow",
                    "date_added": datetime.now().strftime("%Y-%m-%d"),
                    "removed": False
                }
                followed_artists.append(new_artist)
                
                if data_service.save_followed_artists(followed_artists):
                    logger.info(f"Added {artist_name} to followed artists file")
                else:
                    logger.error(f"Failed to update followed artists file for {artist_name}")
            
            return jsonify({
                "success": True, 
                "message": f"Successfully followed {artist_name} on Spotify and added to tracking list!"
            })
        
        except Exception as e:
            logger.error(f"Error following artist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/run_scraping", methods=["POST"])
    def admin_run_scraping():
        """Admin endpoint to run the scraping script."""
        try:
            data = request.get_json()
            headless = data.get("headless", True)
            today_only = data.get("today_only", False)
            
            # Create and start scraping job
            job_id = job_service.create_scraping_job(headless=headless, today_only=today_only)
            
            if job_service.start_scraping_job(job_id):
                scraping_type = "filtered (today's artists only)" if today_only else "full"
                return jsonify({
                    "success": True,
                    "message": f"Scraping started successfully ({scraping_type})",
                    "job_id": job_id
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Failed to start scraping job"
                })
        
        except Exception as e:
            logger.error(f"Error starting scraping: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/scraping_status/<job_id>")
    def admin_scraping_status(job_id):
        """Get the status of a scraping job."""
        try:
            job_data = job_service.get_job_status(job_id)
            
            if job_data:
                return jsonify({
                    "success": True,
                    "job": job_data
                })
            else:
                return jsonify({"success": False, "message": "Job not found"})
        
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/scraping_jobs")
    def admin_scraping_jobs():
        """Get all scraping jobs."""
        try:
            jobs = job_service.get_all_jobs()
            return jsonify({
                "success": True,
                "jobs": jobs
            })
        
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/process_suggestions", methods=["POST"])
    def admin_process_suggestions():
        """Admin endpoint to process approved suggestions."""
        try:
            result = job_service.run_process_suggestions()
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error processing suggestions: {e}")
            return jsonify({
                "success": False,
                "message": f"Error: {str(e)}"
            })
    
    return admin_bp
