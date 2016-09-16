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
    levelModelNameOffsets = []
    levelModelNamePointerOffsets = []
    levelModelAnimationFrameOffsets = []
    levelModelTriangleOffsets = []
    levelModelCollisionGridPointers = []
    numberOfLevelModelTriangles = []
    numberOfBackgroundModels = 0
    backgroundModelsOffset = 0
    backgroundModelObjects = []
    backgroundModelNameOffsets = []
    backgroundModelNamePointerOffsets = []
    backgroundModelAnimationFrameOffsets = []
    backgroundModelTriangleOffsets = []
    backgroundModelCollisionGridPointers = []
    numberOfBackgoundModelTriangles = []
    numberOfReflectiveObjects = 0
    reflectiveObjectsOffset = 0
    reflectiveObjects = []
    reflectiveObjectNameOffsets = []
    reflectiveObjectNamePointerOffsets = []
    reflectiveObjectAnimationFrameOffsets = []
    reflectiveObjectTriangleOffsets = []
    reflectiveObjectCollisionGridPointers = []
    numberOfReflectiveObjectTriangles = []
    modelNamesOffset = 0
    
    filename_ext = ".lz"
    filter_glob = StringProperty(
            default="*.lz",
            options={'HIDDEN'},
            )


    def execute(self, context):        # execute() is called by blender when running the operator.

        # The original script
        scene = context.scene
        #print(dir(scene.objects[0]))
        for obj in scene.objects:
            lowerName = obj.name.lower()
            if "start" in lowerName:
                self.startPositionObjects.append(obj)
            elif "goal" in lowerName:
                self.goalObjects.append(obj)
            elif "bumper" in lowerName:
                self.bumperObjects.append(obj)
            elif "jamabar" in lowerName:
                self.jamabarObjects.append(obj)
            elif "banana" in lowerName:
                self.bananaObjects.append(obj)
            elif "background" in lowerName:
                self.backgroundModelObjects.append(obj)
            elif "reflective" in lowerName:
                self.reflectiveObjects.append(obj)
                self.levelModelObjects.append(obj)
            else:
                self.levelModelObjects.append(obj)
            
        #    obj.location.x += 1.0
        self.numberOfGoals = len(self.goalObjects)
        print(len(self.jamabarObjects))
        self.numberOfBumpers = len(self.bumperObjects)
        self.numberOfJamabars = len(self.jamabarObjects)
        self.numberOfBananas = len(self.bananaObjects)
        self.numberOfLevelModels = len(self.levelModelObjects)
        self.numberOfBackgroundModels = len(self.backgroundModelObjects)
        self.numberOfReflectiveObjects = len(self.reflectiveObjects)
        self.writeLZ(context)
        return {'FINISHED'}            # this lets blender know the operator finished successfully.
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def writeLZ(self, context):
        """Save an SMB LZ File"""
        with open(self.filepath, 'wb') as file:
            self.writeStartPositions(file)
            self.writeGoals(file)
            self.writeBumpers(file)
            self.writeJamabars(file)
            self.writeBananas(file)
            self.writeobjectNames(file)
            self.writeLevelModels(file)
            self.writeCollisionTriangles(file, context)
            self.writeHeader(file)
    
    def writeZeroBytes(self, file, numZeros):
        byteArray = []
        for i in range(0, numZeros):
            byteArray.append(0)
        file.write(bytes(byteArray))
            
    def writeHeader(self, file):
        file.seek(0, 0)
        self.writeZeroBytes(file, 8)                            # Unknown
        file.write(self.toBigI(self.numCollisionFields))        # Number of collision fields
        file.write(self.toBigI(self.collisionFieldsOffset))     # Offset to to collision fields
        file.write(self.toBigI(160))                            # Size of head/offset to start position (always 0xA0)
        file.write(self.toBigI(self.falloutPlaneOffset))        # Offset to fallout plane Y coordinate
        file.write(self.toBigI(self.numberOfGoals))             # Number of goals
        file.write(self.toBigI(self.goalsOffset))               # Offset to goals
        file.write(self.toBigI(self.numberOfGoals));            # Number of goals
        self.writeZeroBytes(file, 4)                            # Zero
        file.write(self.toBigI(self.numberOfBumpers))           # Number of bumpers
        file.write(self.toBigI(self.bumpersOffset))             # Offset to bumpers
        file.write(self.toBigI(self.numberOfJamabars))          # Number of jamabars
        file.write(self.toBigI(self.jamabarOffset))             # Offset to jamabars
        file.write(self.toBigI(self.numberOfBananas))           # Number of bananas
        file.write(self.toBigI(self.bananasOffset))             # Offset to bananas
        self.writeZeroBytes(file, 10)                           # Zero
        file.write(self.toBigI(0))                              # Number of something?
        file.write(self.toBigI(0))                              # Offset to something?
        file.write(self.toBigI(self.numberOfLevelModels))       # Number of level models
        file.write(self.toBigI(self.levelModelsOffset))         # Offset to level models
        self.writeZeroBytes(file, 8)                            # Zero
        file.write(self.toBigI(self.numberOfBackgroundModels))  # Number of background models
        file.write(self.toBigI(self.backgroundModelsOffset))    # Offset to background models
        file.write(self.toBigI(0))                              # Number of something?
        file.write(self.toBigI(0))                              # Offset to something
        file.write(self.toBigI(0))                              # Zero
        file.write(self.toBigI(1))                              # One
        file.write(self.toBigI(self.numberOfReflectiveObjects)) # Number of reflective objects
        file.write(self.toBigI(self.reflectiveObjectsOffset))   # Offset to reflective objects
        self.writeZeroBytes(file, 30)                           # Unknown
        
    def writeStartPositions(self, file):
        file.seek(self.sizeOfHeader, 0)
        for obj in self.startPositionObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toBigF(obj.location.y))
            file.write(self.toShortI(obj.rotation_euler.x))
            file.write(self.toShortI(obj.rotation_euler.z))
            file.write(self.toShortI(obj.rotation_euler.y))
            self.writeZeroBytes(file, 2)
        self.goalsOffset = file.tell()
        
    def writeGoals(self, file):
        file.seek(self.goalsOffset, 0)
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toBigF(obj.location.y))
            file.write(self.toShortI(obj.rotation_euler.x))
            file.write(self.toShortI(obj.rotation_euler.z))
            file.write(self.toShortI(obj.rotation_euler.y))
            lowerName = obj.name.lower()
            if "red" in lowerName:
                file.write(self.toShortI(0x5200))
            elif "green" in lowerName:
                file.write(self.toShortI(0x4700))
            else:
                file.write(self.toShortI(0x4200))
            
            
        self.bumpersOffset = file.tell()
        
    def writeBumpers(self, file):
        file.seek(self.bumpersOffset, 0)
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toBigF(obj.location.y))
            file.write(self.toShortI(obj.rotation_euler.x))
            file.write(self.toShortI(obj.rotation_euler.z))
            file.write(self.toShortI(obj.rotation_euler.y))
            self.writeZeroBytes(file, 2)
            file.write(self.toBigF(obj.scale.x))
            file.write(self.toBigF(obj.scale.z))
            file.write(self.toBigF(obj.scale.y)) 
        self.jamabarOffset = file.tell()
        
    def writeJamabars(self, file):
        file.seek(self.jamabarOffset, 0)
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toBigF(obj.location.y))
            file.write(self.toShortI(obj.rotation_euler.x))
            file.write(self.toShortI(obj.rotation_euler.z))
            file.write(self.toShortI(obj.rotation_euler.y))
            self.writeZeroBytes(file, 2)
            file.write(self.toBigF(obj.scale.x))
            file.write(self.toBigF(obj.scale.z))
            file.write(self.toBigF(obj.scale.y)) 
        self.bananasOffset = file.tell()
        
    def writeBananas(self, file):
        file.seek(self.bananasOffset, 0)
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))
            file.write(self.toBigF(obj.location.z))
            file.write(self.toBigF(obj.location.y))
            if "bunch" in obj.name.lower():
                file.write(self.toBigI(1))
            else:
                file.write(self.toBigI(0))
        self.modelNamesOffset = file.tell()
        
    def writeobjectNames(self, file):
        file.seek(self.modelNamesOffset, 0)
        print(self.modelNamesOffset)
        for obj in self.levelModelObjects:
            self.levelModelNameOffsets.append(file.tell())
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)
        for obj in self.backgroundModelObjects:
            self.backgroundModelNameOffsets.append(file.tell())
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)
        for obj in self.reflectiveObjects:
            self.reflectiveObjectNameOffsets.append(file.tell())
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)
        self.levelModelsOffset = file.tell()
        
    def writeLevelModels(self, file):
        # Level Models
        file.seek(self.levelModelsOffset, 0)
        for i in range(0, len(self.levelModelNameOffsets)):
            file.write(self.toBigI(1))
            self.levelModelNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.levelModelNameOffsets[i]))
            file.write(self.toBigI(0))
            
        # Background Models
        self.backgroundModelsOffset = file.tell()
        for i in range(0, len(self.backgroundModelNameOffsets)):
            file.write(self.toBigI(1))
            self.backgroundModelNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.backgroundModelNameOffsets[i]))
            file.write(self.toBigI(0))
        
        # Reflective Models
        self.reflectiveObjectsOffset = file.tell()
        for i in range(0, len(self.reflectiveObjectNameOffsets)):
            file.write(self.toBigI(1))
            self.reflectiveObjectNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.reflectiveObjectNameOffsets[i]))
            file.write(self.toBigI(0))
            
    def writeCollisionTriangles(self, file, context):
        # Level Models
        for i in range(0, len(self.levelModelObjects)):
            
            self.levelModelTriangleOffsets.append(file.tell())
            obj = self.duplicateObject(self.levelModelObjects[i])
            self.triangulate_object(obj)
            for i in range(0, obj.data.vertices, 3):
                vertex = obj.data.vertices[i]
                temp = vertex[1]
                vertex[1] = vertex[2]
                vertex[2] = temp
                if i % 3 == 0:
                    vertex2 = obj.data.vertices[i + 1]
                    vertex3 = obj.data.vertices[i + 2]
                elif i % 3 == 1:
                    vertex2 = obj.data.vertices[i + 1]
                    vertex3 = obj.data.vertices[i - 1]
                else:
                    vertex2 = obj.data.vertices[i - 2]
                    vertex3 = obj.data.vertices[i - 1]
                temp = vertex2[1]
                vertex2[1] = vertex2[2]
                vertex2[2] = temp
                temp = vertex3[1]
                vertex3[1] = vertex3[2]
                vertex3[2] = temp
                ba = Vector((vector2.x - vector.x, vector2.y - vector.y, vector2.z - vector.z))
                ca = Vector((vector3.x - vector.x, vector3.y - vector.y, vector3.z - vector.z))
                
                
            
            
        # Background Models
        for i in range(0, len(self.backgroundModelObjects)):
            break
        
        # Reflective Models
        for i in range(0, len(self.reflectiveObjects)):
            break
            
    def toBigI(self, number):
        return struct.pack('>I', number)
        
    def toBigF(self, number):
        return struct.pack('>f', number)
        
    def toShortI(self, number):
        return struct.pack('>H', int(number) & 0xFFFF)
        
    def cross(self, a, b):
        return Vector((a[1] * b[2]) - (a[2] * b[1]),
                      (a[2] * b[0]) - (a[0] * b[1]),
                      (a[0] * b[1]) - (a[1] * b[0])
                      
    def dot(self, a, b):
        return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] + b[2])
        
    def normalize(self, v):
        magnitude = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        return Vector(v[0] / magnitude, v[1] / magnitude, v[2] / magnitude)
      
    
    def duplicateObject(self, object):
        from mathutils import Vector
        copy = object.copy()
        copy.location += Vector((0, 0, 0))
        copy.data = copy.data.copy()
        return copy
            
    def triangulate_object(self, obj):
        import bmesh
        me = obj.data
        # Get a BMesh representation
        bm = bmesh.new()
        bm.from_mesh(me)

        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(me)
        bm.free()

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
    
    