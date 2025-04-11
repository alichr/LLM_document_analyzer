import subprocess
import time
import os

REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Automatically detect project root
CHECK_INTERVAL = 15  # seconds

def run_command(cmd):
    return subprocess.run(cmd, cwd=REPO_PATH, shell=True, capture_output=True, text=True)

def get_latest_commit():
    result = run_command("git rev-parse HEAD")
    return result.stdout.strip()

def restart_flask():
    print("🔁 Restarting Flask app...")
    subprocess.run("pkill -f flask", shell=True)
    env = os.environ.copy()
    env["FLASK_APP"] = "app/web_page.py"  # change if needed
    env["FLASK_ENV"] = "development"
    subprocess.Popen("nohup flask run --host=0.0.0.0 --port=5000 > flask.log 2>&1 &",
                     cwd=REPO_PATH, shell=True, env=env)

def main():
    print("🚀 Auto-deployer running...")
    last_commit = get_latest_commit()

    while True:
        time.sleep(CHECK_INTERVAL)
        run_command("git fetch origin main")
        new_commit = run_command("git rev-parse origin/main").stdout.strip()

        if new_commit != last_commit:
            print(f"🔄 New commit detected: {new_commit}")
            run_command("git pull origin main")
            restart_flask()
            last_commit = new_commit
        else:
            print("✅ No new commits.")

if __name__ == "__main__":
    main()
