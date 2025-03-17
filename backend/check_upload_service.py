#!/usr/bin/env python3
"""
Check Upload Service
Verifies that the upload service has proper async methods
"""

import os
import sys
import inspect
import traceback
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def main():
    # Load environment variables
    load_dotenv()
    
    print("=" * 70)
    print("CHECKING UPLOAD SERVICE".center(70))
    print("=" * 70)
    
    try:
        # Import upload service
        print("\nImporting UploadService...")
        from services.upload_service import UploadService
        
        # Print info about the class
        print(f"Module: {UploadService.__module__}")
        
        # Check methods in UploadService
        print("\nMethods in UploadService:")
        for name, method in inspect.getmembers(UploadService, predicate=inspect.isfunction):
            # Skip private methods
            if name.startswith('_'):
                continue
                
            # Check if method is async
            is_async = inspect.iscoroutinefunction(method)
            
            print(f"Method: {name}, Async: {is_async}")
            
            # For key methods, check in more detail
            if name in ['upload_complete_question', 'bulk_upload_complete_questions', 'register_user']:
                source = inspect.getsource(method)
                
                # Check if contains await keyword
                has_await = 'await' in source
                
                print(f"  Contains 'await': {has_await}")
                
                # Check for potential issues
                if has_await and not is_async:
                    print(f"  ⚠️ WARNING: Method {name} contains 'await' but is not defined as async!")
                elif not has_await and is_async:
                    print(f"  ⚠️ WARNING: Method {name} is defined as async but doesn't contain 'await'!")
        
        # Check if the method signatures match what's expected by the controller
        print("\nChecking method signatures:")
        
        # Import the controller to compare
        from controllers.upload_controller import UploadController
        
        upload_service_methods = {name: method for name, method in inspect.getmembers(UploadService, predicate=inspect.isfunction) 
                                 if not name.startswith('_')}
        
        controller_methods = {name: method for name, method in inspect.getmembers(UploadController, predicate=inspect.isfunction) 
                             if not name.startswith('_')}
        
        for controller_method_name, controller_method in controller_methods.items():
            # Find corresponding service method (if it exists)
            if controller_method_name in ['upload_question', 'bulk_upload_questions', 'register_user']:
                expected_service_method = None
                
                if controller_method_name == 'upload_question':
                    expected_service_method = 'upload_complete_question'
                elif controller_method_name == 'bulk_upload_questions':
                    expected_service_method = 'bulk_upload_complete_questions'
                elif controller_method_name == 'register_user':
                    expected_service_method = 'register_user'
                
                if expected_service_method in upload_service_methods:
                    controller_is_async = inspect.iscoroutinefunction(controller_method)
                    service_is_async = inspect.iscoroutinefunction(upload_service_methods[expected_service_method])
                    
                    print(f"Controller {controller_method_name} (async: {controller_is_async}) -> " +
                          f"Service {expected_service_method} (async: {service_is_async})")
                    
                    if controller_is_async != service_is_async:
                        print(f"  ⚠️ WARNING: Async mismatch between controller and service method!")
                else:
                    print(f"⚠️ WARNING: Controller {controller_method_name} has no corresponding service method!")
        
        # Create an instance to check instance methods
        print("\nChecking instance methods:")
        import supabase
        from config.environment import Environment
        
        env = Environment()
        client = supabase.create_client(
            supabase_url=env.get("supabase_url"),
            supabase_key=env.get("supabase_key")
        )
        
        service = UploadService(client)
        
        for name, method in inspect.getmembers(service, predicate=inspect.ismethod):
            # Skip private methods
            if name.startswith('_'):
                continue
                
            # Check if method is async
            is_async = inspect.iscoroutinefunction(method)
            
            print(f"Method: {name}, Async: {is_async}")
            
            # Simple test call for upload_complete_question
            if name == 'upload_complete_question':
                print("\nTesting method call (not executing):")
                sig = inspect.signature(method)
                print(f"Method signature: {sig}")
                params = list(sig.parameters.keys())
                print(f"Parameters: {params}")
                
    except Exception as e:
        print(f"Error checking upload service: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()