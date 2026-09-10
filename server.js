const { spawn } = require("node:child_process");
const path = require("node:path");

const pythonCommand = process.platform === "win32" ? "python" : "python3";
const launcher = spawn(pythonCommand, [path.join(__dirname, "run.py")], {
  cwd: __dirname,
  stdio: "inherit",
});

let shuttingDown = false;

function stopLauncher(signal) {
  if (shuttingDown) {
    return;
  }

  shuttingDown = true;
  launcher.kill(signal);
}

process.once("SIGINT", () => stopLauncher("SIGINT"));
process.once("SIGTERM", () => stopLauncher("SIGTERM"));

launcher.on("error", (error) => {
  console.error(`Unable to start Python launcher: ${error.message}`);
  process.exit(1);
});

launcher.on("exit", (code, signal) => {
  if (signal && !shuttingDown) {
    process.exitCode = 1;
    return;
  }

  process.exitCode = code ?? 0;
});