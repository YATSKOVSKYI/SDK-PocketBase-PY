"""
PocketBase Python SDK
A Python client for PocketBase API
"""

import json
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import time
import os
import re


class PocketBaseException(Exception):
    """Custom exception for PocketBase API errors."""

    def __init__(self, message: str, status_code: int = None, data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(self.message)


class Collection:
    """Represents a PocketBase collection for performing CRUD operations"""

    def __init__(self, client, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    def get_list(self, page: int = 1, per_page: int = 30, filter_str: str = None,
                 sort: str = None, expand: str = None) -> Dict:
        """
        Get a paginated list of records from the collection.

        Args:
            page: The page number (default: 1)
            per_page: The number of items per page (default: 30)
            filter_str: Filter expression following PocketBase filter rules
            sort: Sort expression following PocketBase sort rules
            expand: Expand expression following PocketBase expand rules

        Returns:
            Dictionary with paginated list results
        """
        params = {
            "page": page,
            "perPage": per_page
        }

        if filter_str:
            params["filter"] = filter_str
        if sort:
            params["sort"] = sort
        if expand:
            params["expand"] = expand

        return self.client._send_request("GET", f"collections/{self.collection_name}/records", params=params)

    def get_one(self, record_id: str, expand: str = None) -> Dict:
        """
        Get a single record by ID.

        Args:
            record_id: The ID of the record to retrieve
            expand: Expand expression following PocketBase expand rules

        Returns:
            Dictionary with the record data
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.client._send_request("GET", f"collections/{self.collection_name}/records/{record_id}",
                                         params=params)

    def create(self, data: Dict, expand: str = None) -> Dict:
        """
        Create a new record.

        Args:
            data: Dictionary with the record data
            expand: Expand expression following PocketBase expand rules

        Returns:
            Dictionary with the created record data
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.client._send_request("POST", f"collections/{self.collection_name}/records", params=params,
                                         json=data)

    def update(self, record_id: str, data: Dict, expand: str = None) -> Dict:
        """
        Update an existing record.

        Args:
            record_id: The ID of the record to update
            data: Dictionary with the record data to update
            expand: Expand expression following PocketBase expand rules

        Returns:
            Dictionary with the updated record data
        """
        params = {}
        if expand:
            params["expand"] = expand

        return self.client._send_request("PATCH", f"collections/{self.collection_name}/records/{record_id}",
                                         params=params, json=data)

    def delete(self, record_id: str) -> bool:
        """
        Delete a record.

        Args:
            record_id: The ID of the record to delete

        Returns:
            True if deletion was successful
        """
        self.client._send_request("DELETE", f"collections/{self.collection_name}/records/{record_id}")
        return True

    def get_full_list(self, batch: int = 100, filter_str: str = None,
                      sort: str = None, expand: str = None) -> List[Dict]:
        """
        Get a full list of records from the collection (all pages).

        Args:
            batch: The batch size (default: 100)
            filter_str: Filter expression following PocketBase filter rules
            sort: Sort expression following PocketBase sort rules
            expand: Expand expression following PocketBase expand rules

        Returns:
            List of all records
        """
        result = []
        page = 1

        while True:
            response = self.get_list(page, batch, filter_str, sort, expand)
            result.extend(response.get("items", []))

            if page >= response.get("totalPages", 0):
                break

            page += 1

        return result

    def filter(self, filter_str: str) -> 'Collection':
        """
        Creates a filter wrapper for the collection.

        Args:
            filter_str: Filter expression following PocketBase filter rules

        Returns:
            A new Collection instance with filter applied
        """
        collection = Collection(self.client, self.collection_name)
        collection._filter = filter_str
        return collection


class Auth:
    """Authentication related methods for PocketBase."""

    def __init__(self, client):
        self.client = client

    def authenticate_with_password(self, identity: str, password: str, collection_name: str = "users") -> Dict:
        """
        Authenticate with email/username and password.

        Args:
            identity: The user email or username
            password: The user password
            collection_name: The auth collection name (default: "users")

        Returns:
            Authentication data including token and record
        """
        data = {
            "identity": identity,
            "password": password
        }

        result = self.client._send_request("POST", f"collections/{collection_name}/auth-with-password", json=data)

        # Save the auth data and token
        self.client.auth_store.save(result.get("token", ""), result.get("record", {}))

        return result

    def refresh_token(self) -> Dict:
        """
        Refreshes the current auth token.

        Returns:
            New authentication data including token and record
        """
        result = self.client._send_request("POST", "auth/refresh")

        # Save the auth data and token
        self.client.auth_store.save(result.get("token", ""), result.get("record", {}))

        return result

    def get_token(self) -> str:
        """Get the current auth token."""
        return self.client.auth_store.token

    def get_model(self) -> Dict:
        """Get the current auth model (user record)."""
        return self.client.auth_store.model

    @property
    def is_valid(self) -> bool:
        """Check if the current auth token is valid."""
        return self.client.auth_store.is_valid

    def clear(self) -> None:
        """Clear the current authentication."""
        self.client.auth_store.clear()


class AuthStore:
    """Storage for authentication data."""

    def __init__(self):
        self.token = ""
        self.model = {}
        self.is_admin = False

    def save(self, token: str, model: Dict, is_admin: bool = False) -> None:
        """
        Save auth data.

        Args:
            token: Auth token
            model: Auth model (user or admin record)
            is_admin: Whether this auth is for an admin
        """
        self.token = token
        self.model = model
        self.is_admin = is_admin

    def clear(self) -> None:
        """Clear auth data."""
        self.token = ""
        self.model = {}
        self.is_admin = False

    @property
    def is_valid(self) -> bool:
        """Check if the current token is valid."""
        return bool(self.token) and bool(self.model)


class Admin:
    """Admin API methods for PocketBase."""

    def __init__(self, client):
        self.client = client

    def authenticate_with_password(self, email: str, password: str) -> Dict:
        """
        Authenticate as admin with email and password.

        Args:
            email: Admin email
            password: Admin password

        Returns:
            Authentication data including token and admin record
        """
        data = {
            "identity": email,
            "password": password
        }

        # Исправленный путь для авторизации администраторов
        result = self.client._send_request("POST", "_superusers/auth-with-password", json=data)

        # Save the auth data and token, marking as admin auth
        self.client.auth_store.save(result.get("token", ""), result.get("admin", {}), True)

        return result

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated as admin.

        Returns:
            True if authenticated as admin
        """
        return self.client.auth_store.is_valid and self.client.auth_store.is_admin

    def is_super_admin(self) -> bool:
        """
        Check if the authenticated admin is a super admin.
        Note: PocketBase superadmins can access and modify anything.

        Returns:
            True if super admin, False otherwise
        """
        if not self.is_authenticated():
            return False

        # В PocketBase все администраторы являются суперпользователями
        return True


class PocketBase:
    """Main PocketBase client."""

    def __init__(self, base_url: str):
        """
        Initialize PocketBase client.

        Args:
            base_url: The base URL of your PocketBase API (e.g., "http://127.0.0.1:8090")
        """
        self.base_url = base_url.rstrip("/")
        self.auth_store = AuthStore()
        self.auth = Auth(self)
        self.admins = Admin(self)

    def collection(self, collection_name: str) -> Collection:
        """
        Get a Collection instance.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection instance for the specified collection
        """
        return Collection(self, collection_name)

    def _send_request(self, method: str, endpoint: str, params: Dict = None,
                      json: Dict = None, files: Dict = None) -> Dict:
        """
        Send a request to the PocketBase API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint path
            params: URL parameters
            json: JSON body data
            files: Files to upload

        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {}

        # Add authentication token if available
        if self.auth_store.token:
            headers["Authorization"] = f"Bearer {self.auth_store.token}"

        try:
            if files:
                # For multipart/form-data requests with file uploads
                data = json or {}
                response = requests.request(method, url, params=params,
                                            data=data, files=files, headers=headers)
            else:
                # For regular JSON requests
                response = requests.request(method, url, params=params,
                                            json=json, headers=headers)

            # Raise exception for non-2xx status codes
            response.raise_for_status()

            if response.status_code == 204:  # No content
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            # Try to parse error response
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                pass

            raise PocketBaseException(
                message=error_data.get("message", str(e)),
                status_code=e.response.status_code,
                data=error_data
            )
        except requests.exceptions.RequestException as e:
            raise PocketBaseException(str(e))

    def send_reset_password_email(self, email: str, collection_name: str = "users") -> bool:
        """
        Send a password reset email.

        Args:
            email: User email
            collection_name: Auth collection name (default: "users")

        Returns:
            True if the request was successful
        """
        data = {
            "email": email
        }

        self._send_request("POST", f"collections/{collection_name}/request-password-reset", json=data)
        return True

    def confirm_verification(self, token: str, collection_name: str = "users") -> bool:
        """
        Confirm email verification.

        Args:
            token: Verification token
            collection_name: Auth collection name (default: "users")

        Returns:
            True if the request was successful
        """
        data = {
            "token": token
        }

        self._send_request("POST", f"collections/{collection_name}/confirm-verification", json=data)
        return True

    def confirm_password_reset(self, token: str, password: str, password_confirm: str,
                               collection_name: str = "users") -> bool:
        """
        Confirm password reset.

        Args:
            token: Password reset token
            password: New password
            password_confirm: New password confirmation
            collection_name: Auth collection name (default: "users")

        Returns:
            True if the request was successful
        """
        data = {
            "token": token,
            "password": password,
            "passwordConfirm": password_confirm
        }

        self._send_request("POST", f"collections/{collection_name}/confirm-password-reset", json=data)
        return True

    def health(self) -> Dict:
        """
        Check API health.

        Returns:
            Health check data
        """
        return self._send_request("GET", "health")