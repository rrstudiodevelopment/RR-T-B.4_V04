import bpy
import os
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.utils import previews
import re
import sys
import ctypes.wintypes

# Global variables
_icons = None
_video_paths = []
preview_collections = {}

def normalize_path(path):
    """Convert any path to absolute, normalized path"""
    if not path:
        return ""
    
    # Expand environment variables and user paths
    path = os.path.expandvars(os.path.expanduser(path))
    
    # Handle Windows special folders
    if sys.platform == 'win32':
        try:
            folder_map = {
                'desktop': 0,
                'documents': 5,
                'pictures': 39,
                'videos': 14,
                'music': 13,
                'downloads': 40
            }
            
            lower_path = path.lower().strip()
            
            if lower_path in folder_map:
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(0, folder_map[lower_path], 0, 0, buf)
                return buf.value
                
            for folder_name, csidl in folder_map.items():
                if lower_path.startswith((folder_name + '\\', folder_name + '/')):
                    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                    ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, buf)
                    remaining_path = path[len(folder_name):].lstrip('\\/')
                    return os.path.join(buf.value, remaining_path)
        except Exception as e:
            print(f"Path normalization error: {e}")
    
    return os.path.abspath(os.path.normpath(path))

def load_videos_from_path(path):
    global _video_paths
    _video_paths.clear()
    
    try:
        norm_path = normalize_path(path)
        if os.path.isdir(norm_path):
            for file in os.listdir(norm_path):
                if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.png', '.jpg', '.jpeg')):
                    full_path = os.path.join(norm_path, file)
                    _video_paths.append((file, file, "", load_preview_icon(full_path)))
    except Exception as e:
        print(f"Error loading videos: {e}")

def load_preview_icon(path):
    global _icons
    try:
        norm_path = normalize_path(path)
        if norm_path not in _icons:
            if os.path.exists(norm_path):
                _icons.load(norm_path, norm_path, "IMAGE")
            else:
                return 0
        return _icons[norm_path].icon_id
    except Exception as e:
        print(f"Error loading icon: {e}")
        return 0

def sna_videos_enum_items(self, context):
    return [(item[0], item[1], item[2], item[3], i) for i, item in enumerate(_video_paths)]

def sna_update_custom_path(self, context):
    try:
        custom_path = normalize_path(bpy.context.scene.sna_custom_path)
        load_videos_from_path(custom_path)
        if context.scene.sna_videos:
            context.scene.sna_selected_info = context.scene.sna_videos
        else:
            context.scene.sna_selected_info = "No file selected"
    except Exception as e:
        print(f"Error updating path: {e}")

class WM_OT_SelectBonesFromScript(bpy.types.Operator):
    bl_idname = "wm.select_bones_from_script"
    bl_label = "Select Bones from Script"
    
    def execute(self, context):
        try:
            selected_video = context.scene.sna_videos
            custom_path = normalize_path(context.scene.sna_custom_path)
            video_name = os.path.splitext(selected_video)[0]
            
            anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
            data_pose_dir = os.path.join(custom_path, "DATA_POSE")
            
            script_path = None
            for folder in [anim_data_dir, data_pose_dir]:
                if os.path.exists(folder):
                    temp_path = os.path.join(folder, f"{video_name}.py")
                    if os.path.exists(temp_path):
                        script_path = temp_path
                        break
            
            if not script_path:
                self.report({'ERROR'}, "Script not found!")
                return {'CANCELLED'}
            
            with open(script_path, 'r') as f:
                content = f.read()
            
            bone_names = re.findall(r"armature_obj\.pose\.bones\[\'([^\']+)\'\]", content)
            if not bone_names:
                self.report({'WARNING'}, "No bones found.")
                return {'CANCELLED'}
            
            armature = context.active_object
            if not armature or armature.type != 'ARMATURE':
                self.report({'ERROR'}, "No active armature!")
                return {'CANCELLED'}
            
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='DESELECT')
            
            selected = 0
            for bone in bone_names:
                if bone in armature.pose.bones:
                    armature.pose.bones[bone].bone.select = True
                    selected += 1
            
            self.report({'INFO'}, f"Selected {selected} bones.")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

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

class WM_OT_ImportAnimation(bpy.types.Operator):
    bl_idname = "wm.import_animation"
    bl_label = "Import Animation"
    
    def execute(self, context):
        try:
            selected = context.scene.sna_videos
            custom_path = normalize_path(context.scene.sna_custom_path)
            file_name = os.path.splitext(selected)[0]
            
            anim_data_dir = os.path.join(custom_path, "ANIM_DATA")
            data_pose_dir = os.path.join(custom_path, "DATA_POSE")
            
            script_path = None
            for folder in [anim_data_dir, data_pose_dir]:
                if os.path.exists(folder):
                    temp_path = os.path.join(folder, f"{file_name}.py")
                    if os.path.exists(temp_path):
                        script_path = temp_path
                        break
            
            if not script_path:
                self.report({'ERROR'}, "Script not found!")
                return {'CANCELLED'}
            
            with open(script_path, 'r') as f:
                exec(f.read())
            
            self.report({'INFO'}, "Animation imported!")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

class WM_OT_RefreshList(bpy.types.Operator):
    bl_idname = "wm.refresh_list"
    bl_label = "Refresh List"
    
    def execute(self, context):
        try:
            custom_path = normalize_path(context.scene.sna_custom_path)
            load_videos_from_path(custom_path)
            self.report({'INFO'}, "List refreshed!")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

class WM_OT_DeleteVideo(bpy.types.Operator):
    bl_idname = "wm.delete_video"
    bl_label = "Delete Video"
    
    def execute(self, context):
        try:
            selected = context.scene.sna_videos
            custom_path = normalize_path(context.scene.sna_custom_path)
            video_path = os.path.join(custom_path, selected)
            video_name = os.path.splitext(selected)[0]
            
            # Delete main file
            if os.path.exists(video_path):
                os.remove(video_path)
            
            # Delete related files
            for folder in ["ANIM_DATA", "DATA_POSE", "preview"]:
                target_dir = os.path.join(custom_path, folder)
                if os.path.exists(target_dir):
                    for file in os.listdir(target_dir):
                        if file.startswith(video_name):
                            os.remove(os.path.join(target_dir, file))
            
            load_videos_from_path(custom_path)
            self.report({'INFO'}, "Deleted successfully!")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

class WM_OT_RenameVideo(bpy.types.Operator):
    bl_idname = "wm.rename_video"
    bl_label = "Rename Video"
    
    new_name: StringProperty(name="New Name")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        try:
            selected = context.scene.sna_videos
            custom_path = normalize_path(context.scene.sna_custom_path)
            old_path = os.path.join(custom_path, selected)
            file_name, file_ext = os.path.splitext(selected)
            
            if not self.new_name:
                self.report({'ERROR'}, "New name cannot be empty!")
                return {'CANCELLED'}
            
            new_path = os.path.join(custom_path, self.new_name + file_ext)
            
            # Rename main file
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            
            # Rename related files
            for folder in ["ANIM_DATA", "DATA_POSE", "preview"]:
                target_dir = os.path.join(custom_path, folder)
                if os.path.exists(target_dir):
                    for file in os.listdir(target_dir):
                        if file.startswith(file_name):
                            old_file = os.path.join(target_dir, file)
                            new_file = os.path.join(target_dir, file.replace(file_name, self.new_name))
                            os.rename(old_file, new_file)
            
            load_videos_from_path(custom_path)
            self.report({'INFO'}, "Renamed successfully!")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}

class FLOATING_OT_Open_Export_Animation(bpy.types.Operator):
    bl_idname = "floating.open_export_animation"
    bl_label = "Open Export Panel"
    
    def execute(self, context):
        bpy.ops.wm.call_panel(name="OBJECT_PT_bone_keyframe", keep_open=True)
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

def register():
    global _icons
    _icons = previews.new()
    
    bpy.types.Scene.sna_custom_path = StringProperty(
        name="Custom Path",
        default="",
        subtype='DIR_PATH',
        update=sna_update_custom_path
    )
    
    bpy.types.Scene.sna_videos = EnumProperty(
        name="Videos",
        items=sna_videos_enum_items
    )
    
    bpy.types.Scene.sna_selected_info = StringProperty(
        name="Selected Info",
        default=""
    )
    
    bpy.types.Scene.show_precentage_value_pose = BoolProperty(
        name="Show Percentage Value Pose",
        default=False
    )
    
    classes = [
        WM_OT_SelectBonesFromScript,
        WM_OT_PlayVideo,
        WM_OT_ImportAnimation,
        WM_OT_RefreshList,
        WM_OT_DeleteVideo,
        WM_OT_RenameVideo,
        FLOATING_OT_Open_Export_Animation,
        VIDEO_PT_Browser
    ]
    
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global _icons
    previews.remove(_icons)
    
    classes = [
        WM_OT_SelectBonesFromScript,
        WM_OT_PlayVideo,
        WM_OT_ImportAnimation,
        WM_OT_RefreshList,
        WM_OT_DeleteVideo,
        WM_OT_RenameVideo,
        FLOATING_OT_Open_Export_Animation,
        VIDEO_PT_Browser
    ]
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.sna_custom_path
    del bpy.types.Scene.sna_videos
    del bpy.types.Scene.sna_selected_info
    del bpy.types.Scene.show_precentage_value_pose

if __name__ == "__main__":
    register()