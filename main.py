from generate_questions import get_trivia_questions
from remove_duplicates import remove_duplicates
from database_import import upload_to_supabase

category = "General Knowledge"
num_questions = 300

questions = get_trivia_questions(category, num_questions)
unique_questions = remove_duplicates(questions)
upload_to_supabase(unique_questions)