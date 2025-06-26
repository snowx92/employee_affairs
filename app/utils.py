from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def permission_required(permission_type='read'):
    """
    Decorator to check if a user has the required permission for a route.
    
    Args:
        permission_type: The type of permission required ('read', 'write', or 'both')
        
    Returns:
        Decorator function that will check permissions before allowing access to a route
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the current route name
            route_name = request.endpoint
            
            # Check if the user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Admin users have access to everything (optional, remove if admins should also be restricted)
            if current_user.user_type == 'admin':
                return f(*args, **kwargs)
            
            # Check if the user has the required permission by querying the database
            user_permission = current_user.get_permission_type(route_name)
            
            # Determine if the user has the required access level
            has_access = False
            if user_permission == 'both':
                # 'both' permission grants access to everything
                has_access = True
            elif permission_type == 'read' and user_permission in ['read', 'both']:
                # 'read' permission requirement is fulfilled by 'read' or 'both'
                has_access = True
            elif permission_type == 'write' and user_permission in ['write', 'both']:
                # 'write' permission requirement is fulfilled by 'write' or 'both'
                has_access = True
            
            if not has_access:
                flash(f'You do not have {permission_type} permission to access this page.', 'danger')
                return redirect(url_for('main.admin_dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_permission_for_action(route_name, permission_type='write'):
    """
    Helper function to check if a user has permission to perform an action.
    Use this in API endpoints or views to check permission before performing an action.
    
    Args:
        route_name: The route name to check permission for
        permission_type: The type of permission required ('read', 'write', or 'both')
        
    Returns:
        Boolean indicating whether the user has permission
    """
    # Admin users have access to everything
    if not current_user.is_authenticated:
        return False
        
    if current_user.user_type == 'admin':
        return True
        
    # Get the user's permission type for this route
    user_permission = current_user.get_permission_type(route_name)
    
    # Determine if the user has the required access level
    if user_permission == 'both':
        return True
    elif permission_type == 'read' and user_permission in ['read', 'both']:
        return True
    elif permission_type == 'write' and user_permission in ['write', 'both']:
        return True
    
    return False 