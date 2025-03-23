import bpy
import os

class ANIMExportSuccessPopup(bpy.types.Operator):
    bl_idname = "wm.export_success_popup"
    bl_label = "Export Pose Sukses"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Export Pose Sukses!", icon='INFO')

#================================ DEF insert_missing_keyframes_pose =============================
def insert_missing_keyframes_pose():
    obj = bpy.context.active_object

    # Pastikan objek adalah Armature dan dalam Pose Mode
    if obj is None or obj.type != 'ARMATURE' or obj.mode != 'POSE':
        print("Pilih objek Armature dalam Pose Mode.")
        return
    
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        print("Objek tidak memiliki action (data animasi).")
        return
    
    current_frame = bpy.context.scene.frame_current  # Ambil frame saat ini

    # Ambil semua keyframe yang ada pada action
    keyframes = set()  # Set untuk menyimpan frame-frame unik
    for fcurve in action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframes.add(int(keyframe.co.x))  # Masukkan frame sebagai integer

    # Set frame saat ini
    bpy.context.scene.frame_set(current_frame)

    # Iterasi setiap bone yang dipilih
    for bone in obj.pose.bones:
        keyframe_status_euler = [False, False, False]  # Status keyframe untuk Rotation Euler (X, Y, Z)
        keyframe_status_quat = [False, False, False, False]  # Status keyframe untuk Quaternion (W, X, Y, Z)
        keyframe_status_loc = [False, False, False]  # Status keyframe untuk Location (X, Y, Z)
        keyframe_status_scale = [False, False, False]  # Status keyframe untuk Scale (X, Y, Z)

        # Periksa keyframe hanya pada frame saat ini
        for fcurve in action.fcurves:
            if fcurve.data_path == f'pose.bones["{bone.name}"].rotation_euler':
                for keyframe in fcurve.keyframe_points:
                    if int(keyframe.co.x) == current_frame:
                        keyframe_status_euler[fcurve.array_index] = True

            elif fcurve.data_path == f'pose.bones["{bone.name}"].rotation_quaternion':
                for keyframe in fcurve.keyframe_points:
                    if int(keyframe.co.x) == current_frame:
                        keyframe_status_quat[fcurve.array_index] = True

            elif fcurve.data_path == f'pose.bones["{bone.name}"].location':
                for keyframe in fcurve.keyframe_points:
                    if int(keyframe.co.x) == current_frame:
                        keyframe_status_loc[fcurve.array_index] = True

            elif fcurve.data_path == f'pose.bones["{bone.name}"].scale':
                for keyframe in fcurve.keyframe_points:
                    if int(keyframe.co.x) == current_frame:
                        keyframe_status_scale[fcurve.array_index] = True

        # Hitung jumlah sumbu yang memiliki keyframe
        keyframe_count_euler = sum(keyframe_status_euler)
        keyframe_count_quat = sum(keyframe_status_quat)
        keyframe_count_loc = sum(keyframe_status_loc)
        keyframe_count_scale = sum(keyframe_status_scale)

        # Tambahkan keyframe yang hilang jika hanya sebagian ada
        if 0 < keyframe_count_euler < 3:
            if not keyframe_status_euler[0]: bone.keyframe_insert(data_path="rotation_euler", index=0)  # X
            if not keyframe_status_euler[1]: bone.keyframe_insert(data_path="rotation_euler", index=1)  # Y
            if not keyframe_status_euler[2]: bone.keyframe_insert(data_path="rotation_euler", index=2)  # Z
            print(f"Keyframe rotation_euler ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

        if 0 < keyframe_count_loc < 3:
            if not keyframe_status_loc[0]: bone.keyframe_insert(data_path="location", index=0)  # X
            if not keyframe_status_loc[1]: bone.keyframe_insert(data_path="location", index=1)  # Y
            if not keyframe_status_loc[2]: bone.keyframe_insert(data_path="location", index=2)  # Z
            print(f"Keyframe location ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

        if 0 < keyframe_count_scale < 3:
            if not keyframe_status_scale[0]: bone.keyframe_insert(data_path="scale", index=0)  # X
            if not keyframe_status_scale[1]: bone.keyframe_insert(data_path="scale", index=1)  # Y
            if not keyframe_status_scale[2]: bone.keyframe_insert(data_path="scale", index=2)  # Z
            print(f"Keyframe scale ditambahkan untuk bone {bone.name} pada frame {current_frame}.")

#========================================= EKPORT BONE ================================================
def export_bone_keyframe_data_pose(context, filepath):
    armature_obj = context.object
    if not armature_obj or armature_obj.type != 'ARMATURE':
        return {'CANCELLED'}   
    
    # Jalankan fungsi insert_missing_keyframes_pose
    insert_missing_keyframes_pose()

    current_frame = context.scene.frame_current  # Ambil frame saat ini

    # Tentukan path folder ANIM_DATA dan Preview
    base_folder = os.path.dirname(filepath)
    anim_data_folder = os.path.join(base_folder, "DATA_POSE")
    preview_folder = os.path.join(base_folder, "Preview")

    # Pastikan folder ANIM_DATA dan Preview ada
    if not os.path.exists(anim_data_folder):
        os.makedirs(anim_data_folder)
    if not os.path.exists(preview_folder):
        os.makedirs(preview_folder)

    # Tentukan nama file dengan tambahan _pose
    file_name = os.path.splitext(os.path.basename(filepath))[0]
    if not file_name.endswith("_pose"):
        file_name += "_pose"

    script_path = os.path.join(anim_data_folder, f"{file_name}.py")
    playblast_path = os.path.join(preview_folder, f"{file_name}.mp4")
    screenshot_path = os.path.join(base_folder, f"{file_name}.png")

    # Mendapatkan data bone yang dipilih
    bone_data = {}
    for bone in armature_obj.pose.bones:
        if bone.bone.select:
            # Simpan transformasi bone
            bone_data[bone.name] = {
                "location": list(bone.location),
                "rotation_quaternion": list(bone.rotation_quaternion),
                "rotation_euler": list(bone.rotation_euler),
                "scale": list(bone.scale),
                "custom_properties": {},  # Dictionary untuk menyimpan custom properties
            }

            # Simpan custom properties
            for key, value in bone.items():
                if key not in ["_RNA_UI"]:  # Abaikan properti internal Blender
                    # Periksa apakah nilai dapat diserialisasi
                    if isinstance(value, (int, float, str, list, tuple)):
                        bone_data[bone.name]["custom_properties"][key] = value
                    else:
                        print(f"Properti {key} pada bone {bone.name} tidak dapat diserialisasi dan akan diabaikan.")

    if not bone_data:
        return {'CANCELLED'}

    # Menulis data ke file .py
    with open(script_path, 'w') as file:
        file.write("import bpy\n")
        file.write("import math\n\n")
        file.write("# Mendapatkan scene aktif\n")
        file.write("scene = bpy.context.scene\n\n")
        file.write("# Mendapatkan daftar tulang yang dipilih\n")
        file.write("selected_pose_bones = bpy.context.selected_pose_bones\n")
        file.write("if not selected_pose_bones:\n")  
        file.write("    print('Tidak ada tulang yang dipilih.')\n")  
        file.write("else:\n") 
        file.write("    armature_obj = selected_pose_bones[0].id_data\n")  
        file.write("    selected_bones = [bone.name for bone in selected_pose_bones]\n")                                  
        file.write("# Menyiapkan dictionary untuk menyimpan bone yang cocok\n")
        file.write("matched_bones = {}\n\n")

        for bone_name, data in bone_data.items():
            file.write(f"# Frame {current_frame}\n")
            file.write(f"if '{bone_name}' in selected_bones:\n")
            file.write(f"    bone = armature_obj.pose.bones['{bone_name}']\n")

            # Tulis data location
            location = data["location"]
            file.write(f"    bone.location = ({location[0]}, {location[1]}, {location[2]})\n")
            file.write(f"    bone.keyframe_insert(data_path='location')\n")

            # Tulis data rotation_quaternion
            rotation_quat = data["rotation_quaternion"]
            file.write(f"    bone.rotation_quaternion = ({rotation_quat[0]}, {rotation_quat[1]}, {rotation_quat[2]}, {rotation_quat[3]})\n")
            file.write(f"    bone.keyframe_insert(data_path='rotation_quaternion')\n")

            # Tulis data rotation_euler
            rotation_euler = data["rotation_euler"]
            file.write(f"    bone.rotation_euler = ({rotation_euler[0]}, {rotation_euler[1]}, {rotation_euler[2]})\n")
            file.write(f"    bone.keyframe_insert(data_path='rotation_euler')\n")

            # Tulis data scale
            scale = data["scale"]
            file.write(f"    bone.scale = ({scale[0]}, {scale[1]}, {scale[2]})\n")
            file.write(f"    bone.keyframe_insert(data_path='scale')\n")

            # Tulis custom properties
            custom_props = data["custom_properties"]
            if custom_props:
                file.write(f"    # Custom properties\n")
                for prop_name, prop_value in custom_props.items():
                    if isinstance(prop_value, (int, float)):
                        file.write(f"    bone['{prop_name}'] = {prop_value}\n")
                    elif isinstance(prop_value, str):
                        file.write(f"    bone['{prop_name}'] = '{prop_value}'\n")
                    elif isinstance(prop_value, (list, tuple)):
                        file.write(f"    bone['{prop_name}'] = {list(prop_value)}\n")
                    else:
                        print(f"Properti {prop_name} pada bone {bone_name} tidak dapat diserialisasi dan akan diabaikan.")

    # Simpan frame awal dan akhir untuk dikembalikan nanti
    original_start_frame = context.scene.frame_start
    original_end_frame = context.scene.frame_end

    # Set frame awal dan akhir ke frame saat ini
    context.scene.frame_start = current_frame
    context.scene.frame_end = current_frame

    # Playblast viewport dalam format MP4
    bpy.context.scene.render.filepath = playblast_path
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.audio_codec = 'AAC'
    bpy.ops.render.opengl(animation=True)  # Render playblast

    # Kembalikan frame awal dan akhir ke nilai aslinya
    context.scene.frame_start = original_start_frame
    context.scene.frame_end = original_end_frame

    # Ambil screenshot dari frame saat ini
    bpy.context.scene.frame_set(current_frame)  # Set frame ke frame saat ini
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = screenshot_path  # Set filepath untuk screenshot
    bpy.ops.render.opengl(write_still=True)  # Ambil screenshot

    # Tampilkan pop-up informasi sukses
    bpy.ops.wm.export_success_popup('INVOKE_DEFAULT')

    return {'FINISHED'}

#========================================= OPERATOR ANIMExportBoneKeyframeData_pose ===================
class ANIMExportBoneKeyframeData_pose(bpy.types.Operator):
    bl_idname = "object.export_bone_keyframe_data_pose"
    bl_label = "Export Bone Keyframe Data (Pose)"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        return export_bone_keyframe_data_pose(context, self.filepath)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#=============================================  Panel UI ====================================


#=============================================  Register ====================================
def register():
    bpy.utils.register_class(ANIMExportBoneKeyframeData_pose)
    bpy.utils.register_class(ANIMExportSuccessPopup)
    
def unregister():
    bpy.utils.unregister_class(ANIMExportBoneKeyframeData_pose)
    bpy.utils.unregister_class(ANIMExportSuccessPopup)
    
if __name__ == "__main__":
    register()