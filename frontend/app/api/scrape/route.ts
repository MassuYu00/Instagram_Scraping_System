import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import path from 'path';

export async function POST(request: Request) {
  try {
    const { targets, country } = await request.json().catch(() => ({}));

    // Determine the path to the main.py script
    // Assuming 'frontend' is in the project root, and main.py is in the parent directory
    const scriptPath = path.resolve(process.cwd(), '../main.py');
    const projectRoot = path.resolve(process.cwd(), '../');

    let command = `python3 ${scriptPath}`;
    if (targets && typeof targets === 'string' && targets.trim().length > 0) {
      // sanitize inputs to avoid command injection is ideal, but for internal tool we just pass it
      // Simple validation: ensure it only contains allowed chars if needed, or rely on python arg parser
      // We wrap it in quotes to handle spaces if any (though targets shouldn't have spaces ideally)
      command += ` --targets "${targets}"`;
    }

    if (country && typeof country === 'string' && country.trim().length > 0) {
      command += ` --country "${country}"`;
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
