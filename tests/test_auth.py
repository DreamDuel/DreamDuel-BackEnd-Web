"""Test authentication endpoints"""

import pytest
from fastapi import status


def test_register_success(client, test_user_data):
    """Test successful user registration"""
    response = client.post("/api/auth/register", json=test_user_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["email"] == test_user_data["email"]
    assert data["user"]["username"] == test_user_data["username"]


def test_register_duplicate_email(client, test_user_data):
    """Test registration with duplicate email"""
    # Register first user
    client.post("/api/auth/register", json=test_user_data)
    
    # Try to register again with same email
    response = client.post("/api/auth/register", json=test_user_data)
    
    assert response.status_code == status.HTTP_409_CONFLICT


def test_login_success(client, test_user_data):
    """Test successful login"""
    # Register user first
    client.post("/api/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "emailOrUsername": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "token" in data
    assert "user" in data


def test_login_invalid_credentials(client, test_user_data):
    """Test login with invalid credentials"""
    login_data = {
        "emailOrUsername": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user(client, test_user_data):
    """Test getting current user profile"""
    # Register user
    register_response = client.post("/api/auth/register", json=test_user_data)
    token = register_response.json()["token"]
    
    # Get current user
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
