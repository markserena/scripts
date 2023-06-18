import __main__
import os

import MASHbakeInstancer
import maya.cmds as cmds
import maya.mel as mel

ms_selectedPath = ""
ms_selected = ""

def convertInstances():
    mel.eval("MASHswitchGeometryType")
    mel.eval('BakeInstancerToGeometry')
    cmds.button('ms_exportButton', edit=True, enable=True)

def mash_instancer():
    import MASHbakeInstancer;MASHbakeInstancer.MASHbakeInstancer(True)

def createBones():
    ## The meshes are automatically selected, find the parent group and rename it
    get_parents = cmds.listRelatives(cmds.ls(sl=True), parent=True)
    cmds.select(get_parents, replace=True)
    newName = cmds.rename(get_parents, 'instancerSkinned_#')

    ## get all objects from newly created instancer conversion and group them seperately for neatness
    instancerGroup = newName
    skeletonGroup = cmds.group(name='%s_skeleton' % instancerGroup, world=True, empty=True)
    masterGroup = cmds.group(name='%s_Unreal_Export_FBX' % instancerGroup)
    newObjects = cmds.listRelatives(instancerGroup)

    ## For each object create a joint and copy the transform from the object to the rig
    ## And delete the previous channels and skin it.
    for obj in newObjects:
        i = 1
        nameSplit = obj.split('_')
        jointName = nameSplit[0] + '_' + nameSplit[1] + '_joint'
        ## find approx size via bounding box and place joints in min Y and max Y
        bbox = cmds.exactWorldBoundingBox(obj)
        cmds.select(clear=True)
        joint01 = cmds.joint(position=(0, bbox[1], 0), name='base_' + jointName + '_%i' % i)
        replaceName = joint01.replace('base_', 'tip_')
        joint02 = cmds.joint(position=(0, bbox[4], 0), name=replaceName)
        cmds.joint(joint01, edit=True, zeroScaleOrient=True, orientJoint='yzx', secondaryAxisOrient='zup')
        cmds.currentTime(0)
        cmds.copyKey(obj)
        cmds.pasteKey(joint01)
        cmds.delete(obj, channels=True)
        cmds.select(joint01, obj, replace=True)
        cmds.bindSkin()
        cmds.parent(joint01, skeletonGroup)
        i += 1

    ## Group everything into a master group ready for export
    cmds.parent(skeletonGroup, instancerGroup, masterGroup)
    cmds.select(masterGroup, replace=True)


def exportToFBX():
    ## Fix the path formatting.
    global ms_selectedPath
    ms_selectedPath = ms_selectedPath.replace('\\', '/')

    # Set defaults for FBX Exporting. Need smoothing groups/triangulation/Animation and other things to export correctly.
    mel.eval("FBXProperty Export|IncludeGrp|Geometry|SmoothingGroups -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Geometry|TangentsandBinormals -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Geometry|Triangulate -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Animation -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Animation|BakeComplexAnimation -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Animation|Deformation -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Animation|ConstraintsGrp|Constraint -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|Animation|ConstraintsGrp|Character -v 1;")
    mel.eval("FBXProperty Export|IncludeGrp|InputConnectionsGrp|InputConnections -v 1;")
    mel.eval("FBXProperty Export|AdvOptGrp|Fbx|AsciiFbx -v \"Binary\";")
    mel.eval("FBXProperty Export|AdvOptGrp|Fbx|ExportFileVersion -v \"FBX201400\";")
    ## Run the export
    mel.eval('FBXExport -f "' + ms_selectedPath + '" -s')

    ## Check the file exists
    if os.path.exists(ms_selectedPath) == 1:
        print("SUCCESS :: The file exported successfully."),
    else:
        print("SOMETHING WENT WRONG. Please try again."),

    ## Delete the UI
    cmds.deleteUI('ms_convertInstancer')
    cmds.deleteUI('mashBakeStill')

def browse():
    ## Choose an export path.
    global ms_selectedPath
    pathDialog = cmds.fileDialog2(fileFilter='*.fbx', dialogStyle=1, fileMode=0,
                                  caption="Select where to save the FBX file", okCaption="Create Here")
    if pathDialog is not None:
        ms_selectedPath = pathDialog[0]
        cmds.textFieldButtonGrp('ms_FBXDirectory', edit=True, text=ms_selectedPath)
        cmds.button('ms_convertButton', edit=True, enable=True)

def export():
    mash_instancer()
    createBones()
    exportToFBX()


def main():
    if not cmds.pluginInfo('MASH', query=True, loaded=True):
        cmds.error("MASH plugin not loaded")
    else:
        selection = cmds.ls(sl=True)
        test_mash = []
        if len(selection) == 1:
            if cmds.nodeType(selection[0]) == 'MASH_Waiter':
                connections = cmds.listConnections(selection[0])
                test_mash.append(['MASH_Repro' in cmds.nodeType(x) for x in connections])
        else:
            cmds.warning(" >>>>>>>>>>>>>>   Please select only one MASH Waiter <<<<<<<<<<<<<<")

        if any(test_mash):
            global ms_selected
            ms_selected = selection[0]
            file_location = __file__
            image_location = file_location.replace('.py', '.png')

            ms_window = 'ms_convertInstancer'
            if cmds.window(ms_window, exists=True):
                cmds.deleteUI(ms_window)

            cmds.window(ms_window, toolbox=True, topEdge=220, leftEdge=900,sizeable=False, title='ms_UE_instance_converter')
            colLayout = cmds.columnLayout(
                width=538,
                columnAlign='center'
            )
            cmds.image( image=image_location, parent=colLayout )
            cmds.textFieldButtonGrp('ms_FBXDirectory',
                label='Export Path',
                buttonLabel='Browse',
                parent=colLayout,
                columnAttach=[(1,'both', 0), (2, 'both', 0), (3, 'right', 0)],
                columnWidth3=(60,420, 50),
                buttonCommand=lambda : browse()
                )
            cmds.button(
                'ms_convertButton',
                label='Convert',
                command=lambda x: convertInstances(),
                parent=colLayout,
                enable=False,
                width=538 )
            cmds.button(
                'ms_exportButton',
                label='Export',
                command=lambda x: export(),
                parent=colLayout,
                enable=False,
                width=538 )

            cmds.text(
                label='Please leave Bake Instance Tool Window open.',
                backgroundColor=(0.4, 0.3, 0.3),
                parent=colLayout,
            )

            cmds.showWindow()
        else:
            cmds.warning(" >>>>>>>>>>>>>>   Please select only one MASH Waiter <<<<<<<<<<<<<<")


if __name__ == '__main__':
    main()
