# test_users.py
#!/usr/bin/env python
# python3 test_users.py --verbose

import requests
import json
import argparse
import sys
import uuid
from typing import Dict, List, Any, Optional
import os
import traceback  # Import traceback

# API base URL
BASE_URL = "http://localhost:8000/api"

# ANSI color codes for prettier output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Test case result type
class ResultType:
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    SKIP = "SKIP"

def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    try:
        print(json.dumps(data, indent=2))
    except TypeError: # Handle cases where data might not be JSON serializable directly
        print(str(data))


def generate_random_name(prefix: str = "TestUser") -> str:
    """Generate a random name."""
    return f"{prefix}_{uuid.uuid4().hex[:6]}"

# --- MODIFIED LINE ---
def generate_random_email(domain: str = "example.com") -> str: # Changed domain to example.com
    """Generate a random email address."""
    return f"{uuid.uuid4().hex[:10]}@{domain}"
# --- END MODIFIED LINE ---

class UserTester:
    def __init__(self, base_url: str = BASE_URL, verbose: bool = False):
        """Initialize the User API tester."""
        self.base_url = base_url
        self.verbose = verbose
        self.results = []
        # Store IDs/emails of created users for subsequent tests and cleanup
        self.permanent_user_id: Optional[str] = None
        self.permanent_user_email: Optional[str] = None
        self.temp_user_id: Optional[str] = None
        self.auth_user_id: Optional[str] = None
        self.converted_temp_user_id: Optional[str] = None # ID after conversion

    def log(self, message: str, end="\n") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message, end=end)

    def record_result(self, test_name: str, result_type: str, message: str = "", data: Any = None, detail: str = None) -> None:
        """Record the test result, including detailed error if available."""
        self.results.append({
            "test_name": test_name,
            "result_type": result_type,
            "message": message,
            "data": data,
            "detail": detail
        })

        # Print result to console
        color = Colors.GREEN if result_type == ResultType.SUCCESS else \
                Colors.WARNING if result_type == ResultType.SKIP else Colors.FAIL

        result_str = f"{color}{result_type}{Colors.ENDC}"
        message_str = f" - {message}" if message else ""

        print(f"{test_name}: {result_str}{message_str}")

        # Print detailed error if it's a failure and detail exists
        if result_type == ResultType.FAIL and detail:
            print(f"  {Colors.FAIL}Detail: {detail}{Colors.ENDC}")

        if data and self.verbose:
            print("  Response Data:")
            print_json(data)


    def run_test(self, test_func, test_name: str, skip_condition: bool = False) -> Any:
        """Run a test function and record the result."""
        if skip_condition:
            self.record_result(test_name, ResultType.SKIP, "Test skipped due to dependency failure")
            return None

        try:
            print(f"\n{Colors.BOLD}Running test: {test_name}{Colors.ENDC}")
            result = test_func()
            return result
        except requests.exceptions.ConnectionError as e:
             self.record_result(test_name, ResultType.FAIL, f"Connection Error: Could not connect to API at {self.base_url}. Is the server running?", detail=str(e))
             # Stop further tests if connection fails
             raise SystemExit("API Connection Failed") from e
        except Exception as e:
            tb_str = traceback.format_exc()
            self.record_result(test_name, ResultType.FAIL, f"Exception: {type(e).__name__}", detail=tb_str if self.verbose else str(e))
            return None

    def _handle_api_error(self, test_name: str, response: requests.Response):
        """Helper to record API errors, attempting to parse details."""
        message = f"Failed with status code: {response.status_code}"
        response_data = None
        detail = None
        try:
            response_data = response.json()
            # FastAPI 422 errors often have a 'detail' field
            if isinstance(response_data, dict) and 'detail' in response_data:
                detail = response_data['detail'] # Extract specific validation error
                if isinstance(detail, list): # FastAPI validation errors are often lists of dicts
                     detail_str = json.dumps(detail)
                     if len(detail_str) > 300: # Keep it concise
                         detail = detail_str[:300] + "..."
                     else:
                         detail = detail_str
                elif isinstance(detail, str) and len(detail) > 300:
                     detail = detail[:300] + "..."


        except json.JSONDecodeError:
            response_data = response.text # Show raw text if not JSON
            detail = response.text[:300] + "..." if len(response.text) > 300 else response.text


        self.record_result(test_name, ResultType.FAIL, message, response_data, detail=detail)


    # --- Individual Test Methods ---

    def test_create_permanent_user(self) -> Optional[str]:
        """Test creating a standard (permanent) user."""
        test_name = "Create Permanent User"
        user_email = generate_random_email()
        user_name = generate_random_name("Perm")

        data = {
            "displayname": user_name,
            "email": user_email,
            "is_temporary": False, # Explicitly permanent
            # Explicitly set optional fields to None, though not strictly needed
            "auth_provider": None,
            "auth_id": None
        }

        self.log(f"Creating permanent user: {user_name} ({user_email})")
        self.log(f"Request Data: {json.dumps(data)}")
        response = requests.post(f"{self.base_url}/users/", json=data)

        if response.status_code == 201:
            response_data = response.json()
            user_id = response_data.get("id")
            self.permanent_user_id = user_id
            self.permanent_user_email = user_email # Store email for later tests
            self.record_result(test_name, ResultType.SUCCESS, f"Created user ID: {user_id}", response_data)
            return user_id
        else:
            self._handle_api_error(test_name, response)
            return None

    def test_create_temporary_user(self) -> Optional[str]:
        """Test creating a temporary user."""
        test_name = "Create Temporary User"
        user_name = generate_random_name("Temp")

        data = {
            "displayname": user_name,
            "is_temporary": True,
            # Explicitly set optional fields to None
            "email": None,
            "auth_provider": None,
            "auth_id": None
        }

        self.log(f"Creating temporary user: {user_name}")
        self.log(f"Request Data: {json.dumps(data)}")
        response = requests.post(f"{self.base_url}/users/", json=data)

        if response.status_code == 201:
            response_data = response.json()
            user_id = response_data.get("id")
            self.temp_user_id = user_id # Store ID for conversion test
            self.record_result(test_name, ResultType.SUCCESS, f"Created temp user ID: {user_id}", response_data)
            return user_id
        else:
            self._handle_api_error(test_name, response)
            return None


    def test_get_user_by_id(self) -> Optional[Dict]:
        """Test retrieving a user by their ID."""
        test_name = "Get User by ID"
        user_id_to_get = self.permanent_user_id

        if not user_id_to_get:
            self.record_result(test_name, ResultType.SKIP, "No permanent user ID available")
            return None

        self.log(f"Getting user with ID: {user_id_to_get}")
        response = requests.get(f"{self.base_url}/users/{user_id_to_get}")

        if response.status_code == 200:
            response_data = response.json()
            self.record_result(test_name, ResultType.SUCCESS, f"Retrieved user data", response_data)
            return response_data
        else:
            self._handle_api_error(test_name, response)
            return None

    def test_get_user_by_email(self) -> Optional[Dict]:
        """Test retrieving a user by their email."""
        test_name = "Get User by Email"
        user_email_to_get = self.permanent_user_email

        if not user_email_to_get:
            self.record_result(test_name, ResultType.SKIP, "No permanent user email available")
            return None

        self.log(f"Getting user with email: {user_email_to_get}")
        response = requests.get(f"{self.base_url}/users/email/{user_email_to_get}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("id") == self.permanent_user_id:
                 self.record_result(test_name, ResultType.SUCCESS, f"Retrieved user data", response_data)
            else:
                 self.record_result(test_name, ResultType.FAIL, f"Retrieved user ID {response_data.get('id')} does not match expected {self.permanent_user_id}", response_data)
            return response_data
        else:
             self._handle_api_error(test_name, response)
             return None

    def test_update_user(self) -> Optional[Dict]:
        """Test updating a user's information."""
        test_name = "Update User"
        user_id_to_update = self.permanent_user_id
        new_name = generate_random_name("Updated")

        if not user_id_to_update:
            self.record_result(test_name, ResultType.SKIP, "No permanent user ID available to update")
            return None

        data = {
            "displayname": new_name
            # Only send the field being updated
        }

        self.log(f"Updating user {user_id_to_update} with new name: {new_name}")
        self.log(f"Request Data: {json.dumps(data)}")
        response = requests.put(f"{self.base_url}/users/{user_id_to_update}", json=data)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("displayname") == new_name:
                self.record_result(test_name, ResultType.SUCCESS, f"User updated successfully", response_data)
            else:
                self.record_result(test_name, ResultType.FAIL, f"User displayname did not update as expected", response_data)
            return response_data
        else:
             self._handle_api_error(test_name, response)
             return None

    def test_authenticate_user(self) -> Optional[str]:
        """Test authenticating (get or create) user via auth provider."""
        test_name = "Authenticate User (Get/Create)"
        auth_provider = "test_provider"
        auth_id = uuid.uuid4().hex # Unique auth ID
        user_name = generate_random_name("Auth")
        user_email = generate_random_email() # Use updated generator

        data = {
            "auth_provider": auth_provider,
            "auth_id": auth_id,
            "email": user_email,
            "displayname": user_name
        }

        self.log(f"Authenticating user via: {auth_provider}/{auth_id}")
        self.log(f"Request Data: {json.dumps(data)}")
        response = requests.post(f"{self.base_url}/users/auth", json=data)

        if response.status_code == 200:
            response_data = response.json()
            user_id = response_data.get("id")
            self.auth_user_id = user_id # Store for cleanup
            self.record_result(test_name, ResultType.SUCCESS, f"Authenticated/Created user ID: {user_id}", response_data)
            return user_id
        else:
             self._handle_api_error(test_name, response)
             return None

    def test_convert_temporary_user(self) -> Optional[Dict]:
        """Test converting a temporary user to a permanent one."""
        test_name = "Convert Temporary User"
        user_id_to_convert = self.temp_user_id
        new_name = generate_random_name("Converted")
        new_email = generate_random_email() # Use updated generator
        auth_provider = "convert_provider"
        auth_id = uuid.uuid4().hex

        if not user_id_to_convert:
            self.record_result(test_name, ResultType.SKIP, "No temporary user ID available to convert")
            return None

        data = {
            "displayname": new_name,
            "email": new_email,
            "auth_provider": auth_provider,
            "auth_id": auth_id
        }

        self.log(f"Converting temporary user {user_id_to_convert} to permanent")
        self.log(f"Request Data: {json.dumps(data)}")
        response = requests.post(f"{self.base_url}/users/convert/{user_id_to_convert}", json=data)

        if response.status_code == 200:
            response_data = response.json()
            if not response_data.get("is_temporary"):
                self.converted_temp_user_id = response_data.get("id") # Store ID for cleanup
                self.record_result(test_name, ResultType.SUCCESS, f"User converted successfully", response_data)
            else:
                self.record_result(test_name, ResultType.FAIL, f"User 'is_temporary' flag not updated", response_data)
            return response_data
        else:
             self._handle_api_error(test_name, response)
             return None

    def test_delete_user(self, user_id: Optional[str], user_desc: str) -> bool:
        """Test deleting a user."""
        test_name = f"Delete {user_desc} User"

        if not user_id:
            self.record_result(test_name, ResultType.SKIP, f"No {user_desc} user ID available to delete")
            return False

        self.log(f"Deleting {user_desc} user with ID: {user_id}")
        response = requests.delete(f"{self.base_url}/users/{user_id}")

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("id") == user_id:
                self.record_result(test_name, ResultType.SUCCESS, f"User deleted successfully", response_data)
                return True
            else:
                 self.record_result(test_name, ResultType.FAIL, f"Deleted user ID {response_data.get('id')} does not match expected {user_id}", response_data)
                 return False
        else:
             self._handle_api_error(test_name, response)
             return False

    def test_get_deleted_user(self, user_id: Optional[str], user_desc: str) -> bool:
        """Test getting a user that should have been deleted."""
        test_name = f"Get Deleted {user_desc} User (Should Fail)"

        if not user_id:
            self.record_result(test_name, ResultType.SKIP, f"No deleted {user_desc} user ID available to test")
            return False

        self.log(f"Attempting to get deleted {user_desc} user with ID: {user_id}")
        response = requests.get(f"{self.base_url}/users/{user_id}")

        if response.status_code == 404:
            response_data = response.json()
            self.record_result(test_name, ResultType.SUCCESS, "User not found as expected (404)", response_data)
            return True
        else:
            self._handle_api_error(test_name, response)
            return False


    # --- Test Orchestration and Summary ---

    def run_all_tests(self) -> None:
        """Run all user API tests in a logical sequence."""
        print(f"{Colors.HEADER}Starting User API Tests{Colors.ENDC}")
        print(f"Base URL: {self.base_url}")

        # 1. Create Permanent User
        self.run_test(self.test_create_permanent_user, "Create Permanent User")

        # 2. Create Temporary User
        self.run_test(self.test_create_temporary_user, "Create Temporary User")

        # 3. Get User by ID (depends on permanent user)
        self.run_test(self.test_get_user_by_id, "Get User by ID", skip_condition=not self.permanent_user_id)

        # 4. Get User by Email (depends on permanent user)
        self.run_test(self.test_get_user_by_email, "Get User by Email", skip_condition=not self.permanent_user_email)

        # 5. Update User (depends on permanent user)
        self.run_test(self.test_update_user, "Update User", skip_condition=not self.permanent_user_id)

        # 6. Authenticate User (Get or Create)
        self.run_test(self.test_authenticate_user, "Authenticate User (Get/Create)")

        # 7. Convert Temporary User (depends on temporary user)
        self.run_test(self.test_convert_temporary_user, "Convert Temporary User", skip_condition=not self.temp_user_id)

        # --- Cleanup ---
        print(f"\n{Colors.HEADER}--- Running Cleanup ---{Colors.ENDC}")

        # 8. Delete Permanent User
        perm_deleted = self.run_test(lambda: self.test_delete_user(self.permanent_user_id, "Permanent"), "Delete Permanent User")

        # 9. Confirm Permanent User Deletion
        self.run_test(lambda: self.test_get_deleted_user(self.permanent_user_id, "Permanent"), "Get Deleted Permanent User", skip_condition=not perm_deleted)

        # 10. Delete Converted User (if conversion was successful)
        conv_deleted = self.run_test(lambda: self.test_delete_user(self.converted_temp_user_id, "Converted"), "Delete Converted User", skip_condition=not self.converted_temp_user_id)

        # 11. Confirm Converted User Deletion
        self.run_test(lambda: self.test_get_deleted_user(self.converted_temp_user_id, "Converted"), "Get Deleted Converted User", skip_condition=not conv_deleted)

        # 12. Delete Authenticated User (if created)
        auth_deleted = self.run_test(lambda: self.test_delete_user(self.auth_user_id, "Authenticated"), "Delete Authenticated User", skip_condition=not self.auth_user_id)

        # 13. Confirm Authenticated User Deletion
        self.run_test(lambda: self.test_get_deleted_user(self.auth_user_id, "Authenticated"), "Get Deleted Authenticated User", skip_condition=not auth_deleted)


        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print a summary of all test results."""
        total = len(self.results)
        success_count = sum(1 for r in self.results if r["result_type"] == ResultType.SUCCESS)
        fail_count = sum(1 for r in self.results if r["result_type"] == ResultType.FAIL)
        skip_count = sum(1 for r in self.results if r["result_type"] == ResultType.SKIP)

        print("\n" + "=" * 50)
        print(f"{Colors.HEADER}User API Test Summary{Colors.ENDC}")
        print(f"Total tests: {total}")
        print(f"Successful: {Colors.GREEN}{success_count}{Colors.ENDC}")
        print(f"Failed: {Colors.FAIL}{fail_count}{Colors.ENDC}")
        print(f"Skipped: {Colors.WARNING}{skip_count}{Colors.ENDC}")
        print("=" * 50)

        # Optionally list failed tests
        if fail_count > 0:
            print(f"\n{Colors.FAIL}Failed Tests Details:{Colors.ENDC}")
            for r in self.results:
                if r["result_type"] == ResultType.FAIL:
                    print(f"- {Colors.BOLD}{r['test_name']}{Colors.ENDC}: {r['message']}")
                    if r['detail']:
                         print(f"  Detail: {r['detail']}") # Print detailed error messages

def main():
    parser = argparse.ArgumentParser(description="Test the User API endpoints")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for the API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    tester = UserTester(base_url=args.base_url, verbose=args.verbose)
    tester.run_all_tests()

if __name__ == "__main__":
    main()