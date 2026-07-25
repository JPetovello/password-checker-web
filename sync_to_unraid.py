import os
import shutil
import subprocess

# --- SET YOUR REPO ROOT PATH HERE ---
UNRAID_REPO_PATH = r"/mnt/user/appdata/password-checker-web"

def main():
    print("=== Unraid Template Sync Tool ===")
    app_name = input("App Name (e.g., password-checker-web): ").strip()
    
    xml_source = f"{app_name}.xml"
    target_dir = os.path.expanduser(UNRAID_REPO_PATH)

    if not os.path.exists(target_dir):
        print(f"[-] Error: The configured path does not exist: {target_dir}")
        return

    # Copy XML file safely
    if os.path.exists(xml_source):
        src_path = os.path.abspath(xml_source)
        dst_path = os.path.abspath(os.path.join(target_dir, f"{app_name}.xml"))
        if src_path != dst_path:
            shutil.copy(src_path, dst_path)
            print(f"[+] Copied {xml_source} to repository root.")
        else:
            print(f"[i] {xml_source} is already in the target directory.")
    else:
        print(f"[-] Warning: {xml_source} not found in the current directory.")

    # Locate and copy icon file dynamically
    icon_source = f"{app_name}.png"
    if not os.path.exists(icon_source):
        if os.path.exists("icon.png"):
            icon_source = "icon.png"
        elif os.path.exists("Icon.png"):
            icon_source = "Icon.png"

    if os.path.exists(icon_source):
        src_icon = os.path.abspath(icon_source)
        dst_icon = os.path.abspath(os.path.join(target_dir, f"{app_name}.png"))
        if src_icon != dst_icon:
            shutil.copy(src_icon, dst_icon)
            print(f"[+] Copied and renamed icon to {app_name}.png in repository root.")
        else:
            print(f"[i] Icon is already in place as {app_name}.png.")
    else:
        print(f"[-] Warning: No matching app icon found (looking for {app_name}.png or icon.png).")

    # Optional Git Automation inside the repository
    do_git = input("Automatically commit and push changes? (y/n): ").strip().lower()
    if do_git == 'y':
        try:
            original_dir = os.getcwd()
            os.chdir(target_dir)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Update template and assets for {app_name}"], check=True)
            # Pull remote changes first to avoid rejections
            subprocess.run(["git", "pull", "--rebase"], check=True)
            subprocess.run(["git", "push"], check=True)
            os.chdir(original_dir)
            print("[+] Successfully synced and pushed changes to GitHub!")
        except subprocess.CalledProcessError as e:
            os.chdir(original_dir)
            print(f"[-] Git command failed: {e}")

if __name__ == "__main__":
    main()
