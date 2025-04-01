import { NextRequest, NextResponse } from 'next/server';
import supabase from '@/lib/supabase';
import { prepareQuestion, shuffleArray } from '@/lib/utils';

export async function GET(
  request: NextRequest,
  { params }: { params: { packId: string } }
) {
  try {
    const packId = params.packId;
    
    // Check if the pack exists
    const { data: packData, error: packError } = await supabase
      .from('packs')
      .select('*')
      .eq('id', packId)
      .single();
    
    if (packError || !packData) {
      return NextResponse.json(
        { error: 'Pack not found' },
        { status: 404 }
      );
    }
    
    // Fetch all questions for this pack
    const { data: questionsData, error: questionsError } = await supabase
      .from('questions')
      .select('*')
      .eq('pack_id', packId);
    
    if (questionsError) {
      console.error('Error fetching questions:', questionsError);
      return NextResponse.json(
        { error: 'Failed to fetch questions' },
        { status: 500 }
      );
    }
    
    // If no questions available
    if (!questionsData || questionsData.length === 0) {
      return NextResponse.json(
        { error: 'No questions available for this pack' },
        { status: 404 }
      );
    }
    
    // Get a random subset of questions (10 or less if fewer are available)
    const count = Math.min(10, questionsData.length);
    const randomQuestions = shuffleArray(questionsData).slice(0, count);
    
    // Fetch incorrect answers for each question
    const questionsWithOptions = await Promise.all(
      randomQuestions.map(async (question) => {
        const { data: incorrectAnswersData, error: incorrectAnswersError } = await supabase
          .from('answers')
          .select('incorrect_answers')
          .eq('question_id', question.id)
          .single();
        
        if (incorrectAnswersError || !incorrectAnswersData) {
          // If we can't find incorrect answers, generate some placeholder ones
          const placeholderAnswers = ['Option A', 'Option B', 'Option C'];
          return prepareQuestion(question, placeholderAnswers);
        }
        
        return prepareQuestion(question, incorrectAnswersData.incorrect_answers);
      })
    );
    
    return NextResponse.json({ questions: questionsWithOptions });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}