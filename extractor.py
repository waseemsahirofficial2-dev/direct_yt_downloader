import subprocess
import os
import sys
import time

URL = os.environ.get("VIDEO_URL")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Added common YouTube clients along with standard fallback
configs = [
    {"client": "android", "use_cookies": True},
    {"client": "tv", "use_cookies": True},
    {"client": "web", "use_cookies": True}
]

def main():
    if not URL:
        print("❌ No VIDEO_URL provided.")
        sys.exit(1)

    print(f"🔍 Extracting direct link for: {URL}", flush=True)

    for attempt in range(1, 3):
        if attempt > 1:
            print("\n🔄 Cycling Cloudflare WARP...", flush=True)
            subprocess.run("sudo warp-cli --accept-tos disconnect", shell=True, stdout=subprocess.DEVNULL)
            time.sleep(3)
            subprocess.run("sudo warp-cli --accept-tos connect", shell=True, stdout=subprocess.DEVNULL)
            time.sleep(8)

        for cfg in configs:
            print(f"🎥 Trying client: {cfg['client']}", flush=True)
            
            cmd = [
                "yt-dlp",
                "--no-check-certificate",
                "--extractor-args", f"youtube:client={cfg['client']}",
                "--user-agent", USER_AGENT,
                # Force a single file with both video and audio (usually max 720p for YT direct links)
                "-f", "b", 
                "--print", "urls",
                URL
            ]

            if cfg["use_cookies"] and os.path.exists("cookies.txt"):
                cmd.extend(["--cookies", "cookies.txt"])

            try:
                process = subprocess.run(cmd, capture_output=True, text=True, check=True)
                urls = process.stdout.strip().split('\n')
                
                if urls and urls[0].startswith("http"):
                    direct_url = urls[0]
                    print("✅ SUCCESSFULLY EXTRACTED", flush=True)
                    print(f"DIRECT_URL={direct_url}", flush=True)
                    
                    # Write to GitHub Actions outputs
                    if "GITHUB_OUTPUT" in os.environ:
                        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                            f.write(f"direct_url={direct_url}\n")
                    
                    sys.exit(0)
            except subprocess.CalledProcessError as e:
                print(f"❌ FAILED CONFIG: {cfg['client']}", flush=True)
                print(e.stderr, flush=True)

    print("❌ ALL ATTEMPTS FAILED", flush=True)
    sys.exit(1)

if __name__ == "__main__":
    main()
