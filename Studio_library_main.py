import bpy
import os
from bpy.props import StringProperty, EnumProperty
from bpy.utils import previews
import re

# Global variables
_icons = None
_video_paths = []
preview_collections = {}
# Function to load videos from a custom path
def load_videos_from_path(path):
    global _video_paths
    _video_paths.clear()
    
    if os.path.exists(path) and os.path.isdir(path):
        for file in os.listdir(path):
            if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.png')):
                _video_paths.append((file, file, "", load_preview_icon(os.path.join(path, file))))

# Function to load a preview icon
def load_preview_icon(path):
    global _icons
    if not path in _icons:
        if os.path.exists(path):
            _icons.load(path, path, "IMAGE")
        else:
            return 0
    return _icons[path].icon_id

# Enum property for the videos
def sna_videos_enum_items(self, context):
    return [(item[0], item[1], item[2], item[3], i) for i, item in enumerate(_video_paths)]

# Update function for the custom path property
def sna_update_custom_path(self, context):
    custom_path = bpy.context.scene.sna_custom_path
    load_videos_from_path(custom_path)
    
    # Update info saat file dipilih
    if context.scene.sna_videos:
        context.scene.sna_selected_info = context.scene.sna_videos
    else:
        context.scene.sna_selected_info = "No file selected"

# Operator to select bones from the script
class WM_OT_SelectBonesFromScript(bpy.types.Operator):
    bl_idname = "wm.select_bones_from_script"
    bl_label = "Select Bones from Script"
    bl_description = "Select bones listed in the imported script"
    
    def execute(self, context):
        selected_video = context.scene.sna_videos
        custom_path = context.scene.sna_custom_path
        video_name = os.path.splitext(selected_video)[0]
        
        # Path to ANIM_DATA folder
        anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
        
        # Path to DATA_POSE folder
        data_pose_dir = os.path.join(custom_path, "DATA_POSE")
        
        script_filepath = None
        
        # Check if ANIM_DATA folder exists and script is there
        if os.path.exists(anim_data_dir):
            temp_path = os.path.join(anim_data_dir, f"{video_name}.py")
            if os.path.exists(temp_path):
                script_filepath = temp_path
                self.report({'INFO'}, f"Script found in ANIM_DATA folder.")
        
        # If not found in ANIM_DATA, check DATA_POSE
        if script_filepath is None and os.path.exists(data_pose_dir):
            temp_path = os.path.join(data_pose_dir, f"{video_name}.py")
            if os.path.exists(temp_path):
                script_filepath = temp_path
                self.report({'INFO'}, f"Script found in DATA_POSE folder.")
        
        if script_filepath is None:
            self.report({'ERROR'}, f"Script file {video_name}.py not found in ANIM_DATA or DATA_POSE folders.")
            return {'CANCELLED'}
        
        # Read the script
        try:
            with open(script_filepath, 'r') as file:
                script_content = file.read()
            
            # Find bones in the script
            bone_names = re.findall(r"armature_obj\.pose\.bones\[\'([^\']+)\'\]", script_content)
            
            if not bone_names:
                self.report({'WARNING'}, "No bones found in the script.")
                return {'CANCELLED'}
            
            # Get the active armature
            armature_obj = context.active_object
            if not armature_obj or armature_obj.type != 'ARMATURE':
                self.report({'ERROR'}, "No active armature found.")
                return {'CANCELLED'}
            
            # Select the bones
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='DESELECT')
            
            selected_bones_count = 0
            for bone_name in bone_names:
                if bone_name in armature_obj.pose.bones:
                    armature_obj.pose.bones[bone_name].bone.select = True
                    selected_bones_count +=1
                    self.report({'INFO'}, f"Bone '{bone_name}' selected.")
                else:
                    self.report({'WARNING'}, f"Bone '{bone_name}' not found in armature.")
            if selected_bones_count == 0:
                self.report({'WARNING'}, "None of the bones in the script were found in armature.")
                return {'CANCELLED'}
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error reading script: {e}")
            return {'CANCELLED'}

# Operator to play the selected video
class WM_OT_PlayVideo(bpy.types.Operator):
    bl_idname = "wm.play_video"
    bl_label = "Play Video"
    bl_description = "Preview"

    def execute(self, context):
        selected_file = context.scene.sna_videos
        custom_path = context.scene.sna_custom_path
        file_path = os.path.join(custom_path, selected_file)

        # Check if the selected file is a video
        if selected_file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            if os.name == 'nt':
                os.startfile(file_path)
            else:
                self.report({'ERROR'}, "This addon only works on Windows.")
            return {'FINISHED'}

        # Check if the selected file is an image
        elif selected_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            preview_folder = os.path.join(custom_path, 'preview')
            if os.path.exists(preview_folder):
                video_name = os.path.splitext(selected_file)[0]  # Remove the image extension
                for video_ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    video_path = os.path.join(preview_folder, video_name + video_ext)
                    if os.path.exists(video_path):
                        if os.name == 'nt':
                            os.startfile(video_path)
                        else:
                            self.report({'ERROR'}, "This addon only works on Windows.")
                        return {'FINISHED'}

                self.report({'WARNING'}, f"No video found in 'preview' folder with the name '{video_name}'.")
            else:
                self.report({'WARNING'}, "No 'preview' folder found.")
        else:
            self.report({'ERROR'}, "Selected file is neither a video nor an image.")

        return {'FINISHED'}
    
# Operator to import animation
class WM_OT_ImportAnimation(bpy.types.Operator):
    bl_idname = "wm.import_animation"
    bl_label = "Import Animation"
    bl_description = "Import animation data from the selected video or image's script"
    
    def execute(self, context):
        selected_file = context.scene.sna_videos  # Assuming this can be a video or image
        custom_path = context.scene.sna_custom_path
        
        # Extract the file name without extension
        file_name = os.path.splitext(selected_file)[0]
        
        # Path to ANIM_DATA folder
        anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
        
        # Path to DATA_POSE folder
        data_pose_dir = os.path.join(custom_path, "DATA_POSE")
        
        # Check if ANIM_DATA folder exists
        if not os.path.exists(anim_data_dir):
            self.report({'ERROR'}, f"ANIM_DATA folder not found in: {custom_path}")
            return {'CANCELLED'}
        
        # Path to script file in ANIM_DATA
        script_filepath = os.path.join(anim_data_dir, f"{file_name}.py")
        
        # If script file is not found in ANIM_DATA, check in DATA_POSE
        if not os.path.exists(script_filepath):
            script_filepath = os.path.join(data_pose_dir, f"{file_name}.py")
            if not os.path.exists(script_filepath):
                self.report({'ERROR'}, f"Script file {file_name}.py not found in ANIM_DATA or DATA_POSE folders.")
                return {'CANCELLED'}
        
        # Read and execute the script
        try:
            with open(script_filepath, 'r') as file:
                exec(file.read())
            self.report({'INFO'}, f"Animation data from {script_filepath} imported successfully.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing script: {e}")
            return {'CANCELLED'}    

# Operator to refresh the video list
class WM_OT_RefreshList(bpy.types.Operator):
    bl_idname = "wm.refresh_list"
    bl_label = "Refresh List"
    bl_description = "Refresh the list of videos in the selected folder"
    
    def execute(self, context):
        custom_path = context.scene.sna_custom_path
        
        if custom_path and os.path.isdir(custom_path):
            load_videos_from_path(custom_path)  # Reload videos from the custom path
            self.report({'INFO'}, "List refreshed.")
        else:
            self.report({'ERROR'}, "Invalid or no folder selected.")
        
        return {'FINISHED'}

# Operator to delete video
class WM_OT_DeleteVideo(bpy.types.Operator):
    bl_idname = "wm.delete_video"
    bl_label = "Delete"
    bl_description = "Delete the selected video and its corresponding script and pose data"
    
    def execute(self, context):
        selected_video = context.scene.sna_videos
        custom_path = context.scene.sna_custom_path
        video_path = os.path.join(custom_path, selected_video)
        video_name = os.path.splitext(selected_video)[0]
        
        # Paths to ANIM_DATA and data_pose folders
        anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
        data_pose_dir = os.path.join(custom_path, "DATA_POSE")
        
        # File paths
        script_filepath = os.path.join(anim_data_dir, f"{video_name}.py")
        pose_filepath = os.path.join(data_pose_dir, f"{video_name}.pose")
        
        # Delete the script file
        if os.path.exists(script_filepath):
            os.remove(script_filepath)
            self.report({'INFO'}, f"Deleted script: {script_filepath}")
        
        # Delete related pose files
        if os.path.exists(data_pose_dir):
            for file in os.listdir(data_pose_dir):
                if file.startswith(video_name):
                    os.remove(os.path.join(data_pose_dir, file))
                    self.report({'INFO'}, f"Deleted pose file: {file}")
        
        # Delete the video file
        if os.path.exists(video_path):
            os.remove(video_path)
            self.report({'INFO'}, f"Deleted video: {selected_video}")
        
        # Refresh the video list
        load_videos_from_path(custom_path)
        
        return {'FINISHED'}

# Operator to rename video
class WM_OT_RenameVideo(bpy.types.Operator):
    bl_idname = "wm.rename_video"
    bl_label = "Rename"
    bl_description = "Rename data"

    new_name: StringProperty(name="New Name", description="New name for the file (without extension)")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        selected_file = context.scene.sna_videos
        custom_path = context.scene.sna_custom_path
        file_path = os.path.join(custom_path, selected_file)
        file_name, file_ext = os.path.splitext(selected_file)

        # Validasi nama baru
        if not self.new_name:
            self.report({'ERROR'}, "New name cannot be empty.")
            return {'CANCELLED'}

        # Path baru untuk file utama
        new_file_path = os.path.join(custom_path, self.new_name + file_ext)

        # Rename file utama (video)
        if os.path.exists(file_path):
            try:
                os.rename(file_path, new_file_path)
                self.report({'INFO'}, f"Renamed {selected_file} to {self.new_name + file_ext}.")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to rename file: {e}")
                return {'CANCELLED'}
        else:
            self.report({'ERROR'}, f"File {selected_file} not found.")
            return {'CANCELLED'}

        # Rename script di ANIM_DATA
        anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
        old_script_path = os.path.join(anim_data_dir, f"{file_name}.py")
        new_script_path = os.path.join(anim_data_dir, f"{self.new_name}.py")

        if os.path.exists(old_script_path):
            try:
                os.rename(old_script_path, new_script_path)
                self.report({'INFO'}, f"Renamed script {file_name}.py to {self.new_name}.py.")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to rename script: {e}")

        # Rename file di folder DATA_POSE
        data_pose_dir = os.path.join(custom_path, "DATA_POSE")
        if os.path.exists(data_pose_dir):
            for pose_file in os.listdir(data_pose_dir):
                if pose_file.startswith(file_name):
                    old_pose_path = os.path.join(data_pose_dir, pose_file)
                    new_pose_path = os.path.join(data_pose_dir, pose_file.replace(file_name, self.new_name))
                    try:
                        os.rename(old_pose_path, new_pose_path)
                        self.report({'INFO'}, f"Renamed pose file {pose_file}.")
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to rename pose file: {e}")

        # Rename file di folder preview
        preview_folder = os.path.join(custom_path, "preview")
        if os.path.exists(preview_folder):
            for preview_file in os.listdir(preview_folder):
                if preview_file.startswith(file_name):
                    old_preview_path = os.path.join(preview_folder, preview_file)
                    new_preview_path = os.path.join(preview_folder, preview_file.replace(file_name, self.new_name))
                    try:
                        os.rename(old_preview_path, new_preview_path)
                        self.report({'INFO'}, f"Renamed preview file {preview_file}.")
                    except Exception as e:
                        self.report({'ERROR'}, f"Failed to rename preview file: {e}")

        # Refresh list
        load_videos_from_path(custom_path)

        return {'FINISHED'}

# Operator to open export animation panel
class FLOATING_OT_Open_Export_Animation(bpy.types.Operator):
    bl_idname = "floating.open_export_animation"
    bl_label = "Open_import_Animation"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_bone_keyframe", keep_open=True)  # Memanggil panel dari script kedua
        return {'FINISHED'}  

# Panel class
class VIDEO_PT_Browser(bpy.types.Panel):
    bl_label = "Import Animation"
    bl_idname = "VIDEO_PT_Browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Animation - pose Library")
        layout.prop(context.scene, 'sna_custom_path', text="Folder")

        layout.template_icon_view(context.scene, 'sna_videos', show_labels=True, scale=5.0, scale_popup=5.0)

        # Tampilkan nama file yang terpilih (tanpa ekstensi)
        if context.scene.sna_videos:
            file_name, file_ext = os.path.splitext(context.scene.sna_videos)  # Pisahkan nama file dan ekstensi
            layout.label(text=f"File: {file_name}")  # Tampilkan hanya nama file
        else:
            layout.label(text="No file selected")

        row = layout.row()
        row.operator("wm.refresh_list", text="", icon='FILE_REFRESH')
        row.operator("wm.select_bones_from_script", text="Selected")
        row.operator("wm.delete_video", text="", icon='TRASH')
        row = layout.row()
        row.operator("wm.play_video", text="Preview", icon='PLAY')
        row.operator("wm.import_animation", text="Import")
        row = layout.row()
        row.operator("floating.open_export_animation", text="Export")
        row.operator("wm.rename_video", text="Rename", icon='SORTALPHA')

        layout.separator()
        # Jika checkbox dicentang, tampilkan tombol Tween Machine
        # Checkbox untuk menampilkan Tween Machine
        layout.prop(context.scene, "show_precentage_value_pose", text="show precentage value pose") #Perbaikan di sini

        # Jika checkbox dicentang, tampilkan tombol Tween Machine
        if context.scene.show_precentage_value_pose:
            layout.label(text="value pose")
            row = layout.row()
            row.prop(context.scene, "percentage_value", text="Percentage (%)")
            row = layout.row()
            row.operator("pose.apply_percentage", text="Apply Percentage")
            row = layout.row()

            row = layout.row()
            row.prop(context.scene, "calc_location", text="Location")
            row.prop(context.scene, "calc_rotation", text="Rotation")
            row.prop(context.scene, "calc_scale", text="Scale")
            row.prop(context.scene, "calc_custom_property", text="Custom Properties")
            layout.operator("object.flip_pose", text="Flip Pose")
            
# Register function
def register():
    global _icons
    _icons = previews.new()
    
    bpy.types.Scene.sna_custom_path = StringProperty(
        name="Custom Path",
        description="Path to the folder containing videos",
        default="",
        subtype='DIR_PATH',
        update=sna_update_custom_path
    )
    
    bpy.types.Scene.sna_videos = EnumProperty(
        name="Videos",
        description="List of videos in the selected folder",
        items=sna_videos_enum_items
    )

    # Tambahkan property untuk menyimpan info
    bpy.types.Scene.sna_selected_info = StringProperty(
        name="Selected Info",
        description="Information about the selected video or image",
        default=""
    )

    global preview_collections
    bpy.types.Scene.show_precentage_value_pose = bpy.props.BoolProperty(
        name="Show Precentage value pose", 
        description="Tampilkan tombol Tween Machine", 
        default=False
    )

    bpy.utils.register_class(FLOATING_OT_Open_Export_Animation) 
    bpy.utils.register_class(WM_OT_SelectBonesFromScript)
    bpy.utils.register_class(WM_OT_ImportAnimation) 
    bpy.utils.register_class(WM_OT_RenameVideo)   
    bpy.utils.register_class(WM_OT_PlayVideo)
    bpy.utils.register_class(WM_OT_DeleteVideo)
    bpy.utils.register_class(VIDEO_PT_Browser)
    bpy.utils.register_class(WM_OT_RefreshList)

  
# Unregister function
def unregister():
    global _icons
    previews.remove(_icons)
    
    del bpy.types.Scene.sna_custom_path
    del bpy.types.Scene.sna_videos
    del bpy.types.Scene.sna_selected_info  # Hapus property info

    bpy.utils.unregister_class(FLOATING_OT_Open_Export_Animation) 
    bpy.utils.unregister_class(WM_OT_SelectBonesFromScript)
    bpy.utils.unregister_class(WM_OT_ImportAnimation)    
    bpy.utils.unregister_class(WM_OT_RenameVideo)    
    bpy.utils.unregister_class(VIDEO_PT_Browser)
    bpy.utils.unregister_class(WM_OT_DeleteVideo)
    bpy.utils.unregister_class(WM_OT_PlayVideo)
    bpy.utils.unregister_class(WM_OT_RefreshList)    

if __name__ == "__main__":
    register()