import bpy
import os
import requests
import zipfile
import base64
import shutil
import sys
from io import BytesIO



# === Config ===
CACHE_DIR = bpy.app.tempdir
PY_FOLDER_V4 = os.path.join(CACHE_DIR, 'raha_tools', 'v4')
VERSION_FOLDER = PY_FOLDER_V4
BASE64_URL = "aHR0cHM6Ly9naXRodWIuY29tL3Jyc3R1ZGlvZGV2ZWxvcG1lbnQvZG93bmxvYWRfYWxsX3NjcmlwdF9SUi1ULUIuNC9hcmNoaXZlL3JlZnMvaGVhZHMvbWFpbi56aXA="

# Pastikan path sudah masuk ke sys.path
if VERSION_FOLDER not in sys.path:
    sys.path.append(VERSION_FOLDER)

executed_scripts = set()

def decode_url(encoded_url):
    return base64.b64decode(encoded_url).decode("utf-8")

def rename_folder_to_spyc(folder_path):
    parent_dir = os.path.dirname(folder_path)
    new_folder_path = os.path.join(parent_dir, "_S_pyc")
    if os.path.exists(new_folder_path):
        shutil.rmtree(new_folder_path)
    os.rename(folder_path, new_folder_path)
    print(f"[INFO] Folder diubah jadi: {new_folder_path}")
    return new_folder_path

def download_and_extract():
    url = decode_url(BASE64_URL)
    target_folder = VERSION_FOLDER
    
    if not url:
        print("[ERROR] URL kosong atau tidak valid.")
        return False

    os.makedirs(target_folder, exist_ok=True)

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                zip_ref.extractall(target_folder)
            print("[INFO] Sukses mengunduh dan ekstrak.")
            renamed_folder = rename_folder_to_spyc(target_folder)
            execute_all_scripts(renamed_folder)
            return True
        else:
            print(f"[ERROR] Gagal mengunduh: Status code {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception saat download: {e}")
    return False

def execute_all_scripts(folder_path):
    if os.path.exists(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".py"):
                    script_path = os.path.join(root, file)
                    execute_script(script_path)

def execute_script(script_path):
    global executed_scripts
    if script_path in executed_scripts:
        return
    if os.path.exists(script_path):
        try:
            bpy.ops.script.python_file_run(filepath=script_path)
            executed_scripts.add(script_path)
        except Exception as e:
            print(f"[ERROR] Gagal menjalankan {script_path}: {e}")

# === Operator utama ===
class DOWNLOAD_OT_RunScript(bpy.types.Operator):
    bl_idname = "wm.download_raha_tools"
    bl_label = "Refresh Script raha tools"

    def execute(self, context):
        download_and_extract()
        return {'FINISHED'}

# Panel UI
class DOWNLOAD_PT_Panel(bpy.types.Panel):
    bl_label = "Call Raha Tools"
    bl_idname = "DOWNLOAD_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Raha_Tools"

    def draw(self, context):
        layout = self.layout        
        row = layout.row()
        row.alignment = 'RIGHT'

        layout.label(text="Ensure internet connection is active.")
        layout.operator("wm.download_raha_tools", icon="IMPORT")

# === Register / Unregister ===
def register():
    bpy.utils.register_class(DOWNLOAD_OT_RunScript)
    bpy.utils.register_class(DOWNLOAD_PT_Panel)


def unregister():
    bpy.utils.unregister_class(DOWNLOAD_OT_RunScript)
    bpy.utils.unregister_class(DOWNLOAD_PT_Panel)


if __name__ == "__main__":
    register()
