"""
Main public routes for the Spotify Listener Tracker app.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_main_routes(spotify_service, data_service, job_service=None):
    """Create main routes blueprint with injected services."""
    
    main_bp = Blueprint('main', __name__)
    
    @main_bp.route("/")
    def home():
        """Home page - redirects to leaderboard."""
        return redirect(url_for('main.leaderboard'))
    
    @main_bp.route("/home")
    def home_page():
        """Redirect /home to the leaderboard."""
        return redirect(url_for('main.leaderboard'))
    
    @main_bp.route("/search", methods=["GET"])
    def search():
        """Search for artists."""
        query = request.args.get("artist", "").strip()
        
        if not query:
            return render_template(
                "search.html",
                results=[],
                results_for_chart=[],
                query="",
                total_change=None,
                artist_info=None,
                artist_image_url=None,
                grow_results=False
            )
        
        try:
            # Search in local data
            results = data_service.search_artists(query)
            
            # Check for exact match and redirect
            query_lower = query.lower()
            for result in results:
                if query_lower == result.get("artist_name", "").lower():
                    artist_id = result.get("artist_id")
                    if artist_id:
                        slug = data_service.slugify(result.get("artist_name", "artist"))
                        return redirect(url_for("main.artist_detail", 
                                               artist_name_slug=slug, 
                                               artist_id=artist_id))
            
            # Add image URLs for results
            for result in results:
                if result.get("artist_id"):
                    result["image_url"] = spotify_service.fetch_artist_image(result["artist_id"])
                else:
                    result["image_url"] = None
            
            # Parse dates for template (like artist_detail)
            def parse_date(val):
                if isinstance(val, datetime):
                    return val
                if isinstance(val, str):
                    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            return datetime.strptime(val, fmt)
                        except Exception:
                            continue
                return val
            for row in results:
                row["date"] = parse_date(row.get("date"))
            
            results_for_chart = list(reversed(results))
            
            # Get artist info for the first result
            artist_info = None
            artist_image_url = None
            
            if results:
                first_result = results[0]
                artist_id = first_result.get("artist_id")
                
                if artist_id:
                    artist_info = spotify_service.get_artist_info(artist_id)
                    artist_image_url = spotify_service.fetch_artist_image(artist_id)
            
            # Calculate total change
            total_change = None
            if results and len(results) > 1:
                total_change = results[-1]['monthly_listeners'] - results[0]['monthly_listeners']
            
            return render_template(
                "search.html",
                results=results,
                results_for_chart=results_for_chart,
                query=query,
                total_change=total_change,
                artist_info=artist_info,
                artist_image_url=artist_image_url,
                grow_results=True if results else False
            )
        
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return render_template(
                "search.html",
                results=[],
                results_for_chart=[],
                query=query,
                total_change=None,
                artist_info=None,
                artist_image_url=None,
                grow_results=False,
                error="An error occurred while searching."
            )
    
    @main_bp.route("/suggest", methods=["GET"])
    def suggest():
        """Auto-suggest artist names."""
        term = request.args.get("term", "").strip().lower()
        
        if not term:
            return jsonify([])
        
        try:
            data = data_service.load_data()
            suggestions = []
            seen = set()
            
            for entry in data:
                name = entry.get("artist_name", "")
                if term in name.lower() and name not in seen:
                    suggestions.append(name)
                    seen.add(name)
            
            suggestions.sort()
            return jsonify(suggestions)
        
        except Exception as e:
            logger.error(f"Error in suggest: {e}")
            return jsonify([])
    
    @main_bp.route("/leaderboard")
    def leaderboard():
        """Display artist leaderboard."""
        mode = request.args.get('mode', 'growth')
        tier = request.args.get('tier', 'all')
        
        try:
            leaderboard_data = data_service.get_leaderboard_data(mode=mode, tier=tier)
            
            # Add image URLs for leaderboard entries
            for entry in leaderboard_data['leaderboard']:
                if entry.get("artist_id"):
                    entry["image_url"] = spotify_service.fetch_artist_image(entry["artist_id"])
                else:
                    entry["image_url"] = None
            
            return render_template(
                "leaderboard.html",
                leaderboard=leaderboard_data['leaderboard'],
                leaderboard_mode=leaderboard_data['mode'],
                leaderboard_tier=leaderboard_data['tier'],
                start_date=leaderboard_data['start_date'],
                end_date=leaderboard_data['end_date']
            )
        
        except Exception as e:
            logger.error(f"Error in leaderboard: {e}")
            return render_template(
                "leaderboard.html",
                leaderboard=[],
                leaderboard_mode=mode,
                leaderboard_tier=tier,
                start_date=None,
                end_date=None,
                error="An error occurred while loading the leaderboard."
            )
    
    @main_bp.route("/artist/<artist_id>")
    def artist_detail_redirect(artist_id):
        """Redirect to artist detail with slug."""
        try:
            data = data_service.load_data()
            for entry in data:
                if entry.get("artist_id") == artist_id:
                    artist_name = entry.get("artist_name", "artist")
                    slug = data_service.slugify(artist_name)
                    return redirect(url_for('main.artist_detail', 
                                           artist_name_slug=slug, 
                                           artist_id=artist_id))
            
            return redirect(url_for('main.home'))
        
        except Exception as e:
            logger.error(f"Error in artist redirect: {e}")
            return redirect(url_for('main.home'))
    
    @main_bp.route("/artist/<artist_name_slug>/<artist_id>")
    def artist_detail(artist_name_slug, artist_id):
        """Display artist detail page."""
        try:
            # Get artist history
            results = data_service.get_artist_history(artist_id)
            results.sort(key=lambda x: x.get("date", ""), reverse=False)  # oldest first
            
            # Parse dates for template
            def parse_date(val):
                if isinstance(val, datetime):
                    return val
                if isinstance(val, str):
                    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            return datetime.strptime(val, fmt)
                        except Exception:
                            continue
                return val
            
            for row in results:
                row["date"] = parse_date(row.get("date"))
            
            # Get artist info and image
            artist_info = spotify_service.get_artist_info(artist_id)
            artist_image_url = spotify_service.fetch_artist_image(artist_id)
            
            # Calculate all-time high
            all_time_high = None
            if results:
                max_entry = max(results, key=lambda x: x.get("monthly_listeners", 0))
                all_time_high = {
                    "value": max_entry.get("monthly_listeners", 0),
                    "date": parse_date(max_entry.get("date", ""))
                }
            
            # Prepare chart labels as formatted month and day strings (e.g., 'Jun 30'), skip invalid, and reverse to match chartData
            chart_labels = [
                row['date'].strftime('%b %d')
                for row in results
                if isinstance(row['date'], datetime)
            ][::-1]
            return render_template(
                "artist.html",
                results=results,
                artist_info=artist_info,
                artist_image_url=artist_image_url,
                all_time_high=all_time_high,
                artist_id=artist_id,
                chart_labels=chart_labels
            )
        
        except Exception as e:
            logger.error(f"Error in artist detail: {e}")
            return render_template(
                "artist.html",
                results=[],
                artist_info=None,
                artist_image_url=None,
                all_time_high=None,
                artist_id=artist_id,
                error="An error occurred while loading artist details."
            )
    
    @main_bp.route("/search_spotify_artists")
    def search_spotify_artists():
        """Search for artists on Spotify API for autocomplete."""
        query = request.args.get("q", "").strip()
        
        if not query or len(query) < 2:
            return jsonify({"artists": []})
        
        try:
            artists = spotify_service.search_artists(query)
            return jsonify({"artists": artists})
        
        except Exception as e:
            logger.error(f"Error searching Spotify artists: {e}")
            return jsonify({"artists": []})
    
    @main_bp.route("/top_tracks/<artist_id>")
    def top_tracks(artist_id):
        """Get top tracks for an artist."""
        try:
            tracks = spotify_service.get_top_tracks(artist_id)
            return jsonify(tracks)
        except Exception as e:
            logger.error(f"Error getting top tracks for {artist_id}: {e}")
            return jsonify([])
    
    @main_bp.route("/artist_info/<artist_id>")
    def artist_info_api(artist_id):
        """Get artist information via API."""
        try:
            info = spotify_service.get_artist_info(artist_id)
            return jsonify(info)
        except Exception as e:
            logger.error(f"Error getting artist info for {artist_id}: {e}")
            return jsonify({})
    
    @main_bp.route("/artist_image")
    def artist_image():
        """Get artist image by name search."""
        name = request.args.get("name")
        
        if not name:
            return jsonify({"image": "https://via.placeholder.com/64?text=No+Image"})
        
        try:
            # Search for artist and get image
            artists = spotify_service.search_artists(name, limit=1)
            if artists and artists[0].get("image"):
                return jsonify({"image": artists[0]["image"]})
            
            return jsonify({"image": "https://via.placeholder.com/64?text=No+Image"})
        
        except Exception as e:
            logger.error(f"Error getting artist image for {name}: {e}")
            return jsonify({"image": "https://via.placeholder.com/64?text=No+Image"})
    
    @main_bp.route('/artist_image/<artist_id>')
    def artist_image_redirect(artist_id):
        """Redirect to artist image URL."""
        try:
            image_url = spotify_service.fetch_artist_image(artist_id)
            if image_url:
                return redirect(image_url)
            else:
                return redirect(url_for('static', filename='placeholder.png'))
        except Exception as e:
            logger.error(f"Error redirecting to artist image for {artist_id}: {e}")
            return redirect(url_for('static', filename='placeholder.png'))
    
    @main_bp.route("/suggest_artist", methods=["POST"])
    def suggest_artist():
        """Submit an artist suggestion."""
        try:
            data = request.get_json()
            artist_name = data.get("artist_name", "").strip()
            spotify_url = data.get("spotify_url", "").strip()
            spotify_id = data.get("spotify_id", "").strip()

            if not artist_name:
                return jsonify({"success": False, "message": "Artist name is required"})

            # Check blacklist
            blacklisted_artists, blacklisted_ids = data_service.load_blacklist()

            if (artist_name.lower() in blacklisted_artists or 
                (spotify_id and spotify_id in blacklisted_ids)):
                return jsonify({"success": False, "message": "We do not support predators"})

            # Check if already suggested
            if data_service.is_artist_suggested(artist_name, spotify_id):
                return jsonify({
                    "success": False, 
                    "message": f"{artist_name} has already been suggested and is waiting to be added!"
                })

            # Check if already followed
            if data_service.is_artist_followed(artist_name, spotify_id):
                return jsonify({
                    "success": False, 
                    "message": f"You're already following {artist_name} on Spotify!"
                })

            # Add new suggestion
            suggestions = data_service.load_suggestions()
            now_str = datetime.now().isoformat()
            new_suggestion = {
                "artist_name": artist_name,
                "spotify_url": spotify_url if spotify_url else None,
                "spotify_id": spotify_id if spotify_id else None,
                "timestamp": now_str,
                # Force status to approved_for_follow for immediate processing
                "status": "approved_for_follow",
                "admin_approved": True,
                "admin_action_date": now_str
            }

            suggestions.append(new_suggestion)

            logger.info(f"[DEBUG] About to call save_suggestions for artist: {artist_name} (ID: {spotify_id})")
            save_result = data_service.save_suggestions(suggestions)
            logger.info(f"[DEBUG] save_suggestions returned: {save_result} for artist: {artist_name} (ID: {spotify_id})")

            if save_result:
                # Immediately process the suggestion and mark as processed
                logger.info(f"[AUTO-PROCESS] About to run process_suggestions after saving suggestion for artist: {artist_name} (ID: {spotify_id})")
                try:
                    import sys
                    import importlib.util
                    import os
                    import_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../scraping/process_suggestions.py'))
                    spec = importlib.util.spec_from_file_location("process_suggestions_module", import_path)
                    process_mod = importlib.util.module_from_spec(spec)
                    sys.modules["process_suggestions_module"] = process_mod
                    spec.loader.exec_module(process_mod)
                    process_mod.process_suggestions()
                    logger.info(f"[AUTO-PROCESS] process_suggestions completed successfully for artist: {artist_name} (ID: {spotify_id})")
                except Exception as e:
                    logger.error(f"[AUTO-PROCESS] Error running process_suggestions after suggestion for artist: {artist_name} (ID: {spotify_id}): {e}")
                    return jsonify({
                        "success": False,
                        "message": f"Suggestion saved but failed to process: {e}"
                    })
                return jsonify({
                    "success": True,
                    "message": "Artist suggestion processed and added!"
                })
            else:
                logger.error(f"[ERROR] save_suggestions failed for artist: {artist_name} (ID: {spotify_id})")
                return jsonify({
                    "success": False,
                    "message": "Failed to save suggestion"
                })

        except Exception as e:
            logger.error(f"Error handling artist suggestion: {e}")
            return jsonify({"success": False, "message": "Server error occurred"})
    
    @main_bp.route("/refresh_data")
    def refresh_data():
        """Refresh data cache manually."""
        try:
            # Clear cache and reload data
            data_service.clear_cache()
            data = data_service.load_data(use_cache=False)
            return jsonify({
                "success": True, 
                "message": f"Data refreshed successfully. Loaded {len(data)} records.",
                "records": len(data)
            })
        except Exception as e:
            logger.error(f"Error refreshing data: {e}")
            return jsonify({"success": False, "error": str(e)})
    
    @main_bp.route("/follow_artist", methods=["POST"])
    def follow_artist():
        """Public endpoint to follow an artist on Spotify."""
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
                    "auth_required": True,
                    "auth_url": spotify_service.get_auth_url()
                })
            
            # Follow the artist
            success, error_message = spotify_service.follow_artist(artist_id)
            
            if not success:
                if "Authentication" in error_message:
                    return jsonify({
                        "success": False,
                        "message": error_message,
                        "auth_required": True,
                        "auth_url": spotify_service.get_auth_url()
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
                    "source": "public_follow",
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
                "message": f"Successfully followed {artist_name} on Spotify!"
            })
        
        except Exception as e:
            logger.error(f"Error following artist: {e}")
            return jsonify({"success": False, "message": f"Error: {str(e)}"})

    return main_bp
