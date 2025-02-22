from remove_duplicates import get_unique_questions
from database_import import upload_questions

def main():
    # Generate questions and remove duplicates
    unique_questions = get_unique_questions()
    
    # Upload the unique questions to Supabase
    upload_questions(unique_questions)

if __name__ == "__main__":
    main()