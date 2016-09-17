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
    
    startPositionObjects = []
    numberOfCollisionFields = 0;
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
    levelModelCollisionGridPointerPointers = []
    numberOfBackgroundModels = 0
    backgroundModelsOffset = 0
    backgroundModelObjects = []
    backgroundModelNameOffsets = []
    backgroundModelNamePointerOffsets = []
    backgroundModelAnimationFrameOffsets = []
    backgroundModelTriangleOffsets = []
    backgroundModelCollisionGridPointers = []
    numberOfBackgoundModelTriangles = []
    backgroundModelCollisionGridPointerPointers = []
    numberOfReflectiveObjects = 0
    reflectiveObjectsOffset = 0
    reflectiveObjects = []
    reflectiveObjectNameOffsets = []
    reflectiveObjectNamePointerOffsets = []
    reflectiveObjectAnimationFrameOffsets = []
    reflectiveObjectTriangleOffsets = []
    reflectiveObjectCollisionGridPointers = []
    numberOfReflectiveObjectTriangles = []
    reflectiveObjectCollisionGridPointerPointers = []
    modelNamesOffset = 0
    
    filename_ext = ".lz"
    filter_glob = StringProperty(
            default="*.lz",
            options={'HIDDEN'},
            )


    def execute(self, context):        # execute() is called by blender when running the operator.
        """Called when the addon is run after selecting a save file"""
        
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
        self.writeZeroBytes(file, 8)                            # (8i) Unknown
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
        file.write(self.toBigI(self.numberOfBackgroundModels))  # (4i) nNumber of background models
        file.write(self.toBigI(self.backgroundModelsOffset))    # (4i) Offset to background models
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(1))                              # (4i) One
        file.write(self.toBigI(self.numberOfReflectiveObjects)) # (4i) Number of reflective objects
        file.write(self.toBigI(self.reflectiveObjectsOffset))   # (4i) Offset to reflective objects
        self.writeZeroBytes(file, 48)                           # (48i)Unknown
        
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
            file.write(self.toShortI(obj.rotation_euler.x))     # (2i) X rotation
            file.write(self.toShortI(obj.rotation_euler.z))     # (2i) Y rotation
            file.write(self.toShortI(obj.rotation_euler.y))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
            
    def writeFalloutPlane(self, file):
        self.falloutPlaneOffset = file.tell()
        file.write(self.toBigI(self.falloutPlaneY))             # (4i) Fallout Y coordinate
        
    def writeGoals(self, file):
        """Writes the goals into the lz"""
        
        self.goalsOffset = file.tell()
        
        # Go through goal objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(obj.rotation_euler.x))     # (2i) X rotation
            file.write(self.toShortI(obj.rotation_euler.z))     # (2i) Y rotation
            file.write(self.toShortI(obj.rotation_euler.y))     # (2i) Z rotation
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
        
        self.bumpersOffset = file.tell()
        
        # Go through bumper objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(obj.rotation_euler.x))     # (2i) X rotation
            file.write(self.toShortI(obj.rotation_euler.z))     # (2i) Y rotation
            file.write(self.toShortI(obj.rotation_euler.y))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
            file.write(self.toBigF(obj.scale.x))                # (4f) X scale
            file.write(self.toBigF(obj.scale.z))                # (4f) Y scale
            file.write(self.toBigF(obj.scale.y))                # (4f) Z scale
            
        
    def writeJamabars(self, file):
        """Writes the bumpers into the LZ"""
        
        self.jamabarOffset = file.tell()
        
        # Go through the jamabar objects and write them in
        for obj in self.goalObjects:
            file.write(self.toBigF(obj.location.x))             # (4f) X location
            file.write(self.toBigF(obj.location.z))             # (4f) Y location
            file.write(self.toBigF(obj.location.y))             # (4f) Z location
            file.write(self.toShortI(obj.rotation_euler.x))     # (2i) X rotation
            file.write(self.toShortI(obj.rotation_euler.z))     # (2i) Y rotation
            file.write(self.toShortI(obj.rotation_euler.y))     # (2i) Z rotation
            self.writeZeroBytes(file, 2)                        # (2i) Zero
            file.write(self.toBigF(obj.scale.x))                # (4f) X scale
            file.write(self.toBigF(obj.scale.z))                # (4f) Y scale
            file.write(self.toBigF(obj.scale.y))                # (4f) Z 
        
        
    def writeBananas(self, file):
        """Write the bananas into the LZ"""
        
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
            
        # Go through every background level model and write their name in
        for obj in self.backgroundModelObjects:
            # Add this name to the list of name offsets
            self.backgroundModelNameOffsets.append(file.tell())
            # Encode the name into bytes and write it in
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)                               # (ascii) Model name
            self.writeZeroBytes(file, 1)                        # (1i) \0 Char
            
        # Go through every reflective level model and write their name in
        for obj in self.reflectiveObjects:
            # Add this name to the list of name offsets
            self.reflectiveObjectNameOffsets.append(file.tell())
            # Encode the name into bytes and write it in
            nameBytes = bytearray()
            nameBytes.extend(obj.name.encode())
            file.write(nameBytes)                               # (ascii) Model name
            
        
    def writeLevelModels(self, file):
        """Write the level model headers into the file"""
        
        self.levelModelsOffset = file.tell()
        
        # Go through every standard level model and write its header
        for i in range(0, len(self.levelModelNameOffsets)):
            file.write(self.toBigI(1))                                      # (4i) Zero
            # Add the offset the list of pointers to level name asciis
            self.levelModelNamePointerOffsets.append(file.tell())   
            file.write(self.toBigI(self.levelModelNameOffsets[i]))          # (4i) Offset to model name ascii
            file.write(self.toBigI(0))                                      # (4i) Zero
                 
    def writeReflectiveModels(self, file):
        """Write the reflective model headers into the file"""
        # Save where the reflective level models headers start
        self.reflectiveObjectsOffset = file.tell()
        # Go through every standard level model and write its header
        for i in range(0, len(self.reflectiveObjectNameOffsets)):
            self.reflectiveObjectNamePointerOffsets.append(file.tell())
            # Add the offset the list of pointers to level name asciis
            file.write(self.toBigI(self.reflectiveObjectNameOffsets[i]))    # (4i) Offset to model name ascii   
            file.write(self.toBigI(0))                                      # (4i) Zero
    
    def writeBackgroundModels(self, file):
        """Write the background model headers into the file"""
        
        # Save where the background level models headers start
        self.backgroundModelsOffset = file.tell()
        # Go through every standard level model and write its header
        for i in range(0, len(self.backgroundModelNameOffsets)):
            obj = self.backgroundModelObjects[i]
            file.write(self.toBigI(31))                                     # (31i)Zero
            # Add the offset the list of pointers to level name asciis
            self.backgroundModelNamePointerOffsets.append(file.tell())
            file.write(self.toBigI(self.backgroundModelNameOffsets[i]))     # (4i) Offset to model name ascii
            file.write(self.toBigI(0))                                      # (4i) Zero
            file.write(self.toBigF(obj.location.x))                         # (4f) X location
            file.write(self.toBigF(obj.location.z))                         # (4f) Y location
            file.write(self.toBigF(obj.location.y))                         # (4f) Z location
            self.write(self.toShortI(obj.rotation_euler.x))                 # (2i) X rotation
            self.write(self.toShortI(obj.rotation_euler.z))                 # (2i) Z rotation
            self.write(self.toShortI(obj.rotation_euler.y))                 # (2i) Y rotation
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
                    vertices.append(Vector((obj.data.vertices[vert].co.x, obj.data.vertices[vert].co.y, obj.data.vertices[vert].co.z)))
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
                    vertices.append(Vector((obj.data.vertices[vert].co.x, obj.data.vertices[vert].co.y, obj.data.vertices[vert].co.z)))
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
            for i in range(0, numTriangles):
                file.write(self.toShortI(i))                    # (2i) Offset to collision triangle in list
            file.write(self.toShortI(65535))                    # (2i) Triangle List terminator
        
        # Go through every reflective level model and write its collision grid list
        for i in range(0, len(self.reflectiveObjects)):
            # Add this offset to the collision grid pointers list
            self.reflectiveObjectCollisionGridPointers.append(file.tell())
            
            numTriangles = self.numberOfReflectiveObjectTriangles[i]
            # Triangles are ordered, so just writing 0-numTriangles
            for i in range(0, numTriangles):
                file.write(self.toShortI(i))                    # (2i) Offset to collision triangle in list
            file.write(self.toShortI(65535))                    # (2i) Triangle List terminator
            
    def writeCollisionGridTrianglePointers(self, file):
        """Writes pointers to the triangle grid list"""
                
        # Go through every standard level model and write its collision grid list pointer
        for i in range(0, len(self.levelModelObjects)):
            # Add this offset to the collision grid pointers list
            self.levelModelCollisionGridPointerPointers.append(file.tell())
            file.write(self.toBigI(self.levelModelCollisionGridPointers[i]))
            
        # Go through every reflective level model and write its collision grid list
        for i in range(0, len(self.reflectiveObjects)):
            # Add this offset to the collision grid pointers list
            self.reflectiveObjectCollisionGridPointerPointers.append(file.tell())
            file.write(self.toBigI(self.reflectiveObjectCollisionGridPointers[i]))


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
            self.writeZeroBytes(file, 24)                       # (24i) Zero
            
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
            self.writeZeroBytes(file, 24)                       # (24i) Zero
                        
    def writeCollisionFields(self, file):
        """Write the collision field headers into the LZ"""
        
        # Save where the collision fields offset is
        self.collisionFieldsOffset = file.tell()
        
        self.numberOfCollisionFields = self.numberOfLevelModels + self.numberOfReflectiveObjects
        
        # Go through every standard level model and write its collision header
        for i in range(0, len(self.levelModelObjects)):
            obj = self.levelModelObjects[i]
            file.write(self.toBigF(obj.location.x))                                 # (4f) X center for animation
            file.write(self.toBigF(obj.location.z))                                 # (4f) Y center for animation
            file.write(self.toBigF(obj.location.y))                                 # (4f) Z center for animation
            file.write(self.toShortI(obj.rotation_euler.x))                         # (2i) X rotation for animation
            file.write(self.toShortI(obj.rotation_euler.z))                         # (2i) Y rotation for animation
            file.write(self.toShortI(obj.rotation_euler.y))                         # (2i) Z rotation for animation
            self.writeZeroBytes(file, 2)                                            # (2i) Zero
            file.write(self.toBigI(self.levelModelAnimationFrameOffsets[i]))        # (4i) Offset to animation frame header
            file.write(self.toBigI(self.levelModelNamePointerOffsets[i]))           # (4i) Offset to level model name pointer
            file.write(self.toBigI(self.levelModelTriangleOffsets[i]))              # (4i) Offset to triangle colliders
            file.write(self.toBigI(self.levelModelCollisionGridPointerPointers[i])) # (4i) Offset to collision grid list pointers
            file.write(self.toBigF(0))                                              # (4i) Start X value for collision grid
            file.write(self.toBigF(0))                                              # (4i) Start Z value for collision grid
            file.write(self.toBigF(1))                                              # (4i) Step X value for collision grid
            file.write(self.toBigF(0))                                              # (4i) Step X value for collision grid
            file.write(self.toBigI(16))                                             # (4i) 16
            file.write(self.toBigI(16))                                             # (4i) 16
            self.writePartialHeader(file)                                           # (136)Partial Header
            
        # Go through every reflective level model and write its collision header
        for i in range(0, len(self.reflectiveObjects)):
            obj = self.reflectiveObjects[i]
            file.write(self.toBigF(obj.location.x))                                         # (4f) X center for animation
            file.write(self.toBigF(obj.location.z))                                         # (4f) Y center for animation
            file.write(self.toBigF(obj.location.y))                                         # (4f) Z center for animation
            file.write(self.toShortI(obj.rotation_euler.x))                                 # (2i) X rotation for animation
            file.write(self.toShortI(obj.rotation_euler.z))                                 # (2i) Y rotation for animation
            file.write(self.toShortI(obj.rotation_euler.y))                                 # (2i) Z rotation for animation
            self.writeZeroBytes(file, 2)                                                    # (2i) Zero
            file.write(self.toBigI(self.reflectiveObjectAnimationFrameOffsets[i]))          # (4i) Offset to animation frame header
            file.write(self.toBigI(self.reflectiveObjectNamePointerOffsets[i]))             # (4i) Offset to level model name pointer
            file.write(self.toBigI(self.reflectiveObjectTriangleOffsets[i]))                # (4i) Offset to triangle colliders
            file.write(self.toBigI(self.reflectiveObjectCollisionGridPointerPointers[i]))   # (4i) Offset to collision grid list pointers
            file.write(self.toBigF(0))                                                      # (4i) Start X value for collision grid
            file.write(self.toBigF(0))                                                      # (4i) Start Z value for collision grid
            file.write(self.toBigF(1))                                          # (4i) Step X value for collision grid
            file.write(self.toBigF(0))                                          # (4i) Step X value for collision grid
            file.write(self.toBigI(16))                                         # (4i) 16
            file.write(self.toBigI(16))                                         # (4i) 16
            self.writePartialHeader(file)                                       # (136)Partial Header
            
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
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(0))                              # (4i) Number of something?
        file.write(self.toBigI(0))                              # (4i) Offset to something
        file.write(self.toBigI(0))                              # (4i) Zero
        file.write(self.toBigI(1))                              # (4i) One
        file.write(self.toBigI(self.numberOfReflectiveObjects)) # (4i) Number of reflective objects
        file.write(self.toBigI(self.reflectiveObjectsOffset))   # (4i) Offset to reflective objects
        self.writeZeroBytes(file, 48)                           # (48i)Unknown
        
    
    def toBigI(self, number):
        return struct.pack('>I', number)
        
    def toBigF(self, number):
        return struct.pack('>f', number)
        
    def toShortI(self, number):
        return struct.pack('>H', int(number) & 0xFFFF)
        
    def cross(self, a, b):
        from mathutils import Vector
        return Vector(((a[1] * b[2]) - (a[2] * b[1]),
                      (a[2] * b[0]) - (a[0] * b[1]),
                      (a[0] * b[1]) - (a[1] * b[0])))
                      
    def dot(self, a, b):
        return (a[0] * b[0]) + (a[1] * b[1]) + (a[2] + b[2])
        
    def dotm(self, a, r0, r1, r2):
        from mathutils import Vector
        return Vector(((a[0] * r0[0]) + (a[1] * r1[0]) + (a[2] * r2[0]),
                      (a[0] * r0[1]) + (a[1] * r1[1]) + (a[2] * r2[1]),
                      (a[0] * r0[2]) + (a[1] * r1[2]) + (a[2] * r2[2])))
        
    def normalize(self, v):
        from mathutils import Vector
        magnitude = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if magnitude == 0:
            return Vector((0, 0, 0))
        return Vector((v[0] / magnitude, v[1] / magnitude, v[2] / magnitude))
      
    def hat(self, v):
        from mathutils import Vector
        return Vector((-v[1], v[0], 0.0))
        
    def toDegrees(self, theta):
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
        if abs(c) < abs(s):
            a = self.toDegrees(math.acos(c))
            if s < 0.0:
                a = -a
        else:
            a = self.toDegrees(math.asin(s))
            if c < 0.0:
                a = 180.0 - a
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
        
        # Swap Y and Z positions (Blender has Z being up instead of Y)
        temp = vertex[1]
        vertex[1] = vertex[2]
        vertex[2] = temp
        temp = vertex2[1]
        vertex2[1] = vertex2[2]
        vertex2[2] = temp
        temp = vertex3[1]
        vertex3[1] = vertex3[2]
        vertex3[2] = temp
        ba = Vector(((vertex2.x - vertex.x, vertex2.y - vertex.y, vertex2.z - vertex.z)))
        ca = Vector(((vertex3.x - vertex.x, vertex3.y - vertex.y, vertex3.z - vertex.z)))
        
        normal = self.normalize(self.cross(self.normalize(ba), self.normalize(ca)))
        l = math.sqrt(normal[0] * normal[0] + normal[2] * normal[2])

        if abs(l) < 0.001:
            cy = 1.0
            sy = 0.0
        else:
            cy = normal[2] / l
            sy = -normal[0] / l
        cx = l
        sx = normal[1]
        
        Rxr0 = Vector((1.0, 0.0, 0.0))
        Rxr1 = Vector((0.0, cx, sx))
        Rxr2 = Vector((0.0, -sx, cx))
        Ryr0 = Vector((cy, 0.0, -sy))
        Ryr1 = Vector((0.0, 1.0, 0.0))
        Ryr2 = Vector((sy, 0.0, cy))
        dotry = self.dotm(ba, Ryr0, Ryr1, Ryr2)
        dotrxry = self.dotm(dotry, Rxr0, Rxr1, Rxr2)
        l = math.sqrt(dotrxry[0] * dotrxry[0] + dotrxry[2] * dotrxry[1])
        cz = dotrxry[0] / l
        sz = -dotrxry[1] / l
        Rzr0 = Vector((cz, sz, 0.0))
        Rzr1 = Vector((-sz, cz, 0.0))
        Rzr2 = Vector((0.0, 0.0, 1.0))
        dotrz = self.dotm(dotrxry, Rzr0, Rzr1, Rzr2)
        dotry = self.dotm(ca, Ryr0, Ryr1, Ryr2)
        dotrzrxry = self.dotm(dotrxry, Rzr0, Rzr1, Rzr2)
        
        n0v = Vector((dotrzrxry[0] - dotrz[0], dotrzrxry[1] - dotrz[1], dotrzrxry[2] - dotrz[2]))
        n1v = Vector((-dotrzrxry[1], -dotrzrxry[1], -dotrzrxry[2]))
        n0 = self.normalize(self.hat(n0v))
        n1 = self.normalize(self.hat(n1v))
        
        rot_x = 360.0 - self.reverse_angle(cx, sx)
        rot_y = 360.0 - self.reverse_angle(cy, sy)
        rot_z = 360.0 - self.reverse_angle(cz, sz)
        
        file.write(self.toBigF(vertex[0]))              # (4f) X1 position
        file.write(self.toBigF(vertex[1]))              # (4f) Y1 position
        file.write(self.toBigF(vertex[2]))              # (4f) Z1 position
        file.write(self.toBigF(normal[0]))              # (4f) X normal
        file.write(self.toBigF(normal[1]))              # (4f) Y normal
        file.write(self.toBigF(normal[2]))              # (4f) Z normal
        file.write(self.toShortI(self.cnvAngle(rot_x))) # (2i) X rotation from XY plane
        file.write(self.toShortI(self.cnvAngle(rot_y))) # (2i) Y rotation from XY plane
        file.write(self.toShortI(self.cnvAngle(rot_z))) # (2i) Z rotation from XY plane
        self.writeZeroBytes(file, 2)                    # (2i) Zero
        file.write(self.toBigF(dotrz[0]))               # (4f) DX2X1
        file.write(self.toBigF(dotrz[1]))               # (4f) DY2Y1
        file.write(self.toBigF(dotrzrxry[0]))           # (4f) DX3X1
        file.write(self.toBigF(dotrzrxry[1]))           # (4f) DY3Y1
        file.write(self.toBigF(n0[0]))                  # (4f) Tangent X
        file.write(self.toBigF(n0[1]))                  # (4f) Tangent Y
        file.write(self.toBigF(n1[0]))                  # (4f) Bitangent X
        file.write(self.toBigF(n1[1]))                  # (4f) Bitangent Y

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
    
    