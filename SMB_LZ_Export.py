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
import math

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
    
    startPositionObjects = []                           # list of start position objects
    numberOfCollisionFields = 0;                        # Number of collision fields/headers
    collisionFieldsOffset = 0                           # Offset to collision fields/headers
    sizeOfHeader = 160                                  # Size of file header (always 0xA0 (160)
    falloutPlaneOffset = -20                              # Offset to fallout plane value
    falloutPlaneY = 0                                   # Fallout plane value
    numberOfGoals = 0                                   # Number of goals
    goalsOffset = 0                                     # Offset to goals
    goalObjects = []                                    # List of goal objects
    numberOfBumpers = 0                                 # Number of bumpers
    bumpersOffset = 0                                   # Offset to bumpers
    bumperObjects = []                                  # List of bumper objects
    numberOfJamabars = 0                                # Number of jamabars
    jamabarOffset = 0                                   # Offset to jamabars
    jamabarObjects = []                                 # List of jamabar objects
    numberOfBananas = 0                                 # Number of bananas
    bananasOffset = 0                                   # Offset to bananas
    bananaObjects = []                                  # List of banana objects
    numberOfLevelModels = 0                             # Number of level models
    levelModelsOffset = 0                               # Offset to level models
    levelModelObjects = []                              # List of level model objects
    levelModelNameOffsets = []                          # List of offsets to level model name asciis
    levelModelNamePointerOffsets = []                   # List of offsets to the level model name ascii offsets
    levelModelAnimationFrameOffsets = []                # List of animation frame offsets
    levelModelTriangleOffsets = []                      # List of triangle collider offsets
    levelModelCollisionGridPointers = []                # List of collision grid pointer offsets
    numberOfLevelModelTriangles = []                    # List of the number of level model triangles
    levelModelCollisionGridPointerPointers = []         # List of pointer offsets to the collision grid pointer
    numberOfBackgroundModels = 0                        # Number of background models
    backgroundModelsOffset = 0                          # Offset to background models
    backgroundModelObjects = []                         # List of background model offsets
    backgroundModelNameOffsets = []                     # List of offsets to model name asciis
    backgroundModelNamePointerOffsets = []              # List of offsets to model name ascii offsets
    backgroundModelCollisionGridPointerPointers = []    # List of pointer offsets to the collision grid pointers
    numberOfReflectiveObjects = 0                       # Number of Reflective objects
    reflectiveObjectsOffset = 0                         # Offset to reflective objects
    reflectiveObjects = []                              # List of reflective objects
    reflectiveObjectNameOffsets = []                    # List of offsets to model name asciis
    reflectiveObjectNamePointerOffsets = []             # List of offsets to the model name ascii offsets
    reflectiveObjectAnimationFrameOffsets = []          # List of animation frame offsets
    reflectiveObjectTriangleOffsets = []                # List of triangle collider offsets
    reflectiveObjectCollisionGridPointers = []          # List of collision grid pointer offsets
    numberOfReflectiveObjectTriangles = []              # List of the number of model triangles
    reflectiveObjectCollisionGridPointerPointers = []   # List of pointer offsets to the collision grid pointers
    modelNamesOffset = 0                                # Offset to model names
    
    filename_ext = ".lz.raw"
    filter_glob = StringProperty(
            default="*.lz.raw",
            options={'HIDDEN'},
            )


    def execute(self, context):        # execute() is called by blender when running the operator.
        """Called when the addon is run after selecting a save file"""
        self.clearData()
        
        scene = context.scene
        # Go through each object in the scene and put it into its related list
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
            else:
                self.levelModelObjects.append(obj)
            
        # Get the length of each list for the file header
        self.numberOfGoals = len(self.goalObjects)
        self.numberOfBumpers = len(self.bumperObjects)
        self.numberOfJamabars = len(self.jamabarObjects)
        self.numberOfBananas = len(self.bananaObjects)
        self.numberOfLevelModels = len(self.levelModelObjects)
        self.numberOfBackgroundModels = len(self.backgroundModelObjects)
        self.numberOfReflectiveObjects = len(self.reflectiveObjects)
        # Begin writing the LZ file
        self.writeLZ(context)
        self.clearData()
        return {'FINISHED'}            # this lets blender know the operator finished successfully.
        
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def writeLZ(self, context):
        """Save an SMB LZ File"""
        with open(self.filepath, 'wb') as file:
            # Written in semi-reverse order so that all needed offsets are known by each method
            self.writeStartPositions(file)
            self.writeFalloutPlane(file)
            self.writeGoals(file)
            self.writeBumpers(file)
            self.writeJamabars(file)
            self.writeBananas(file)
            self.writeobjectNames(file)
            self.writeLevelNameOffsets(file)
            self.writeLevelModels(file)
            self.writeReflectiveModels(file)
            self.writeBackgroundModels(file)
            self.writeCollisionTriangles(file, context)
            self.writeCollisionGridTriangleList(file)
            self.writeCollisionGridTrianglePointers(file)
            self.writeAnimationFrameHeaders(file)
            self.writeCollisionFields(file)
            self.writeHeader(file)
                
    def writeZeroBytes(self, file, numZeros):
        """Writes a set number of 0 bytes to a file"""
        byteArray = []
        for i in range(0, numZeros):
            byteArray.append(0)
        file.write(bytes(byteArray))
            
    def writeHeader(self, file):
        """Writes the SMB LZ Header"""
        file.seek(0, 0)
        self.writeZeroBytes(file, 4)                            # (4i) Unknown
        file.write(self.toBigI(100))                            # (4i) Unknown/100  
        file.write(self.toBigI(self.numberOfCollisionFields))   # (4i) Number of collision fields
        file.write(self.toBigI(self.collisionFieldsOffset))     # (4i) Offset to to collision fields
        file.write(self.toBigI(160))                            # (4i) Size of head/offset to start position (always 0xA0)
        file.write(self.toBigI(self.falloutPlaneOffset))        # (4i) Offset to fallout plane Y coordinate
        file.write(self.toBigI(self.numberOfGoals))             # (4i) Number of goals
        file.write(self.toBigI(self.goalsOffset))               # (4i) Offset to goals
        file.write(self.toBigI(self.numberOfGoals));            # (4i) Number of goals
        self.writeZeroBytes(file, 4)                            # (4i) Zero
        file.write(self.toBigI(self.numberOfBumpers))           # (4i) Number of bumpers
        file.write(self.toBigI(self.bumpersOffset))             # (4i) Offset to bumpers
        file.write(self.toBigI(self.numberOfJamabars))          # (4i) Number of jamabars
        file.write(self.toBigI(self.jamabarOffset))             # (4i) Offset to jamabars
        file.write(self.toBigI(self.numberOfBananas))           # (4i) Number of bananas
        file.write(self.toBigI(self.bananasOffset))             # (4i) Offset to bananas
        self.writeZeroBytes(file, 16)                           # (16i)Zero
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something?
        file.write(self.toBigI(self.numberOfLevelModels))       # (4i) Number of level models
        file.write(self.toBigI(self.levelModelsOffset))         # (4i) Offset to level models
        self.writeZeroBytes(file, 8)                            # (8i) Zero
        file.write(self.toBigI(self.numberOfBackgroundModels))  # (4i) Number of background models
        file.write(self.toBigI(self.backgroundModelsOffset))    # (4i) Offset to background models
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(1))                              # (4i) One
        file.write(self.toBigI(self.numberOfReflectiveObjects))                              # (4i) Number of reflective objects
        file.write(self.toBigI(self.reflectiveObjectsOffset))   # (4i) Offset to reflective objects
        self.writeZeroBytes(file, 24)                           # (24i)Unknown
        
    def writeStartPositions(self, file):
        """Writes the start positions to the file"""
        """(1 for levels, 1+ for some many games)"""
        
        
        # Make sure we write into the right position
        # Start positions are always right after the header
        file.seek(self.sizeOfHeader, 0)
                
        # Go through start position objects and write them in
        for obj in self.startPositionObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z Location
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))     # (2i) X rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))     # (2i) Y rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
                        
    def writeFalloutPlane(self, file):
        self.falloutPlaneOffset = file.tell()
        file.write(self.toBigF(self.falloutPlaneY))             # (4i) Fallout Y coordinate
        
    def writeGoals(self, file):
        """Writes the goals into the lz"""
        
        if self.numberOfGoals == 0:
            return
        
        self.goalsOffset = file.tell()
        
        # Go through goal objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))     # (2i) X rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))     # (2i) Y rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))     # (2i) Z rotation
            # Determine the goal type (blue = default)
            # Red = 0x5200, Green = 0x4700, Blue = 0x4200
            lowerName = obj.name.lower()
            if "red" in lowerName:
                file.write(self.toShortI(0x5200))               # (2i) Goal type (Red)  
            elif "green" in lowerName:
                file.write(self.toShortI(0x4700))               # (2i) Goal type (Green)
            else:
                file.write(self.toShortI(0x4200))               # (2i) Goal type (Blue)
            
        
    def writeBumpers(self, file):
        """Writes the bumpers into the LZ"""
        
        if self.numberOfBumpers == 0:
            return
        
        self.bumpersOffset = file.tell()
          
        # Go through bumper objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))     # (2i) X rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))     # (2i) Y rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
            file.write(self.toBigF(obj.scale.x))                # (4f) X scale
            file.write(self.toBigF(obj.scale.z))                # (4f) Y scale
            file.write(self.toBigF(obj.scale.y))                # (4f) Z scale
            
        
    def writeJamabars(self, file):
        """Writes the bumpers into the LZ"""
        
        if self.numberOfJamabars == 0:
            return
        
        self.jamabarOffset = file.tell()
        
        # Go through the jamabar objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))     # (2i) X rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))     # (2i) Y rotation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
            file.write(self.toBigF(obj.scale.x))                # (4f) X scale
            file.write(self.toBigF(obj.scale.z))                # (4f) Y scale
            file.write(self.toBigF(obj.scale.y))                # (4f) Z 
        
        
    def writeBananas(self, file):
        """Write the bananas into the LZ"""
        
        if self.numberOfBananas == 0:
            return
        
        self.bananasOffset = file.tell()
        
        # Go through the banana objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            # Determine the banana type (single/nanner = default)
            # Bunch = 1, Single.Nanner = 1
            if "bunch" in obj.name.lower():
                file.write(self.toBigI(1))                      # (4i) Banana Type (Bunch)
            else:
                file.write(self.toBigI(0))                      # (4i) Banana Type (Single/Nanner)
        
        
    def writeobjectNames(self, file):
        """Write the model names into the file"""
        
        alignment = file.tell() % 4
        if alignment != 0:
            self.writeZeroBytes(file, 4 - alignment)
        self.modelNamesOffset = file.tell()
        
        # Go through every standard level model and write their name in
        for obj in self.levelModelObjects:
            # Add this name to the list of name offsets
            self.levelModelNameOffsets.append(file.tell())
            # Encode the name into bytes and write it in
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)                               # (ascii) Model name
            self.writeZeroBytes(file, 1)                        # (1i) \0 Char
            alignment = file.tell() % 4;                        # Get number of bytes that would align the file
            if alignment != 0:
                self.writeZeroBytes(file, 4 - alignment)         
                
        # Go through every background level model and write their name in
        for obj in self.backgroundModelObjects:
            # Add this name to the list of name offsets
            self.backgroundModelNameOffsets.append(file.tell())
            # Encode the name into bytes and write it in
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)                               # (ascii) Model name
            self.writeZeroBytes(file, 1)                        # (1i) \0 Char
            alignment = file.tell() % 4;                        # Get number of bytes that would align the file
            if alignment != 0:
                self.writeZeroBytes(file, 4 - alignment)        
            
        # Go through every reflective level model and write their name in
        for obj in self.reflectiveObjects:
            # Add this name to the list of name offsets
            self.reflectiveObjectNameOffsets.append(file.tell())
            # Encode the name into bytes and write it in
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)                               # (ascii) Model name
            self.writeZeroBytes(file, 1)                        # (1i) \0 Char
            alignment = file.tell() % 4;                        # Get number of bytes that would align the file
            if alignment != 0:
                self.writeZeroBytes(file, 4 - alignment)            
        
    def writeLevelNameOffsets(self, file):
        # Go through every standard level model and write its header
        for i in range(0, len(self.levelModelNameOffsets)):
            # Add the offset the list of pointers to level name asciis
            self.levelModelNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.levelModelNameOffsets[i]))          # (4i) Offset to model name ascii
    
        # Go through every standard level model and write its header
        for i in range(0, len(self.reflectiveObjectNameOffsets)):
            # Add the offset the list of pointers to level name asciis
            self.reflectiveObjectNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.reflectiveObjectNameOffsets[i]))    # (4i) Offset to model name ascii   
    
        # Go through every standard level model and write its header
        for i in range(0, len(self.backgroundModelNameOffsets)):
            # Add the offset the list of pointers to level name asciis
            self.backgroundModelNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.backgroundModelNameOffsets[i]))  
        
    def writeLevelModels(self, file):
        """Write the level model headers into the file"""
        
        if self.numberOfLevelModels == 0:
            return
        
        self.levelModelsOffset = file.tell()
        
        # Go through every standard level model and write its header
        for i in range(0, len(self.levelModelNameOffsets)):
   
            file.write(self.toBigI(1))                                      # (4i) Zero
            file.write(self.toBigI(self.levelModelNameOffsets[i]))          # (4i) Offset to model name ascii
            file.write(self.toBigI(0))                                      # (4i) Zero
                 
    def writeReflectiveModels(self, file):
        """Write the reflective model headers into the file"""
        
        if self.numberOfReflectiveObjects == 0:
            return
        
        # Save where the reflective level models headers start
        self.reflectiveObjectsOffset = file.tell()
        # Go through every standard level model and write its header
        for i in range(0, len(self.reflectiveObjectNameOffsets)):
            # Add the offset the list of pointers to level name asciis
            file.write(self.toBigI(self.reflectiveObjectNameOffsets[i]))    # (4i) Offset to model name ascii   
            file.write(self.toBigI(0))                                      # (4i) Zero
    
    def writeBackgroundModels(self, file):
        """Write the background model headers into the file"""
        
        if self.numberOfBackgroundModels == 0:
            return
        
        # Save where the background level models headers start
        self.backgroundModelsOffset = file.tell()
        # Go through every standard level model and write its header
        for i in range(0, len(self.backgroundModelNameOffsets)):
            obj = self.backgroundModelObjects[i]
            file.write(self.toBigI(31))                                     # (31i)0x1F
            file.write(self.toBigI(self.backgroundModelNameOffsets[i]))     # (4i) Offset to model name ascii
            file.write(self.toBigI(0))                                      # (4i) Zero
            file.write(self.toBigF(obj.location.x))                         # (4f) X location
            file.write(self.toBigF(obj.location.z))                         # (4f) Y location
            file.write(self.toBigF(obj.location.y))                         # (4f) Z location
            self.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))                 # (2i) X rotation
            self.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))                 # (2i) Z rotation
            self.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))                 # (2i) Y rotation
            self.writeZeroBytes(file, 2)                                    # (2i) Zero
            file.write(self.toBigF(obj.scale.x))                            # (4f) X scale
            file.write(self.toBigF(obj.scale.z))                            # (4f) Y scale
            file.write(self.toBigF(obj.scale.y))                            # (4f) Z scale
            self.writeZeroBytes(file, 12)                                   # (12i)Zero
        
    def writeCollisionTriangles(self, file, context):
        """Write the collision triangles into the LZ"""
        from mathutils import Vector
        
        # Go through every standard level model and write its triangles
        for i in range(0, len(self.levelModelObjects)):
            # Add this offset to the list of triangle offsets
            self.levelModelTriangleOffsets.append(file.tell())
            # Duplicate the object to avoid modifying the actual blender scene
            obj = self.duplicateObject(self.levelModelObjects[i])
            # Triangulate the object
            self.triangulate_object(obj)
            # Add the number of faces to the list of triangle counts
            self.numberOfLevelModelTriangles.append(len(obj.data.polygons))
            
            # Go through every triangle face
            for face in obj.data.polygons:
                vertices = []
                # Collect the face's vertices
                for vert in face.vertices:
                    vertices.append(Vector((obj.data.vertices[vert].co.x, obj.data.vertices[vert].co.z, obj.data.vertices[vert].co.y)))
                # Write the triangle to the LZ
                self.writeTriangle(file, vertices[0], vertices[1], vertices[2])
            
        # Go through every reflective level model and write its triangles
        for i in range(0, len(self.reflectiveObjects)):
            # Add this offset to the list of triangle offsets
            self.reflectiveObjectTriangleOffsets.append(file.tell())
            # Duplicate the object to avoid modifying the actual blender scene
            obj = self.duplicateObject(self.reflectiveObjects[i])
            # Triangulate the object
            self.triangulate_object(obj)
             # Add the number of faces to the list of triangle counts
            self.numberOfReflectiveObjectTriangles.append(len(obj.data.polygons))
            
            # Go through every triangle face
            for face in obj.data.polygons:
                vertices = []
                # Collect the face's vertices
                for vert in face.vertices:
                    vertices.append(Vector((obj.data.vertices[vert].co.x, obj.data.vertices[vert].co.z, obj.data.vertices[vert].co.y)))
                # Write the triangle to the LZ
                self.writeTriangle(file, vertices[0], vertices[1], vertices[2])
            
                
    def writeCollisionGridTriangleList(self, file):
        """Writes the list of triangles used for each objects collider"""
        
        # Go through every standard level model and write its collision grid list
        for i in range(0, len(self.levelModelObjects)):
            # Add this offset to the collision grid pointers list
            self.levelModelCollisionGridPointers.append(file.tell())
            
            numTriangles = self.numberOfLevelModelTriangles[i]
            # Triangles are ordered, so just writing 0-numTriangles
            for j in range(0, 256):
                for i in range(0, numTriangles):
                    file.write(self.toShortI(i))                    # (2i) Offset to collision triangle in list
                file.write(self.toShortI(65535))                    # (2i) Triangle List terminator
            alignment = file.tell() % 4
            if alignment != 0:
                self.writeZeroBytes(file, 4 - alignment)
        
        # Go through every reflective level model and write its collision grid list
        for i in range(0, len(self.reflectiveObjects)):
            # Add this offset to the collision grid pointers list
            self.reflectiveObjectCollisionGridPointers.append(file.tell())
            
            numTriangles = self.numberOfReflectiveObjectTriangles[i]
            # Triangles are ordered, so just writing 0-numTriangles
            for j in range(0, 256):
                for i in range(0, numTriangles):
                    file.write(self.toShortI(i))                    # (2i) Offset to collision triangle in list
                file.write(self.toShortI(65535))                    # (2i) Triangle List terminator
            alignment = file.tell() % 4
            if alignment != 0:
                self.writeZeroBytes(file, 4 - alignment)
            
    def writeCollisionGridTrianglePointers(self, file):
        """Writes pointers to the triangle grid list"""
                
        # Go through every standard level model and write its collision grid list pointer
        for i in range(0, len(self.levelModelObjects)):
            numTriangles = self.numberOfLevelModelTriangles[i]
            # Add this offset to the collision grid pointers list
            self.levelModelCollisionGridPointerPointers.append(file.tell())
            for j in range(0, 256):
                file.write(self.toBigI(self.levelModelCollisionGridPointers[i] + (j * (2 + (2 * numTriangles)))))
            
        # Go through every reflective level model and write its collision grid list
        for i in range(0, len(self.reflectiveObjects)):
            numTriangles = self.numberOfReflectiveObjectTriangles[i]
            # Add this offset to the collision grid pointers list
            self.reflectiveObjectCollisionGridPointerPointers.append(file.tell())
            for j in range(0, 256):
                file.write(self.toBigI(self.reflectiveObjectCollisionGridPointers[i]+ (j * (2 + (2 * numTriangles)))))


    def writeAnimationFrameHeaders(self, file):
        """Writes a stub of animation frame headers for objects"""
        
        # Go through every standard level model and write its collision grid list
        for i in range(0, len(self.levelModelObjects)):
            self.levelModelAnimationFrameOffsets.append(file.tell())
            # Writing stub with 0 animation frames for now
            file.write(self.toBigI(0))                          # (4i) Number of X frames
            file.write(self.toBigI(0))                          # (4i) Offset to X frames
            file.write(self.toBigI(0))                          # (4i) Number of Y frames
            file.write(self.toBigI(0))                          # (4i) Offset to Y frames
            file.write(self.toBigI(0))                          # (4i) Number of Z frames
            file.write(self.toBigI(0))                          # (4i) Offset to Z frames
            self.writeZeroBytes(file, 24)                       # (24i)Zero
            
        # Go through every reflective level model and write its collision grid list
        for i in range(0, len(self.reflectiveObjects)):
            self.reflectiveObjectAnimationFrameOffsets.append(file.tell())
            # Writing stub with 0 animation frames for now
            file.write(self.toBigI(0))                          # (4i) Number of X frames
            file.write(self.toBigI(0))                          # (4i) Offset to X frames
            file.write(self.toBigI(0))                          # (4i) Number of Y frames
            file.write(self.toBigI(0))                          # (4i) Offset to Y frames
            file.write(self.toBigI(0))                          # (4i) Number of Z frames
            file.write(self.toBigI(0))                          # (4i) Offset to Z frames
            self.writeZeroBytes(file, 24)                       # (24i)Zero
                        
    def writeCollisionFields(self, file):
        """Write the collision field headers into the LZ"""
        
        self.numberOfCollisionFields = self.numberOfLevelModels + self.numberOfReflectiveObjects

        if self.numberOfCollisionFields == 0:
            return
        
        # Save where the collision fields offset is
        self.collisionFieldsOffset = file.tell()
        
        
        # Go through every standard level model and write its collision header
        for i in range(0, len(self.levelModelObjects)):
            obj = self.levelModelObjects[i]
            file.write(self.toBigF(0))#obj.location.x))                                 # (4f) X center for animation
            file.write(self.toBigF(0))#obj.location.z))                                 # (4f) Y center for animation
            file.write(self.toBigF(0))#obj.location.y))                                 # (4f) Z center for animation
            file.write(self.toShortI(0))#self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))                         # (2i) X rotation for animation
            file.write(self.toShortI(0))#self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))                         # (2i) Y rotation for animation
            file.write(self.toShortI(0))#self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))                         # (2i) Z rotation for animation
            self.writeZeroBytes(file, 2)                                            # (2i) Zero
            file.write(self.toBigI(0))        # (4i) Offset to animation frame header
            file.write(self.toBigI(self.levelModelNamePointerOffsets[i]))           # (4i) Offset to level model name pointer
            file.write(self.toBigI(self.levelModelTriangleOffsets[i]))              # (4i) Offset to triangle colliders
            file.write(self.toBigI(self.levelModelCollisionGridPointerPointers[i])) # (4i) Offset to collision grid list pointers
            file.write(self.toBigF(-256))                                              # (4i) Start X value for collision grid
            file.write(self.toBigF(-256))                                              # (4i) Start Z value for collision grid
            file.write(self.toBigF(32))                                              # (4i) Step X value for collision grid
            file.write(self.toBigF(32))                                              # (4i) Step X value for collision grid
            file.write(self.toBigI(16))                                             # (4i) 16
            file.write(self.toBigI(16))                                             # (4i) 16
            self.writePartialHeader(file)                                           # (136)Partial Header
            
        # Go through every reflective level model and write its collision header
        for i in range(0, len(self.reflectiveObjects)):
            obj = self.reflectiveObjects[i]
            file.write(self.toBigF(obj.location.x))                                         # (4f) X center for animation
            file.write(self.toBigF(obj.location.z))                                         # (4f) Y center for animation
            file.write(self.toBigF(obj.location.y))                                         # (4f) Z center for animation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.x))))                                 # (2i) X rotation for animation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.z))))                                 # (2i) Y rotation for animation
            file.write(self.toShortI(self.cnvAngle(self.toDegrees(obj.rotation_euler.y))))                                 # (2i) Z rotation for animation
            self.writeZeroBytes(file, 2)                                                    # (2i) Zero
            file.write(self.toBigI(self.reflectiveObjectAnimationFrameOffsets[i]))          # (4i) Offset to animation frame header
            file.write(self.toBigI(self.reflectiveObjectNamePointerOffsets[i]))             # (4i) Offset to level model name pointer
            file.write(self.toBigI(self.reflectiveObjectTriangleOffsets[i]))                # (4i) Offset to triangle colliders
            file.write(self.toBigI(self.reflectiveObjectCollisionGridPointerPointers[i]))   # (4i) Offset to collision grid list pointers
            file.write(self.toBigF(-256))                                                   # (4i) Start X value for collision grid
            file.write(self.toBigF(-256))                                                   # (4i) Start Z value for collision grid
            file.write(self.toBigF(32))                                                    # (4i) Step X value for collision grid
            file.write(self.toBigF(32))                                                    # (4i) Step X value for collision grid
            file.write(self.toBigI(16))                                                     # (4i) 16
            file.write(self.toBigI(16))                                                     # (4i) 16
            self.writePartialHeader(file)                                                   # (136)Partial Header
            
    def writePartialHeader(self, file):
        file.write(self.toBigI(self.numberOfGoals))             # (4i) Number of goals
        file.write(self.toBigI(self.goalsOffset))               # (4i) Offset to goals
        file.write(self.toBigI(self.numberOfGoals));            # (4i) Number of goals
        self.writeZeroBytes(file, 4)                            # (4i) Zero
        file.write(self.toBigI(self.numberOfBumpers))           # (4i) Number of bumpers
        file.write(self.toBigI(self.bumpersOffset))             # (4i) Offset to bumpers
        file.write(self.toBigI(self.numberOfJamabars))          # (4i) Number of jamabars
        file.write(self.toBigI(self.jamabarOffset))             # (4i) Offset to jamabars
        file.write(self.toBigI(self.numberOfBananas))           # (4i) Number of bananas
        file.write(self.toBigI(self.bananasOffset))             # (4i) Offset to bananas
        self.writeZeroBytes(file, 16)                           # (16i)Zero
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something?
        file.write(self.toBigI(self.numberOfLevelModels))       # (4i) Number of level models
        file.write(self.toBigI(self.levelModelsOffset))         # (4i) Offset to level models
        self.writeZeroBytes(file, 8)                            # (8i) Zero
        file.write(self.toBigI(0))                              # (4i) Number of background models
        file.write(self.toBigI(0))                              # (4i) Offset to background models
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(1))                              # (4i) One
        file.write(self.toBigI(self.numberOfReflectiveObjects))                              # (4i) Number of reflective objects
        file.write(self.toBigI(self.reflectiveObjectsOffset))   # (4i) Offset to reflective objects
        self.writeZeroBytes(file, 24)                           # (24i)Unknown
        
    
    def toBigI(self, number):
        return struct.pack('>I', number)
        
    def toBigF(self, number):
        return struct.pack('>f', number)
        
    def toShortI(self, number):
        return struct.pack('>H', int(number) & 0xFFFF)
        
    def cross(self, a, b):
        from mathutils import Vector
        return Vector(((a.y * b.z) - (a.z * b.y),
                      (a.z * b.x) - (a.x * b.z),
                      (a.x * b.y) - (a.y * b.x)))
                      
    def dot(self, a, b):
        return (a.x * b.x) + (a.y * b.y) + (a.z + b.z)
        
    def dotm(self, a, r0, r1, r2):
        from mathutils import Vector
        return Vector(((a.x * r0.x) + (a.y * r1.x) + (a.z * r2.x),
                      (a.x * r0.y) + (a.y * r1.y) + (a.z * r2.y),
                      (a.x * r0.z) + (a.y * r1.z) + (a.z * r2.z)))
        
    def normalize(self, v):
        from mathutils import Vector
        magnitude = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        if magnitude == 0:
            return Vector((0, 0, 0))
        return Vector((v.x / magnitude, v.y / magnitude, v.z / magnitude))
      
    def hat(self, v):
        from mathutils import Vector
        return Vector((-v.y, v.x, 0.0))
        
    def toDegrees(self, theta):
        if math.isnan(theta):
            theta = 0
        return 57.2957795130824*theta
        
    def cnvAngle(self, theta):
        return int(65536.0 * theta / 360.0)
        
    def reverse_angle(self, c, s):
        if c > 1.0:
            c = 1.0
        elif c < -1.0:
            c = -1.0
        if s > 1.0:
            s = 1.0
        elif s < -1.0:
            s = -1.0
        a = self.toDegrees(math.asin(s))
        if c < 0:
            a -= 180.0
        if abs(c) < abs(s):
            a = self.toDegrees(math.acos(c))
            if s < 0.0:
                a = -a
        if a < 0.0:
            if a > -0.001:
                a = 0.0
            else:
                a += 360.0
        return a
    
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
        
    def writeTriangle(self, file, vertex, vertex2, vertex3):
        """Writes a triangle into the LZ"""
        """Mostly duplicated from Yoshimaster's original code"""
        from mathutils import Vector

        ba = Vector(((vertex2.x - vertex.x, vertex2.y - vertex.y, vertex2.z - vertex.z)))
        ca = Vector(((vertex3.x - vertex.x, vertex3.y - vertex.y, vertex3.z - vertex.z)))
        
        normal = self.normalize(self.cross(self.normalize(ba), self.normalize(ca)))
        l = math.sqrt(normal.x * normal.x + normal.z * normal.z)

        if abs(l) < 0.001:
            cy = 1.0
            sy = 0.0
        else:
            cy = normal.z / l
            sy = -normal.x / l
        cx = l
        sx = normal.y
        
        Rxr0 = Vector((1.0, 0.0, 0.0))
        Rxr1 = Vector((0.0, cx, sx))
        Rxr2 = Vector((0.0, -sx, cx))
        Ryr0 = Vector((cy, 0.0, -sy))
        Ryr1 = Vector((0.0, 1.0, 0.0))
        Ryr2 = Vector((sy, 0.0, cy))
        dotry = self.dotm(ba, Ryr0, Ryr1, Ryr2)
        dotrxry = self.dotm(dotry, Rxr0, Rxr1, Rxr2)
        l = math.sqrt(dotrxry.x * dotrxry.x + dotrxry.y * dotrxry.y)
        cz = dotrxry.x / l
        sz = -dotrxry.y / l
        Rzr0 = Vector((cz, sz, 0.0))
        Rzr1 = Vector((-sz, cz, 0.0))
        Rzr2 = Vector((0.0, 0.0, 1.0))
        dotrz = self.dotm(dotrxry, Rzr0, Rzr1, Rzr2)
        dotry = self.dotm(ca, Ryr0, Ryr1, Ryr2)
        dotrzrxry = self.dotm(dotrxry, Rzr0, Rzr1, Rzr2)
        
        n0v = Vector((dotrzrxry.x - dotrz.x, dotrzrxry.y - dotrz.y, dotrzrxry.z - dotrz.z))
        n1v = Vector((-dotrzrxry.y, -dotrzrxry.y, -dotrzrxry.z))
        n0 = self.normalize(self.hat(n0v))
        n1 = self.normalize(self.hat(n1v))
        
        rot_x = 360.0 - self.reverse_angle(cx, sx)
        rot_y = 360.0 - self.reverse_angle(cy, sy)
        rot_z = 360.0 - self.reverse_angle(cz, sz)
        
        file.write(self.toBigF(vertex.x))              # (4f) X1 position
        file.write(self.toBigF(vertex.y))              # (4f) Y1 position
        file.write(self.toBigF(vertex.z))              # (4f) Z1 position
        file.write(self.toBigF(normal.x))              # (4f) X normal
        file.write(self.toBigF(normal.y))              # (4f) Y normal
        file.write(self.toBigF(normal.z))              # (4f) Z normal
        file.write(self.toShortI(self.cnvAngle(rot_x))) # (2i) X rotation from XY plane
        file.write(self.toShortI(self.cnvAngle(rot_y))) # (2i) Y rotation from XY plane
        file.write(self.toShortI(self.cnvAngle(rot_z))) # (2i) Z rotation from XY plane
        self.writeZeroBytes(file, 2)                    # (2i) Zero
        file.write(self.toBigF(dotrz.x))               # (4f) DX2X1
        file.write(self.toBigF(dotrz.y))               # (4f) DY2Y1
        file.write(self.toBigF(dotrzrxry.x))           # (4f) DX3X1
        file.write(self.toBigF(dotrzrxry.y))           # (4f) DY3Y1
        file.write(self.toBigF(n0.x))                  # (4f) Tangent X
        file.write(self.toBigF(n0.y))                  # (4f) Tangent Y
        file.write(self.toBigF(n1.x))                  # (4f) Bitangent X
        file.write(self.toBigF(n1.y))                  # (4f) Bitangent Y
        
    def clearData(self):
        self.startPositionObjects = []                           # list of start position objects
        self.numberOfCollisionFields = 0;                        # Number of collision fields/headers
        self.collisionFieldsOffset = 0                           # Offset to collision fields/headers
        self.sizeOfHeader = 160                                  # Size of file header (always 0xA0 (160)
        self.falloutPlaneOffset = 0                              # Offset to fallout plane value
        self.falloutPlaneY = 0                                   # Fallout plane value
        self.numberOfGoals = 0                                   # Number of goals
        self.goalsOffset = 0                                     # Offset to goals
        self.goalObjects = []                                    # List of goal objects
        self.numberOfBumpers = 0                                 # Number of bumpers
        self.bumpersOffset = 0                                   # Offset to bumpers
        self.bumperObjects = []                                  # List of bumper objects
        self.numberOfJamabars = 0                                # Number of jamabars
        self.jamabarOffset = 0                                   # Offset to jamabars
        self.jamabarObjects = []                                 # List of jamabar objects
        self.numberOfBananas = 0                                 # Number of bananas
        self.bananasOffset = 0                                   # Offset to bananas
        self.bananaObjects = []                                  # List of banana objects
        self.numberOfLevelModels = 0                             # Number of level models
        self.levelModelsOffset = 0                               # Offset to level models
        self.levelModelObjects = []                              # List of level model objects
        self.levelModelNameOffsets = []                          # List of offsets to level model name asciis
        self.levelModelNamePointerOffsets = []                   # List of offsets to the level model name ascii offsets
        self.levelModelAnimationFrameOffsets = []                # List of animation frame offsets
        self.levelModelTriangleOffsets = []                      # List of triangle collider offsets
        self.levelModelCollisionGridPointers = []                # List of collision grid pointer offsets
        self.numberOfLevelModelTriangles = []                    # List of the number of level model triangles
        self.levelModelCollisionGridPointerPointers = []         # List of pointer offsets to the collision grid pointer
        self.numberOfBackgroundModels = 0                        # Number of background models
        self.backgroundModelsOffset = 0                          # Offset to background models
        self.backgroundModelObjects = []                         # List of background model offsets
        self.backgroundModelNameOffsets = []                     # List of offsets to model name asciis
        self.backgroundModelNamePointerOffsets = []              # List of offsets to model name ascii offsets
        self.backgroundModelCollisionGridPointerPointers = []    # List of pointer offsets to the collision grid pointers
        self.numberOfReflectiveObjects = 0                       # Number of Reflective objects
        self.reflectiveObjectsOffset = 0                         # Offset to reflective objects
        self.reflectiveObjects = []                              # List of reflective objects
        self.reflectiveObjectNameOffsets = []                    # List of offsets to model name asciis
        self.reflectiveObjectNamePointerOffsets = []             # List of offsets to the model name ascii offsets
        self.reflectiveObjectAnimationFrameOffsets = []          # List of animation frame offsets
        self.reflectiveObjectTriangleOffsets = []                # List of triangle collider offsets
        self.reflectiveObjectCollisionGridPointers = []          # List of collision grid pointer offsets
        self.numberOfReflectiveObjectTriangles = []              # List of the number of model triangles
        self.reflectiveObjectCollisionGridPointerPointers = []   # List of pointer offsets to the collision grid pointers
        self.modelNamesOffset = 0                                # Offset to model names
        

def menu_func_export(self, context):
    self.layout.operator(SMBLZExporter.bl_idname, text="SMB LZ (.lz.raw)")


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
    
    