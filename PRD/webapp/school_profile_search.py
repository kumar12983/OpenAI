"""
School Profile Search API
Enhanced endpoint to return school profile details when searching by school ID
"""

# Add this to webapp/app.py in the appropriate location

from flask import Flask, jsonify, request
from flask_login import login_required
import psycopg2
from psycopg2.extras import RealDictCursor


def get_school_profile_info(school_id, db_config):
    """
    Get comprehensive school information from school_type_lookup table
    Returns both catchment and profile data
    
    Args:
        school_id: School ID from catchments table
        db_config: Database configuration dictionary
        
    Returns:
        Dictionary with school information or None if not found
    """
    conn = psycopg2.connect(**db_config)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query the school_type_lookup table for comprehensive data
        query = """
        SELECT 
            school_id,
            catchment_school_name,
            school_first,
            school_abbrev,
            school_type_name,
            acara_sml_id,
            profile_school_name,
            school_sector,
            school_type,
            icsea,
            icsea_percentile,
            suburb,
            state,
            postcode,
            school_url,
            governing_body,
            governing_body_url
        FROM gnaf.school_type_lookup
        WHERE school_id = %s
        LIMIT 1
        """
        
        cursor.execute(query, (school_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return dict(result) if result else None
        
    except Exception as e:
        print(f"Error in get_school_profile_info: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if conn:
            conn.close()


# API Endpoint for School Search with Profile Details
# Add this route to your Flask app in app.py

def setup_school_profile_routes(app, db_config):
    """
    Setup school profile search routes
    Call this in your app.py: setup_school_profile_routes(app, DB_CONFIG)
    """
    
    @app.route('/api/school/<int:school_id>', methods=['GET'])
    @login_required
    def lookup_school_by_id(school_id):
        """
        Look up school by school_id (quick lookup)
        
        Example: /api/school/1001
        
        Returns:
            JSON with comprehensive school information
        """
        try:
            school_data = get_school_profile_info(school_id, db_config)
            
            if not school_data:
                return jsonify({
                    'error': 'School not found',
                    'school_id': school_id
                }), 404
            
            # Format the response
            response = {
                'school_id': school_data['school_id'],
                'school_name': school_data['profile_school_name'] or school_data['catchment_school_name'],
                'school_name_short': school_data['school_first'],
                'school_sector': school_data['school_sector'],
                'school_type': school_data['school_type'],
                'school_type_name': school_data['school_type_name'],
                'icsea': school_data['icsea'],
                'icsea_percentile': school_data['icsea_percentile'],
                'location': {
                    'suburb': school_data['suburb'],
                    'state': school_data['state'],
                    'postcode': school_data['postcode']
                },
                'contact': {
                    'school_url': school_data['school_url'],
                    'governing_body': school_data['governing_body'],
                    'governing_body_url': school_data['governing_body_url']
                },
                'acara_sml_id': school_data['acara_sml_id']
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            print(f"Error in lookup_school_by_id for {school_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Database error',
                'message': str(e)
            }), 500

    
    @app.route('/api/school/<school_id>/profile', methods=['GET'])
    @login_required
    def get_school_profile(school_id):
        """
        Get school profile information including:
        - School Sector (Government, Non-Government)
        - School Type (PS, HS, GHS, etc. with full names)
        - ICSEA value and percentile
        - Suburb, State, Postcode
        - School URL
        - Governing body information
        
        Example: /api/school/1001/profile
        
        Returns:
            JSON with school profile data or 404 if not found
        """
        try:
            school_data = get_school_profile_info(school_id, db_config)
            
            if not school_data:
                return jsonify({
                    'error': 'School not found',
                    'school_id': school_id
                }), 404
            
            # Format the response
            response = {
                'school_id': school_data['school_id'],
                'school_name': school_data['profile_school_name'] or school_data['catchment_school_name'],
                'school_name_short': school_data['school_first'],
                'school_sector': school_data['school_sector'],
                'school_type': school_data['school_type'],
                'school_type_name': school_data['school_type_name'],
                'icsea': school_data['icsea'],
                'icsea_percentile': school_data['icsea_percentile'],
                'location': {
                    'suburb': school_data['suburb'],
                    'state': school_data['state'],
                    'postcode': school_data['postcode']
                },
                'contact': {
                    'school_url': school_data['school_url'],
                    'governing_body': school_data['governing_body'],
                    'governing_body_url': school_data['governing_body_url']
                },
                'acara_sml_id': school_data['acara_sml_id']
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            print(f"Error fetching school profile for {school_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Database error',
                'message': str(e)
            }), 500


    @app.route('/api/school/search-by-name', methods=['GET'])
    @login_required
    def search_school_by_name():
        """
        Search schools by name with profile information
        
        Query parameters:
            - q: Search query (school name)
            - state: Filter by state (optional)
            - limit: Max results (default 10, max 50)
            
        Example: /api/school/search-by-name?q=Sydney&state=NSW&limit=10
        
        Returns:
            JSON array of matching schools with profile data
        """
        search_query = request.args.get('q', '').strip()
        state_filter = request.args.get('state', '').upper()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not search_query or len(search_query) < 2:
            return jsonify({'error': 'Query must be at least 2 characters'}), 400
        
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Search query with optional state filter
            sql = """
            SELECT 
                school_id,
                catchment_school_name,
                school_first,
                school_abbrev,
                school_type_name,
                profile_school_name,
                school_sector,
                school_type,
                icsea,
                icsea_percentile,
                suburb,
                state,
                postcode,
                school_url
            FROM gnaf.school_type_lookup
            WHERE (
                catchment_school_name ILIKE %s 
                OR profile_school_name ILIKE %s
                OR school_first ILIKE %s
            )
            """
            
            params = [f'%{search_query}%', f'%{search_query}%', f'%{search_query}%']
            
            if state_filter:
                sql += " AND state = %s"
                params.append(state_filter)
            
            sql += " ORDER BY catchment_school_name LIMIT %s"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'school_id': row['school_id'],
                    'school_name': row['profile_school_name'] or row['catchment_school_name'],
                    'school_sector': row['school_sector'],
                    'school_type': row['school_type_name'],
                    'icsea': row['icsea'],
                    'icsea_percentile': row['icsea_percentile'],
                    'location': {
                        'suburb': row['suburb'],
                        'state': row['state'],
                        'postcode': row['postcode']
                    },
                    'school_url': row['school_url']
                })
            
            return jsonify({
                'total_results': len(formatted_results),
                'results': formatted_results
            }), 200
            
        except Exception as e:
            print(f"Error in school search: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'error': 'Search failed',
                'message': str(e)
            }), 500


# ============================================================================
# USAGE IN app.py
# ============================================================================
# Add this to your app.py after database configuration:
#
# from school_profile_search import setup_school_profile_routes
# 
# # Setup school profile routes
# setup_school_profile_routes(app, DB_CONFIG)
#
# Then you can use:
# GET /api/school/1001/profile  - Get profile for school ID 1001
# GET /api/school/search-by-name?q=Sydney&state=NSW&limit=10  - Search schools
