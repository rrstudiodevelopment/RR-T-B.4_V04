
#    "name": "Bone Custom Properties UI",


import bpy

class RegisteredBone(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Bone Name")

class BoneCustomPropertiesPanel(bpy.types.Panel):
    bl_label = "Show Bone Custom Properties UI"
    bl_idname = "OBJECT_PT_bone_custom_props"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Raha_Tools"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        scene = context.scene

        if obj and obj.type == 'ARMATURE':
            box = layout.box()
            box.prop(scene, "only_registered_bones", text="Show Only Registered Bones")

            if scene.only_registered_bones:
                # Registered bones list management
                row = box.row()
                row.template_list(
                    "UI_UL_registered_bones_list", 
                    "Registered Bones", 
                    scene, "registered_bones", 
                    scene, "registered_bones_index"
                )
                
                col = row.column(align=True)
                col.operator("scene.register_selected_bones", icon='ADD', text="")                
#                col.operator("scene.add_registered_bone", icon='ADD', text="")
                col.operator("scene.remove_registered_bone", icon='REMOVE', text="")
#                col.operator("scene.register_selected_bones", icon='ADD', text="")
                
                box.prop(scene, "pin_bones", text="Show Selected Bones Alongside Registered")
                
                # Display custom properties for registered bones
                for registered_bone in scene.registered_bones:
                    bone = obj.pose.bones.get(registered_bone.name)
                    if bone:
                        self.draw_bone_properties(box, bone)
                    else:
                        box.label(text=f"{registered_bone.name} (Not found in armature)", icon='ERROR')

                # Display pinned selected bones if enabled
                if scene.pin_bones and context.selected_pose_bones:
                    for bone in context.selected_pose_bones:
                        if bone.name not in [rb.name for rb in scene.registered_bones]:
                            self.draw_bone_properties(box, bone)
            else:
                # Display custom properties for selected bones only
                if context.selected_pose_bones:
                    for bone in context.selected_pose_bones:
                        self.draw_bone_properties(box, bone)
                else:
                    box.label(text='Select bone(s) in Pose Mode', icon='INFO')
        else:
            layout.label(text="Select an armature object.", icon='ERROR')

    def draw_bone_properties(self, layout, bone):
        """Helper function to draw custom properties for a bone"""
        has_props = False
        
        # First check if bone has any displayable custom properties
        for prop_name in bone.keys():
            if not prop_name.startswith('_'):
                has_props = True
                break
        
        if has_props:
            layout.label(text=bone.name, icon='BONE_DATA')
            for prop_name, value in bone.items():
                if not prop_name.startswith('_'):
                    row = layout.row()
                    if isinstance(value, (int, float)):
                        row.prop(bone, f'["{prop_name}"]', text=prop_name, slider=True)
                    else:
                        row.prop(bone, f'["{prop_name}"]', text=prop_name)
        else:
            layout.label(text=f"{bone.name} (No custom properties)", icon='BONE_DATA')

class AddRegisteredBone(bpy.types.Operator):
    bl_idname = "scene.add_registered_bone"
    bl_label = "Add Registered Bone"
    bl_description = "Add a new bone to the registered bones list"

    def execute(self, context):
        new_bone = context.scene.registered_bones.add()
        new_bone.name = "NewBone"
        context.scene.registered_bones_index = len(context.scene.registered_bones) - 1
        return {'FINISHED'}

class RemoveRegisteredBone(bpy.types.Operator):
    bl_idname = "scene.remove_registered_bone"
    bl_label = "Remove Registered Bone"
    bl_description = "Remove the selected bone from the registered bones list"

    def execute(self, context):
        scene = context.scene
        if scene.registered_bones:
            scene.registered_bones.remove(scene.registered_bones_index)
            scene.registered_bones_index = min(scene.registered_bones_index, len(scene.registered_bones) - 1)
        return {'FINISHED'}

class RegisterSelectedBones(bpy.types.Operator):
    bl_idname = "scene.register_selected_bones"
    bl_label = "Register Selected Bones"
    bl_description = "Add currently selected bones to the registered bones list"

    def execute(self, context):
        if context.selected_pose_bones:
            for bone in context.selected_pose_bones:
                # Check if bone is already registered
                if bone.name not in [rb.name for rb in context.scene.registered_bones]:
                    new_bone = context.scene.registered_bones.add()
                    new_bone.name = bone.name
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No bones selected in Pose Mode")
            return {'CANCELLED'}

class UI_UL_registered_bones_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index, flt_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='BONE_DATA')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.name, icon='BONE_DATA')

def register():
    bpy.utils.register_class(RegisteredBone)
    bpy.utils.register_class(BoneCustomPropertiesPanel)
    bpy.utils.register_class(AddRegisteredBone)
    bpy.utils.register_class(RemoveRegisteredBone)
    bpy.utils.register_class(RegisterSelectedBones)
    bpy.utils.register_class(UI_UL_registered_bones_list)
    
    # Scene properties
    bpy.types.Scene.registered_bones = bpy.props.CollectionProperty(type=RegisteredBone)
    bpy.types.Scene.registered_bones_index = bpy.props.IntProperty()
    bpy.types.Scene.only_registered_bones = bpy.props.BoolProperty(
        name="Only Registered Bones",
        description="Show custom properties only for registered bones",
        default=False
    )
    bpy.types.Scene.pin_bones = bpy.props.BoolProperty(
        name="Pin Selected Bones",
        description="Show custom properties for selected bones alongside registered ones",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(RegisteredBone)
    bpy.utils.unregister_class(BoneCustomPropertiesPanel)
    bpy.utils.unregister_class(AddRegisteredBone)
    bpy.utils.unregister_class(RemoveRegisteredBone)
    bpy.utils.unregister_class(RegisterSelectedBones)
    bpy.utils.unregister_class(UI_UL_registered_bones_list)
    
    del bpy.types.Scene.registered_bones
    del bpy.types.Scene.registered_bones_index
    del bpy.types.Scene.only_registered_bones
    del bpy.types.Scene.pin_bones

if __name__ == "__main__":
    register()