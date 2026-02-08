import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
  try {
    const { country, daysFilter, maxPosts, skipDuplicates } = await request.json().catch(() => ({}));

    // Security: Whitelist allowed countries to prevent command injection
    const ALLOWED_COUNTRIES = ['Toronto', 'Thailand', 'Philippines', 'UK', 'Australia'];
    const safeCountry = ALLOWED_COUNTRIES.includes(country) ? country : 'Toronto';

    // Security: Validate numeric inputs
    const safeDaysFilter = typeof daysFilter === 'number' && daysFilter >= 1 && daysFilter <= 365 ? Math.floor(daysFilter) : 14;
    const safeMaxPosts = typeof maxPosts === 'number' && maxPosts >= 1 && maxPosts <= 50 ? Math.floor(maxPosts) : 10;

    // Determine the path to the main.py script
    // Assuming 'frontend' is in the project root, and main.py is in the parent directory
    const scriptPath = path.resolve(process.cwd(), '../main.py');
    const projectRoot = path.resolve(process.cwd(), '../');

    // Build command with validated inputs only
    let command = `python3 ${scriptPath}`;
    command += ` --country "${safeCountry}"`;
    command += ` --days ${safeDaysFilter}`;
    command += ` --limit ${safeMaxPosts}`;

    if (skipDuplicates === false) {
      command += ` --no-skip-duplicates`;
    }

    console.log(`Executing command: ${command}`);

    // Execute the Python script
    // We wrap it in a promise to await the result
    const result = await new Promise<{ stdout: string; stderr: string }>((resolve, reject) => {
      exec(command, { cwd: projectRoot }, (error, stdout, stderr) => {
        if (error) {
          console.error(`Exec error: ${error}`);
          // We resolve even on error to return the stderr to the frontend
          resolve({ stdout, stderr: stderr + "\n" + error.message });
          return;
        }
        resolve({ stdout, stderr });
      });
    });

    return NextResponse.json({
      success: true,
      output: result.stdout,
      error: result.stderr
    });

  } catch (error: any) {
    return NextResponse.json(
      { success: false, error: error.message || 'Internal Server Error' },
      { status: 500 }
    );
  }
}
