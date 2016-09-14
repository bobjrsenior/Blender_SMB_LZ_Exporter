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
    
    startPositionObjects = []
    numCollisionFields = 0;
    collisionFieldsOffset = 0
    collisionFields = []
    sizeOfHeader = 160
    falloutPlaneOffset = 0
    falloutPlaneY = 0
    numberOfGoals = 0
    goalsOffset = 0
    goalObjects = []
    numberOfBumpers = 0
    bumpersOffset = 0
    bumperObjects = []
    numberOfJamabars = 0
    jamabarOffset = 0
    jamabarObjects = []
    numberOfBananas = 0
    bananasOffset = 0
    bananaObjects = []
    numberOfLevelModels = 0
    levelModelsOffset = 0
    levelModelObjects = []
    numberOfBackgroundModels = 0
    backgroundModelsOffset = 0
    backgroundModelObjects = []
    numberOfReflectiveObjects = 0
    reflectiveObjectsOffset = 0
    reflectiveObjects = []
    
    filename_ext = ".lz"
    filter_glob = StringProperty(
            default="*.lz",
            options={'HIDDEN'},
            )


    def execute(self, context):        # execute() is called by blender when running the operator.

        # The original script
        scene = context.scene
        print(dir(scene.objects[0]))
        for obj in scene.objects:
            if "start" in obj.name.lower():
                self.startPositionObjects.append(obj)
            elif "goal" in obj.name.lower():
                self.goalObjects.append(obj)
            elif "bumper" in obj.name.lower():
                self.bumperObjects.append(obj)
            elif "jamabar" in obj.name.lower():
                self.jamabarObjects
            elif "banana" in obj.name.lower():
                self.bananaObjects.append(obj)
            elif "background" in obj.name.lower():
                self.backgroundModelObjects.append(obj)
            elif "reflective" in obj.name.lower():
                self.reflectiveObjects.append(obj)
            else:
                self.levelModelObjects.append(obj)
            
        #    obj.location.x += 1.0
        self.numberOfGoals = len(self.goalObjects)
        print(self.goalObjects)
        self.numberOfBumpers = len(self.bumperObjects)
        self.numberOfJamabars = len(self.jamabarObjects)
        self.numberOfBananas = len(self.bananaObjects)
        self.numberOfLevelModels = len(self.levelModelObjects)
        self.numberOfBackgroundModels = len(self.backgroundModelObjects)
        self.numberOfReflectiveObjects = len(self.reflectiveObjects)
        self.writeLZ()
        return {'FINISHED'}            # this lets blender know the operator finished successfully.
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def writeLZ(self):
        """Save an SMB LZ File"""
        with open(self.filepath, 'wb') as file:
            self.writeStartPositions(file)
            self.writeHeader(file)
    
    def writeZeroBytes(self, file, numZeros):
        byteArray = []
        for i in range(0, numZeros):
            byteArray.append(0)
        file.write(bytes(byteArray))
            
    def writeHeader(self, file):
        file.seek(0, 0)
        self.writeZeroBytes(file, 8)
        file.write(self.toBigI(self.numCollisionFields))
        file.write(self.toBigI(self.collisionFieldsOffset))
        file.write(self.toBigI(160))
        file.write(self.toBigI(self.falloutPlaneOffset))
        file.write(self.toBigI(self.numberOfGoals))
        file.write(self.toBigI(self.goalsOffset))
        file.write(self.toBigI(self.numberOfGoals));
        self.writeZeroBytes(file, 4)
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
        
    def writeStartPositions(self, file):
        file.seek(self.sizeOfHeader, 0)
        for obj in self.startPositionObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.y))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toShortI(obj.rotation_euler.x))
            file.write(self.toShortI(obj.rotation_euler.y))
            file.write(self.toShortI(obj.rotation_euler.z))
            self.writeZeroBytes(file, 1)
        self.goalsOffset = file.tell()
        
        

            
    def toBigI(self, number):
        return struct.pack('>I', number)
        
    def toBigF(self, number):
        return struct.pack('>f', number)
        
    def toShortI(self, number):
        return struct.pack('>H', int(number) & 0xFFFF)
            


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
    
    