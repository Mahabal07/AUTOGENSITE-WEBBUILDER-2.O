#!/usr/bin/env python3
"""
Script to create an initial admin user for AutoSiteGen
"""

import json
from werkzeug.security import generate_password_hash

def create_admin_user():
    """Create an admin user in the users.json file"""
    
    # Default admin credentials
    admin_username = "admin"
    admin_password = "admin123"  # Change this to a secure password
    
    # Load existing users or create new list
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []
    
    # Check if admin user already exists
    for user in users:
        if user['username'] == admin_username:
            print(f"Admin user '{admin_username}' already exists!")
            return
    
    # Create admin user
    admin_user = {
        'username': admin_username,
        'password': generate_password_hash(admin_password),
        'is_admin': True
    }
    
    users.append(admin_user)
    
    # Save to file
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"Admin user created successfully!")
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")
    print("\nIMPORTANT: Change the default password after first login!")

if __name__ == "__main__":
    create_admin_user() 