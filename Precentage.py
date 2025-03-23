import os
import ast  # Tambahkan ini
import bpy
from bpy.types import Operator

import bpy
import json
import os
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import Operator, Panel
from bpy.utils import previews

# Global variables for image previews
_icons = None
_image_paths = []

def flip_selected_pose(context):
    # Ensure we're in Pose Mode and an armature is selected
    if context.object is None or context.object.type != 'ARMATURE' or context.object.mode != 'POSE':
        return

    # Copy the current pose
    bpy.ops.pose.copy()

    # Paste the pose with flipping enabled
    bpy.ops.pose.paste(flipped=True)

class ApplyPercentageOperator(bpy.types.Operator):
    bl_idname = "pose.apply_percentage"
    bl_label = "Apply Percentage to Bones"
    
    def execute(self, context):
        armature = context.object
        
        # Pastikan objek adalah armature
        if armature.type != 'ARMATURE':
            self.report({'WARNING'}, "Selected object is not an armature")
            return {'CANCELLED'}
        
        percentage = context.scene.percentage_value / 100  # Konversi persentase menjadi rasio
        calc_location = context.scene.calc_location
        calc_rotation = context.scene.calc_rotation
        calc_scale = context.scene.calc_scale
        calc_custom_property = context.scene.calc_custom_property
        
        # Iterasi setiap bone yang terseleksi
        for bone in armature.pose.bones:
            if bone.bone.select:
                # Kalkulasi dan modifikasi data asli bone (bukan data objek)
                
                if calc_location:
                    # Lokasi bone (transformasi relatif)
                    bone.location.x *= percentage
                    bone.location.y *= percentage
                    bone.location.z *= percentage

                if calc_rotation:
                    # Rotasi bone (Euler)
                    bone.rotation_euler.x *= percentage
                    bone.rotation_euler.y *= percentage
                    bone.rotation_euler.z *= percentage

                    # Rotasi bone (Quaternion)
                    bone.rotation_quaternion.x *= percentage
                    bone.rotation_quaternion.y *= percentage
                    bone.rotation_quaternion.z *= percentage
                    bone.rotation_quaternion.w *= percentage

                if calc_scale:
                    # Skala bone
                    bone.scale.x *= percentage
                    bone.scale.y *= percentage
                    bone.scale.z *= percentage

                if calc_custom_property:
                    # Kalkulasi custom property jika ada
                    for prop_name in bone.keys():
                        if prop_name != "_RNA_UI":  # Menghindari modifikasi metadata internal
                            current_value = bone[prop_name]
                            bone[prop_name] = current_value * percentage
        
        # Set keyframe sesuai dengan kategori yang dipilih
        bpy.ops.anim.keyframe_insert_by_name(type="LocRotScaleCProp")
        
        return {'FINISHED'}

#========================================================================================    


class OBJECT_OT_FlipPoseOperator(bpy.types.Operator):
    """Flip the current pose"""
    bl_idname = "object.flip_pose"
    bl_label = "Flip Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Ensure an armature is selected and we're in Pose Mode
        if context.object is None or context.object.type != 'ARMATURE' or context.object.mode != 'POSE':
            self.report({'WARNING'}, "Flip Pose failed. Ensure an armature is selected and you're in Pose Mode.")
            return {'CANCELLED'}
        
        # Call the flip_selected_pose function
        flip_selected_pose(context)
        return {'FINISHED'}
#=====================================================================================================
             

#=====================================================================================================

def register():
    global _icons
    _icons = previews.new()


        

    bpy.utils.register_class(OBJECT_OT_FlipPoseOperator)    


    bpy.utils.register_class(ApplyPercentageOperator)

    
    # Menambahkan properti untuk persen
    bpy.types.Scene.percentage_value = bpy.props.FloatProperty(name="Percentage", default=50)
    
    # Menambahkan properti untuk checkbox
    bpy.types.Scene.calc_location = bpy.props.BoolProperty(name="Location", default=True)
    bpy.types.Scene.calc_rotation = bpy.props.BoolProperty(name="Rotation", default=True)
    bpy.types.Scene.calc_scale = bpy.props.BoolProperty(name="Scale", default=False)
    bpy.types.Scene.calc_custom_property = bpy.props.BoolProperty(name="Custom Properties", default=False)    
    bpy.types.Scene.set_keyframes = BoolProperty(name="Set Keyframes")
    
    # Properties


def unregister():
    global _icons
    previews.remove(_icons)

    bpy.utils.unregister_class(OBJECT_OT_FlipPoseOperator)      

    bpy.utils.unregister_class(ApplyPercentageOperator)

    
    del bpy.types.Scene.script_folder_path
    del bpy.types.Scene.set_keyframes
    del bpy.types.Scene.percentage_value
    del bpy.types.Scene.calc_location
    del bpy.types.Scene.calc_rotation
    del bpy.types.Scene.calc_scale
    del bpy.types.Scene.calc_custom_property
    del bpy.types.Scene.sna_custom_path
    del bpy.types.Scene.sna_images

if __name__ == "__main__":
    register()