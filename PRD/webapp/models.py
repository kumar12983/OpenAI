"""
Database models for user authentication and subscription management
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor


class User(UserMixin):
    """User model for authentication and subscription management"""
    
    def __init__(self, user_id, email, full_name, tier_id, tier_name, 
                 searches_per_month, can_export_data, can_access_analytics,
                 can_access_school_catchments, subscription_status):
        self.id = user_id  # Required by Flask-Login
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
        self.tier_id = tier_id
        self.tier_name = tier_name
        self.searches_per_month = searches_per_month
        self.can_export_data = can_export_data
        self.can_access_analytics = can_access_analytics
        self.can_access_school_catchments = can_access_school_catchments
        self.subscription_status = subscription_status
    
    @staticmethod
    def get_by_id(conn, user_id):
        """Load user by ID"""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                u.user_id,
                u.email,
                u.full_name,
                u.tier_id,
                t.tier_name,
                t.searches_per_month,
                t.can_export_data,
                t.can_access_analytics,
                t.can_access_school_catchments,
                u.subscription_status
            FROM webapp.users u
            JOIN webapp.subscription_tiers t ON u.tier_id = t.tier_id
            WHERE u.user_id = %s AND u.is_active = TRUE
        """, (user_id,))
        
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return User(**row)
        return None
    
    @staticmethod
    def get_by_email(conn, email):
        """Load user by email"""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                u.user_id,
                u.email,
                u.full_name,
                u.password_hash,
                u.tier_id,
                t.tier_name,
                t.searches_per_month,
                t.can_export_data,
                t.can_access_analytics,
                t.can_access_school_catchments,
                u.subscription_status
            FROM webapp.users u
            JOIN webapp.subscription_tiers t ON u.tier_id = t.tier_id
            WHERE u.email = %s AND u.is_active = TRUE
        """, (email,))
        
        row = cursor.fetchone()
        cursor.close()
        
        return row
    
    @staticmethod
    def create_user(conn, email, password, full_name):
        """Create a new user with Free tier"""
        password_hash = generate_password_hash(password)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO webapp.users (email, password_hash, full_name, tier_id, subscription_start_date)
                VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP)
                RETURNING user_id
            """, (email, password_hash, full_name))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            return user_id
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.close()
            return None
        except psycopg2.Error:
            conn.rollback()
            cursor.close()
            return None
    
    @staticmethod
    def verify_password(password_hash, password):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    def get_monthly_usage(self, conn):
        """Get current month's search count for this user"""
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM webapp.usage_tracking
            WHERE user_id = %s
            AND request_timestamp >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
        """, (self.user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        return result['count'] if result else 0
    
    def has_searches_remaining(self, conn):
        """Check if user has searches remaining this month"""
        if self.searches_per_month is None:  # Unlimited
            return True
        
        usage = self.get_monthly_usage(conn)
        return usage < self.searches_per_month
    
    def track_usage(self, conn, endpoint, search_type, search_query, status_code, ip_address):
        """Record a search in usage tracking"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO webapp.usage_tracking 
            (user_id, endpoint, search_type, search_query, response_status, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (self.user_id, endpoint, search_type, search_query, status_code, ip_address))
        conn.commit()
        cursor.close()
    
    def is_premium(self):
        """Check if user has premium subscription"""
        return self.tier_name == 'Premium' and self.subscription_status == 'active'
