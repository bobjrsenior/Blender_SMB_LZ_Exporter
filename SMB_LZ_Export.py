bl_info = {
    "name": "SMB LZ format",
    "category": "Import-Export",
    "description": "Exports to the SMB LZ format",
    "version": (0, 0, 1)}

import os    
import bpy
import mathutils
import bpy_extras.io_utils
import struct
from array import array

from bpy.props import (
        BoolProperty,
        FloatProperty,
        StringProperty,
        EnumProperty,
        )

class SMBLZExporter(bpy.types.Operator):
    """Export to an SMB LZ File"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "export_smb.lz"        # unique identifier for buttons and menu items to reference.
    bl_label = "Export SMB LZ"         # display name in the interface.
    bl_options = {'PRESET'}
    
    # the two files we want to select
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    
    numCollisionFields = 0;
    collisionFieldsOffset = 0
    sizeOfHeader = 160
    falloutPlaneOffset = 0
    falloutPlaneY = 0
    numberOfGoals = 0
    goalsOffset = 0
    numberOfBumpers = 0
    bumpersOffset = 0
    numberOfJamabars = 0
    jamabarOffset = 0
    numberOfBananas = 0
    bananasOffset = 0
    numberOfLevelModels = 0
    levelModelsOffset = 0
    numberOfBackgroundModels = 0
    backgroundModelsOffset = 0
    numberOfReflectiveObjects = 0
    reflectiveObjectsOffset = 0
    
    
    filename_ext = ".lz"
    filter_glob = StringProperty(
            default="*.lz",
            options={'HIDDEN'},
            )


    def execute(self, context):        # execute() is called by blender when running the operator.

        # The original script
        scene = context.scene
        #for obj in scene.objects:
        #    obj.location.x += 1.0
        self.writeLZ()
        return {'FINISHED'}            # this lets blender know the operator finished successfully.
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def writeZeroBytes(self, file, numZeros):
        byteArray = []
        for i in range(0, numZeros):
            byteArray.append(0)
        print(bytes(byteArray))
        file.write(bytes(byteArray))
            
    def writeHeader(self, file):
        self.writeZeroBytes(file, 8)
        file.write(self.toBigI(self.numCollisionFields))
        file.write(self.toBigI(self.collisionFieldsOffset))
        file.write(self.toBigI(160))
        file.write(self.toBigI(self.falloutPlaneOffset))
        file.write(self.toBigI(self.numberOfGoals))
        file.write(self.toBigI(self.goalsOffset))
        file.write(self.toBigI(self.numberOfGoals));
        self.writeZeroBytes(file, 1)
        file.write(self.toBigI(self.numberOfBumpers))
        file.write(self.toBigI(self.bumpersOffset))
        file.write(self.toBigI(self.numberOfJamabars))
        file.write(self.toBigI(self.jamabarOffset))
        file.write(self.toBigI(self.numberOfBananas))
        file.write(self.toBigI(self.bananasOffset))
        self.writeZeroBytes(file, 10)
        self.writeZeroBytes(file, 8)
        file.write(self.toBigI(self.numberOfLevelModels))
        file.write(self.toBigI(self.levelModelsOffset))
        self.writeZeroBytes(file, 8)
        file.write(self.toBigI(self.numberOfBackgroundModels))
        file.write(self.toBigI(self.backgroundModelsOffset))
        self.writeZeroBytes(file, 8)
        self.writeZeroBytes(file, 8)
        file.write(self.toBigI(self.numberOfReflectiveObjects))
        file.write(self.toBigI(self.reflectiveObjectsOffset))
        self.writeZeroBytes(file, 30)
        
            
    def writeLZ(self):
        """Save an SMB LZ File"""
        with open(self.filepath, 'wb') as file:
            self.writeHeader(file)
            
    def toBigI(self, number):
        return struct.pack('>I', number)
            


def menu_func_export(self, context):
    self.layout.operator(SMBLZExporter.bl_idname, text="SMB LZ (.lz)")


def register():
    bpy.utils.register_class(SMBLZExporter)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    


def unregister():
    bpy.utils.unregister_class(SMBLZExporter)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
    
    