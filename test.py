import subprocess

def main():
    try:
        process = subprocess.Popen(
            ["cmd", "/c", "echo Hello from subprocess"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        print("Subprocess Output:", stdout.decode())
        if stderr:
            print("Subprocess Error:", stderr.decode())
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
