import { NextResponse } from 'next/server';
import supabase from '@/lib/supabase';

export async function GET() {
  try {
    // Fetch all packs from the packs table
    const { data, error } = await supabase
      .from('packs')
      .select('*')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Error fetching packs:', error);
      return NextResponse.json(
        { error: 'Failed to fetch packs' },
        { status: 500 }
      );
    }
    
    return NextResponse.json({ packs: data });
  } catch (error) {
    console.error('Unexpected error:', error);
    return NextResponse.json(
      { error: 'An unexpected error occurred' },
      { status: 500 }
    );
  }
}