"""
Admin routes for the Spotify Listener Tracker app.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from datetime import datetime
import logging
import hashlib
import os

logger = logging.getLogger(__name__)
admin_security_logger = logging.getLogger('admin_security')

# Admin password from .env file (required)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not ADMIN_PASSWORD:
    logger.warning("ADMIN_PASSWORD not found in .env file! Admin login will not work.")

def get_client_ip():
    """Get client IP address for logging"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

def create_admin_routes(spotify_service, data_service, job_service, scheduler_service):
    """Create admin routes blueprint with injected services."""
    
    admin_bp = Blueprint('admin', __name__)
    
    def require_admin_auth():
        """Check if user is authenticated as admin"""
        return session.get('admin_authenticated') == True
    
    def admin_login_required(f):
        """Decorator to require admin authentication"""
        def decorated_function(*args, **kwargs):
            if not require_admin_auth():
                return redirect(url_for('admin.admin_login_page'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    
    @admin_bp.route("/admin_login")
    def admin_login_page():
        """Admin login page"""
        client_ip = get_client_ip()
        admin_security_logger.info(f"Admin login page accessed from IP: {client_ip}")
        return render_template("admin_login.html")
    
    @admin_bp.route("/admin_auth", methods=["POST"])
    def admin_authenticate():
        """Handle admin password submission"""
        client_ip = get_client_ip()
        password = request.form.get('password')
        
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            session.permanent = True  # Keep session active
            admin_security_logger.info(f"SUCCESSFUL admin login from IP: {client_ip}")
            logger.info(f"Admin authenticated successfully from {client_ip}")
            return redirect(url_for('admin.admin'))
        else:
            admin_security_logger.warning(f"FAILED admin login attempt from IP: {client_ip} - Invalid password")
            logger.warning(f"Failed admin login attempt from {client_ip}")
            return render_template("admin_login.html", error="Invalid password")
    
    @admin_bp.route("/logout")
    def admin_logout():
        """Admin logout"""
        client_ip = get_client_ip()
        if session.get('admin_authenticated'):
            admin_security_logger.info(f"Admin logout from IP: {client_ip}")
            logger.info(f"Admin logged out from {client_ip}")
        session.pop('admin_authenticated', None)
        return redirect(url_for('admin.admin_login_page'))
        """Logout from admin and redirect immediately to home page"""
        session.clear()  # Clear entire session
        return redirect('/')  # Direct redirect to home, no intermediate page
    
    @admin_bp.route("/debug_session")
    def debug_session():
        """Debug route to check session status"""
        return jsonify({
            "session_contents": dict(session),
            "admin_authenticated": session.get('admin_authenticated'),
            "require_admin_auth": require_admin_auth()
        })
    
    @admin_bp.route("/check_admin_auth")
    def check_admin_auth():
        """API endpoint to check if user is admin authenticated"""
        return jsonify({"admin_authenticated": require_admin_auth()})
    
    @admin_bp.route("/")
    @admin_login_required
    def admin():
        """Admin page to review and manage artist suggestions."""
        client_ip = get_client_ip()
        admin_security_logger.info(f"Admin panel accessed from IP: {client_ip}")
        
        # Check for force logout parameter
        if request.args.get('force_logout') == 'true':
            session.clear()
            response = redirect(url_for('admin.admin_login_page'))
            response.set_cookie(current_app.session_cookie_name, '', expires=0)
            admin_security_logger.info(f"Forced logout executed from IP: {client_ip}")
            return response
        return render_template("admin.html")
    
    @admin_bp.route("/login")
    @admin_login_required
    def login():
        """Initiate Spotify OAuth login"""
        # Check if force login is requested
        force = request.args.get('force', 'false').lower() == 'true'
        
        try:
            auth_url = spotify_service.get_auth_url(force_login=force)
            return redirect(auth_url)
        except Exception as e:
            logger.error(f"Login error: {e}")
            return redirect(url_for('admin.admin') + '?error=auth_failed')
    
    @admin_bp.route("/callback")
    def callback():
        """Handle Spotify OAuth callback"""
        code = request.args.get('code')
        if not code:
            return redirect(url_for('admin.admin') + '?error=auth_cancelled')
        
        try:
            success = spotify_service.handle_oauth_callback(code)
            if success:
                return redirect(url_for('admin.admin') + '?success=logged_in')
            else:
                return redirect(url_for('admin.admin') + '?error=auth_failed')
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return redirect(url_for('admin.admin') + '?error=auth_failed')
    
    @admin_bp.route("/spotify_logout")
    def spotify_logout():
        """Clear Spotify authentication only"""
        spotify_service.logout()
        return redirect(url_for('admin.admin') + '?success=logged_out')
    
    @admin_bp.route("/auth_status")
    def auth_status():
        """Check if user is authenticated with Spotify"""
        try:
            auth_info = spotify_service.get_auth_status()
            return jsonify(auth_info)
        except Exception as e:
            logger.error(f"Auth status error: {e}")
            return jsonify({"authenticated": False})
    
    @admin_bp.route("/suggestions")
    @admin_login_required
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
            
            client_ip = get_client_ip()
            suggestions = data_service.load_suggestions()
            
            # Find the suggestion to update
            suggestion_found = False
            for suggestion in suggestions:
                if suggestion.get("timestamp") == suggestion_id:
                    suggestion_found = True
                    artist_name = suggestion.get("artist_name", "Unknown")
                    
                    if action == "approve_follow":
                        suggestion["status"] = "approved_for_follow"
                        suggestion["admin_approved"] = True
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                        admin_security_logger.info(f"Admin approved artist '{artist_name}' for follow from IP: {client_ip}")
                    elif action == "approve_track":
                        suggestion["status"] = "approved_for_tracking"
                        suggestion["admin_approved"] = True
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                        admin_security_logger.info(f"Admin approved artist '{artist_name}' for tracking only from IP: {client_ip}")
                    elif action == "process_track_only":
                        # Immediately process for tracking (skip the "approved" intermediate state)
                        suggestion["status"] = "processed"
                        suggestion["admin_approved"] = True
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                        suggestion["processed_date"] = datetime.now().isoformat()
                        
                        # Add to followed artists file
                        artist_id = suggestion.get("spotify_id")
                        if artist_id:
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
                                    "source": "admin_track_only",
                                    "date_added": datetime.now().strftime("%Y-%m-%d"),
                                    "removed": False
                                }
                                followed_artists.append(new_artist)
                                data_service.save_followed_artists(followed_artists)
                                logger.info(f"Added {artist_name} to followed artists file (track only)")
                        
                        admin_security_logger.info(f"Admin processed artist '{artist_name}' for tracking only (immediate) from IP: {client_ip}")
                    elif action == "reject":
                        suggestion["status"] = "rejected"
                        suggestion["admin_approved"] = False
                        suggestion["admin_action_date"] = datetime.now().isoformat()
                        admin_security_logger.info(f"Admin rejected artist '{artist_name}' from IP: {client_ip}")
                    
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
    @admin_login_required
    def admin_follow_artist():
        """Admin endpoint to immediately follow an artist on Spotify and process suggestion if provided."""
        try:
            data = request.get_json()
            artist_id = data.get("artist_id")
            artist_name = data.get("artist_name", "Unknown Artist")
            suggestion_id = data.get("suggestion_id")  # Optional - for processing suggestions
            
            client_ip = get_client_ip()
            logger.info(f"FOLLOW_ARTIST REQUEST: artist_id={artist_id}, artist_name={artist_name}, suggestion_id={suggestion_id}")
            admin_security_logger.info(f"Admin initiated follow for artist '{artist_name}' (ID: {artist_id}) from IP: {client_ip}")
            
            if not artist_id:
                logger.error("FOLLOW_ARTIST ERROR: No artist ID provided")
                return jsonify({"success": False, "message": "Artist ID is required"})

            # Check if authenticated
            if not spotify_service.get_token_from_session():
                logger.warning("FOLLOW_ARTIST ERROR: Not authenticated")
                admin_security_logger.warning(f"Admin follow attempt without Spotify auth from IP: {client_ip}")
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
            logger.info(f"FOLLOW_ARTIST RESULT: success={success}, error_message={error_message}")

            # Check if the failure is due to already following (which is OK for our purposes)
            already_following = not success and ("already" in error_message.lower() or "following" in error_message.lower())
            
            if not success and not already_following:
                logger.error(f"FOLLOW_ARTIST FAILED: {error_message}")
                if "Authentication" in error_message:
                    return jsonify({
                        "success": False,
                        "message": error_message,
                        "auth_required": True
                    })
                else:
                    return jsonify({"success": False, "message": error_message})
            
            # Determine success message based on whether we followed or already following
            if already_following:
                logger.info(f"Artist {artist_name} already followed, proceeding with suggestion processing")
                follow_status_msg = "already followed"
            else:
                follow_status_msg = "successfully followed"

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
            
            # If this was from a suggestion, mark it as processed
            success_message = f"Artist {artist_name} {follow_status_msg} and added to tracking list!"
            if suggestion_id:
                try:
                    # Load suggestions
                    suggestions = data_service.load_suggestions()
                    logger.info(f"Attempting to process suggestion with ID: {suggestion_id}")
                    logger.info(f"Available suggestion timestamps: {[s.get('timestamp') for s in suggestions]}")
                    
                    # Find and update the suggestion
                    suggestion_found = False
                    for suggestion in suggestions:
                        current_timestamp = suggestion.get('timestamp')
                        logger.debug(f"Checking suggestion with timestamp: {current_timestamp} (type: {type(current_timestamp)})")
                        logger.debug(f"Looking for timestamp: {suggestion_id} (type: {type(suggestion_id)})")
                        logger.debug(f"Timestamps match: {current_timestamp == suggestion_id}")
                        
                        if current_timestamp == suggestion_id:
                            suggestion['status'] = 'processed'
                            suggestion['admin_approved'] = True
                            suggestion['admin_action_date'] = datetime.now().isoformat()
                            suggestion['processed_date'] = datetime.now().isoformat()
                            suggestion_found = True
                            logger.info(f"Marked suggestion {suggestion_id} as processed for artist {artist_name}")
                            break
                    
                    if suggestion_found:
                        if data_service.save_suggestions(suggestions):
                            success_message = f"Artist {artist_name} {follow_status_msg}, added to tracking, and suggestion marked as processed!"
                            logger.info(f"Suggestion {suggestion_id} successfully saved as processed")
                        else:
                            logger.error(f"Failed to save processed suggestion {suggestion_id}")
                    else:
                        logger.warning(f"Suggestion {suggestion_id} not found when trying to mark as processed.")
                        logger.warning(f"Available suggestion timestamps: {[s.get('timestamp') for s in suggestions]}")
                        
                except Exception as e:
                    logger.error(f"Error processing suggestion {suggestion_id}: {e}")
                    # Don't fail the whole operation if suggestion processing fails
            
            return jsonify({
                "success": True, 
                "message": success_message,
                "warning": already_following  # Flag to indicate this should be shown as warning
            })
        
        except Exception as e:
            logger.error(f"Error following artist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/run_scraping", methods=["POST"])
    @admin_login_required
    def admin_run_scraping():
        """Admin endpoint to run the scraping script."""
        try:
            data = request.get_json()
            headless = data.get("headless", True)
            today_only = data.get("today_only", False)
            allow_duplicates = data.get("allow_duplicates", False)
            
            # Create and start scraping job
            job_id = job_service.create_scraping_job(headless=headless, today_only=today_only, allow_duplicates=allow_duplicates)
            
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
    @admin_login_required
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
    @admin_login_required
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
    
    @admin_bp.route("/scheduler/status")
    def admin_scheduler_status():
        """Get scheduler status."""
        try:
            status = scheduler_service.get_status()
            return jsonify({"success": True, "status": status})
        
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/scheduler/set_time", methods=["POST"])
    def admin_set_schedule_time():
        """Set the daily scraping schedule time."""
        try:
            data = request.get_json()
            time_str = data.get("time")
            
            if not time_str:
                return jsonify({"success": False, "message": "Time is required"})
            
            scheduler_service.set_schedule_time(time_str)
            client_ip = get_client_ip()
            admin_security_logger.info(f"Admin updated daily scraping schedule to {time_str} from IP: {client_ip}")
            
            return jsonify({
                "success": True,
                "message": f"Daily scraping scheduled for {time_str}",
                "status": scheduler_service.get_status()
            })
        
        except ValueError as e:
            return jsonify({"success": False, "message": "Invalid time format. Use HH:MM (24-hour format)"})
        except Exception as e:
            logger.error(f"Error setting schedule time: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/scheduler/run_now", methods=["POST"])
    def admin_run_scheduled_scrape_now():
        """Trigger the scheduled scraping job immediately."""
        try:
            # Use the same logic as the scheduled job
            job_id = job_service.create_scraping_job(headless=True, today_only=False)
            
            if job_service.start_scraping_job(job_id):
                client_ip = get_client_ip()
                admin_security_logger.info(f"Admin triggered immediate full scraping from IP: {client_ip}")
                
                return jsonify({
                    "success": True,
                    "message": "Full scraping started immediately",
                    "job_id": job_id
                })
            else:
                return jsonify({"success": False, "message": "Failed to start scraping job"})
        
        except Exception as e:
            logger.error(f"Error running immediate scrape: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/blacklist")
    @admin_login_required
    def blacklist_management():
        """Blacklist management page."""
        try:
            blacklist_data = data_service.get_blacklist_data()
            return jsonify({
                "success": True,
                "blacklist": blacklist_data,
                "count": len(blacklist_data)
            })
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/blacklist/add", methods=["POST"])
    @admin_login_required
    def add_to_blacklist():
        """Add an artist to the blacklist."""
        try:
            data = request.get_json()
            artist_name = (data.get("artist_name") or "").strip()
            spotify_id = (data.get("spotify_id") or "").strip()
            reason = (data.get("reason") or "").strip()
            
            if not artist_name:
                return jsonify({"success": False, "message": "Artist name is required"})
            
            # Get current blacklist
            blacklist_data = data_service.get_blacklist_data()
            
            # Check if already blacklisted
            for item in blacklist_data:
                if (item["name"].lower() == artist_name.lower() or 
                    (spotify_id and item.get("spotify_id") == spotify_id)):
                    return jsonify({
                        "success": False, 
                        "message": f"{artist_name} is already blacklisted"
                    })
            
            # Add new blacklist entry
            new_entry = {
                "name": artist_name,
                "spotify_id": spotify_id if spotify_id else None,
                "reason": reason if reason else "Added by admin",
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            blacklist_data.append(new_entry)
            
            if data_service.save_blacklist(blacklist_data):
                admin_security_logger.info(
                    f"Admin added {artist_name} to blacklist from IP: {get_client_ip()}"
                )
                return jsonify({
                    "success": True, 
                    "message": f"{artist_name} added to blacklist successfully"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save blacklist"})
        
        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    
    @admin_bp.route("/blacklist/remove", methods=["POST"])
    @admin_login_required
    def remove_from_blacklist():
        """Remove an artist from the blacklist."""
        try:
            data = request.get_json()
            artist_name = (data.get("artist_name") or "").strip()
            
            if not artist_name:
                return jsonify({"success": False, "message": "Artist name is required"})
            
            # Get current blacklist
            blacklist_data = data_service.get_blacklist_data()
            
            # Find and remove the entry
            original_count = len(blacklist_data)
            blacklist_data = [
                item for item in blacklist_data 
                if item["name"].lower() != artist_name.lower()
            ]
            
            if len(blacklist_data) == original_count:
                return jsonify({
                    "success": False, 
                    "message": f"{artist_name} not found in blacklist"
                })
            
            if data_service.save_blacklist(blacklist_data):
                admin_security_logger.info(
                    f"Admin removed {artist_name} from blacklist from IP: {get_client_ip()}"
                )
                return jsonify({
                    "success": True, 
                    "message": f"{artist_name} removed from blacklist successfully"
                })
            else:
                return jsonify({"success": False, "message": "Failed to save blacklist"})
        
        except Exception as e:
            logger.error(f"Error removing from blacklist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    @admin_bp.route("/fix_stuck_suggestions", methods=["POST"])
    @admin_login_required
    def fix_stuck_suggestions():
        """Admin endpoint to fix suggestions stuck in limbo (approved but not followed)."""
        try:
            client_ip = get_client_ip()
            admin_security_logger.info(f"Admin initiated stuck suggestions fix from IP: {client_ip}")
            
            # Load suggestions
            suggestions = data_service.load_suggestions()
            followed_artists = data_service.load_followed_artists()
            
            # Find stuck suggestions (approved but not marked as followed)
            stuck_suggestions = []
            for suggestion in suggestions:
                if (suggestion.get("status") == "approved" and 
                    not suggestion.get("already_followed") and 
                    not suggestion.get("admin_action_date")):
                    stuck_suggestions.append(suggestion)
            
            if not stuck_suggestions:
                return jsonify({
                    "success": True,
                    "message": "No stuck suggestions found - all approved suggestions are properly processed!",
                    "fixed_count": 0
                })
            
            # Get existing followed artist IDs for duplicate checking
            existing_artist_ids = {artist.get("artist_id") for artist in followed_artists if artist.get("artist_id")}
            
            # Process each stuck suggestion
            fixed_count = 0
            added_to_followed = 0
            
            for suggestion in stuck_suggestions:
                artist_name = suggestion.get("artist_name", "Unknown")
                spotify_id = suggestion.get("spotify_id")
                spotify_url = suggestion.get("spotify_url")
                
                # Mark suggestion as properly processed
                suggestion["already_followed"] = True
                suggestion["admin_action_date"] = datetime.now().isoformat()
                fixed_count += 1
                
                # Add to followed artists if not already there
                if spotify_id and spotify_id not in existing_artist_ids:
                    new_artist = {
                        "artist_name": artist_name,
                        "artist_id": spotify_id,
                        "url": spotify_url if spotify_url else f"https://open.spotify.com/artist/{spotify_id}",
                        "source": "admin_fix",
                        "date_added": datetime.now().strftime("%Y-%m-%d"),
                        "removed": False
                    }
                    followed_artists.append(new_artist)
                    existing_artist_ids.add(spotify_id)
                    added_to_followed += 1
                    logger.info(f"Fixed stuck suggestion: {artist_name} - added to followed artists")
            
            # Save updated files
            if not data_service.save_suggestions(suggestions):
                return jsonify({
                    "success": False,
                    "message": "Failed to save updated suggestions"
                })
            
            if not data_service.save_followed_artists(followed_artists):
                return jsonify({
                    "success": False,
                    "message": "Failed to save updated followed artists"
                })
            
            logger.info(f"Fixed {fixed_count} stuck suggestions, added {added_to_followed} to followed list")
            admin_security_logger.info(f"Admin fixed {fixed_count} stuck suggestions from IP: {client_ip}")
            
            return jsonify({
                "success": True,
                "message": f"Fixed {fixed_count} stuck suggestion(s) and added {added_to_followed} artist(s) to followed list",
                "fixed_count": fixed_count,
                "added_count": added_to_followed
            })
            
        except Exception as e:
            logger.error(f"Error fixing stuck suggestions: {e}")
            return jsonify({
                "success": False,
                "message": f"Error fixing stuck suggestions: {str(e)}"
            })

    return admin_bp
