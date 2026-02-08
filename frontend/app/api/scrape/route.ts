import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
  try {
    const { country, daysFilter, maxPosts, skipDuplicates } = await request.json().catch(() => ({}));

    // Determine the path to the main.py script
    // Assuming 'frontend' is in the project root, and main.py is in the parent directory
    const scriptPath = path.resolve(process.cwd(), '../main.py');
    const projectRoot = path.resolve(process.cwd(), '../');

    let command = `python3 ${scriptPath}`;

    if (country && typeof country === 'string' && country.trim().length > 0) {
      command += ` --country "${country}"`;
    }

    // Add filter settings
    if (daysFilter && typeof daysFilter === 'number') {
      command += ` --days ${daysFilter}`;
    }

    if (maxPosts && typeof maxPosts === 'number') {
      command += ` --limit ${maxPosts}`;
    }

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
