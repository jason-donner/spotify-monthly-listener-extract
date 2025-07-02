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

def create_admin_routes(spotify_service, data_service, job_service):

    admin_bp = Blueprint('admin', __name__)
    def require_admin_auth():
        return session.get('admin_authenticated') == True
    def admin_login_required(f):
        def decorated_function(*args, **kwargs):
            if not require_admin_auth():
                return redirect(url_for('admin.admin_login_page'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    @admin_bp.route("/search_artist", methods=["GET"])
    def admin_search_artist():
        """Search Spotify for artists by name and return a list of matches."""
        try:
            query = request.args.get("q", "").strip()
            if not query:
                return jsonify({"success": False, "results": [], "message": "No search query provided."}), 200
            results = spotify_service.search_artists(query)
            # Always return a JSON response, even if no results
            if not results:
                return jsonify({"success": False, "results": [], "message": "No artists found for this query."}), 200
            return jsonify({"success": True, "results": results}), 200
        except Exception as e:
            logger.error(f"Error searching artists: {e}")
            return jsonify({"success": False, "results": [], "message": f"Error: {str(e)}"}), 200

    @admin_bp.route("/artist_top_tracks", methods=["GET"])
    @admin_login_required
    def admin_artist_top_tracks():
        """Get top tracks for a given artist ID from Spotify."""
        try:
            artist_id = request.args.get("artist_id", "").strip()
            if not artist_id:
                return jsonify({"success": False, "message": "No artist ID provided."}), 400
            tracks = spotify_service.get_artist_top_tracks(artist_id)
            # Expecting a list of dicts with name, url, preview_url, album, etc.
            return jsonify({"success": True, "tracks": tracks})
        except Exception as e:
            logger.error(f"Error getting top tracks: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

    @admin_bp.route("/process_artist_list", methods=["GET"])
    @admin_login_required
    def admin_process_artist_list():
        """Return a list of followed but not processed artists."""
        followed_artists = data_service.load_followed_artists()
        suggestions = data_service.load_suggestions()
        # Build a set of processed artist IDs from suggestions
        processed_ids = set()
        for s in suggestions:
            if s.get('status') == 'processed' and s.get('spotify_id'):
                processed_ids.add(s['spotify_id'])
        # Filter followed artists that are not processed
        unprocessed = [a for a in followed_artists if a.get('artist_id') and a['artist_id'] not in processed_ids]
        return jsonify({"success": True, "unprocessed_artists": unprocessed})
        except Exception as e:
            logger.error(f"Error in process_artist endpoint: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})
    # (Removed duplicate blueprint and decorator definitions)
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
    

    @admin_bp.route("/add_artist", methods=["POST"])
    @admin_login_required
    def admin_add_artist():
        """Admin endpoint to directly add (follow) an artist by Spotify ID or URL."""
        try:
            data = request.get_json()
            artist_id = data.get("artist_id")
            artist_name = data.get("artist_name", "Unknown Artist")

            # If only artist_name is provided, search Spotify for the artist
            if (not artist_id or artist_id.strip() == "") and artist_name and artist_name.strip() != "":
                try:
                    search_result = spotify_service.search_artist(artist_name)
                    if search_result and search_result.get("id"):
                        artist_id = search_result["id"]
                        artist_name = search_result["name"]
                        logger.info(f"Spotify search found artist: {artist_name} ({artist_id})")
                    else:
                        logger.error(f"No artist found for name: {artist_name}")
                        return jsonify({"success": False, "message": f"No artist found for name: {artist_name}"})
                except Exception as e:
                    logger.error(f"Spotify search error: {e}")
                    return jsonify({"success": False, "message": f"Spotify search error: {e}"})

            # If artist_id is a Spotify URL, extract the ID
            if artist_id and "spotify.com" in artist_id:
                import re
                match = re.search(r"artist/([a-zA-Z0-9]+)", artist_id)
                if match:
                    artist_id = match.group(1)
                else:
                    logger.error("Invalid Spotify artist URL provided")
                    return jsonify({"success": False, "message": "Invalid Spotify artist URL provided"})
            client_ip = get_client_ip()
            logger.info(f"ADD_ARTIST REQUEST: artist_id={artist_id}, artist_name={artist_name}")
            admin_security_logger.info(f"Admin initiated add for artist '{artist_name}' (ID: {artist_id}) from IP: {client_ip}")

            if not artist_id:
                logger.error("ADD_ARTIST ERROR: No artist ID provided")
                return jsonify({"success": False, "message": "Artist ID is required"})

            # Check if authenticated
            if not spotify_service.get_token_from_session():
                logger.warning("ADD_ARTIST ERROR: Not authenticated")
                admin_security_logger.warning(f"Admin add attempt without Spotify auth from IP: {client_ip}")
                return jsonify({
                    "success": False,
                    "message": "Spotify authentication required. Please log in with Spotify to follow artists.",
                    "auth_required": True
                })

            # Get current user info for logging
            user = spotify_service.get_current_user()
            if user:
                logger.info(f"Adding artist as user: {user.get('display_name', user.get('id'))}")

            # Follow the artist
            success, error_message = spotify_service.follow_artist(artist_id)
            logger.info(f"ADD_ARTIST RESULT: success={success}, error_message={error_message}")

            already_following = not success and ("already" in error_message.lower() or "following" in error_message.lower())

            if not success and not already_following:
                logger.error(f"ADD_ARTIST FAILED: {error_message}")
                if "Authentication" in error_message:
                    return jsonify({
                        "success": False,
                        "message": error_message,
                        "auth_required": True
                    })
                else:
                    return jsonify({"success": False, "message": error_message})

            follow_status_msg = "already followed" if already_following else "added and followed"
            return jsonify({
                "success": True,
                "message": f"Artist {artist_name} ({artist_id}) {follow_status_msg}.",
                "warning": already_following
            })
        except Exception as e:
            logger.error(f"Error adding artist: {e}")
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
    
    # Scheduler endpoints removed (scheduler_service is deprecated)
    # Cleaned up: No scheduler code remains. If you see this comment, all scheduler code is removed.
    
    return admin_bp
