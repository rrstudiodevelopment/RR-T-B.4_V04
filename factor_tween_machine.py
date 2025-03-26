import bpy

def apply_pose_breakdowner(context, factor):
    obj = context.object
    if obj and obj.type == 'ARMATURE' and obj.mode == 'POSE':
        # Pertama update semua fcurves untuk keyframe yang ada
        for bone in context.selected_pose_bones:
            action = obj.animation_data.action
            if action:
                fcurves = action.fcurves
                for fcurve in fcurves:
                    if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]'):
                        # Cari keyframe sebelumnya dan berikutnya
                        prev_key, next_key = None, None
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.co[0] < context.scene.frame_current:
                                prev_key = keyframe
                            elif keyframe.co[0] > context.scene.frame_current:
                                next_key = keyframe
                                break

                        if prev_key and next_key:
                            prev_value = prev_key.co[1]
                            next_value = next_key.co[1]
                            
                            # Hitung nilai baru dengan ekstrapolasi
                            new_value = prev_value + (next_value - prev_value) * factor
                            
                            # Cari keyframe di frame saat ini
                            existing_key = None
                            for k in fcurve.keyframe_points:
                                if k.co[0] == context.scene.frame_current:
                                    existing_key = k
                                    break
                            
                            # Update atau insert keyframe
                            if existing_key:
                                existing_key.co[1] = new_value
                            else:
                                fcurve.keyframe_points.insert(
                                    context.scene.frame_current, 
                                    new_value, 
                                    options={'FAST'}
                                )
                            fcurve.update()
        
        # Kedua, update nilai pose bone secara langsung
        for bone in context.selected_pose_bones:
            # Dapatkan nilai property yang ingin diubah
            bone_paths = [
                'location', 'rotation_quaternion', 'rotation_euler', 
                'scale', 'rotation_axis_angle'
            ]
            
            for path in bone_paths:
                try:
                    # Cari fcurve untuk property ini
                    data_path = f'pose.bones["{bone.name}"].{path}'
                    fcurve = None
                    for fc in obj.animation_data.action.fcurves:
                        if fc.data_path == data_path:
                            fcurve = fc
                            break
                    
                    if fcurve:
                        # Evaluasi nilai di frame saat ini
                        value = fcurve.evaluate(context.scene.frame_current)
                        
                        # Terapkan ke bone
                        if path == 'location':
                            bone.location = value
                        elif path == 'rotation_quaternion':
                            bone.rotation_quaternion = value
                        elif path == 'rotation_euler':
                            bone.rotation_euler = value
                        elif path == 'scale':
                            bone.scale = value
                        elif path == 'rotation_axis_angle':
                            bone.rotation_axis_angle = value
                            
                except:
                    continue


class ApplyPoseBreakdownerOperator(bpy.types.Operator):
    """Apply Pose Breakdowner with unlimited extrapolation"""
    bl_idname = "pose.apply_breakdowner"
    bl_label = "Apply Breakdowner (Unlimited Range)"

    def execute(self, context):
        factor = context.scene.pose_breakdowner_factor
        apply_pose_breakdowner(context, factor)
        context.view_layer.update()
        return {'FINISHED'}

class ApplyPoseBreakdownerButtonOperator(bpy.types.Operator):
    """Apply Breakdowner with specific factor"""
    bl_idname = "pose.apply_breakdowner_button"
    bl_label = "Apply Breakdowner Button"
    
    factor: bpy.props.FloatProperty(default=0.0)

    @classmethod
    def description(cls, context, properties):
        return f" value factor {properties.factor:.2f}"
    
    def execute(self, context):
        # Perbaikan: Langsung terapkan faktor tanpa perlu klik dua kali
        context.scene.pose_breakdowner_factor = self.factor
        apply_pose_breakdowner(context, self.factor)
        context.view_layer.update()
        return {'FINISHED'}

class DUMMY_OT_button(bpy.types.Operator):
    bl_idname = "pose.dummy_button"
    bl_label = "Dummy Button"
    
    def execute(self, context):
        return {'CANCELLED'}  # Tidak melakukan apa pun



    
#class POSE_PT_breakdowner_panel(bpy.types.Panel):
#    bl_label = "Pose Breakdowner"
#    bl_idname = "POSE_PT_breakdowner_panel"
#    bl_space_type = 'VIEW_3D'
#    bl_region_type = 'UI'
#    bl_category = "Raha_Tools"
#    bl_context = "posemode"

#    def draw(self, context):
#        layout = self.layout
#        scene = context.scene
        
        # Slider utama
#        row = layout.row()
#        row.prop(scene, "pose_breakdowner_factor", slider=True)

#        layout.label(text="Tween Button")        
        # 10 tombol preset
#        box = layout.box()
#        row = box.row(align=True)

#        sub = row.row(align=True)
        
#        sub.operator("pose.apply_breakdowner_button", text="-1").factor = -1.0        
#        sub.operator("pose.apply_breakdowner_button", text="0").factor = 0.0
 #       sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.12
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.25
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.37
#        sub.operator("pose.apply_breakdowner_button", text="T").factor = 0.5        
        # Tombol 6-10 (nilai positif)
#        sub = row.row(align=True)
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.62
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.75
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = 0.87
#        sub.operator("pose.apply_breakdowner_button", text="100").factor = 1.0



#        layout.separator()
#        layout.label(text="OverShoot - +")
#        box = layout.box()
#        row = box.row(align=True)

#        sub = row.row(align=True)
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = -0.50
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = -0.30
#        sub.operator("pose.apply_breakdowner_button", text="-").factor = -0.10 
    
#        sub.operator("pose.dummy_button", text="  T  ")

       
#        sub.operator("pose.apply_breakdowner_button", text="+").factor = 1.10
#        sub.operator("pose.apply_breakdowner_button", text="+").factor = 1.30
#        sub.operator("pose.apply_breakdowner_button", text="+").factor = 1.50    

            
def register():
    bpy.types.Scene.pose_breakdowner_factor = bpy.props.FloatProperty(
        name="Extrapolation Factor",
        description="0.0=First Key, 1.0=Second Key, <0 or >1 for extrapolation",
        default=0.5,
        update=lambda self, context: bpy.ops.pose.apply_breakdowner()
    )
    
    bpy.utils.register_class(ApplyPoseBreakdownerOperator)
    bpy.utils.register_class(ApplyPoseBreakdownerButtonOperator)
#    bpy.utils.register_class(POSE_PT_breakdowner_panel)

    bpy.utils.register_class(DUMMY_OT_button)
def unregister():
    del bpy.types.Scene.pose_breakdowner_factor
    bpy.utils.unregister_class(ApplyPoseBreakdownerOperator)
    bpy.utils.unregister_class(ApplyPoseBreakdownerButtonOperator)
#    bpy.utils.unregister_class(POSE_PT_breakdowner_panel)

    bpy.utils.unregister_class(DUMMY_OT_button)
if __name__ == "__main__":
    register()