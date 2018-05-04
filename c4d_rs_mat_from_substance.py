#!/usr/bin/env python

"""RC_RS_mat_from_substance.py: Loads Substances from the c4d asset manager and connects them in a new redshift material."""

__author__      = "Bonsak Schieldrop"
__copyright__   = "WTFPL, 2018, Racecar"
__version__     = "0.1"

import c4d
try:
    import redshift
except:
    pass

def GetChannels(doc, assets, model):
    
    subGraph = c4d.modules.substance.GetSubstanceGraph(assets[0])
    channels = {}
    prevOutput = None
    
    while True:
        output, uid, type, name, bmp = c4d.modules.substance.GetSubstanceOutput(assets[0], subGraph[0], False, prevOutput)   
        prevOutput = output

        if name in model:
            #print output[3]
            channels[name] = (output, uid, type, name, bmp, model[name])     
        
        if output == None:
            break

    return channels, subGraph[1], assets[0]

def CreateMaterial(matx, maty):

    mat = c4d.BaseMaterial(1036224)
    if mat is None:
        raise Exception("Could not create material")

    doc.InsertMaterial(mat)
    
    gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
    root = gvNodeMaster.GetRoot()
    output = root.GetDown()

    redshift_material = gvNodeMaster.CreateNode(gvNodeMaster.GetRoot(), 1036227, gvNodeMaster.GetRoot(), matx, maty)
    redshift_material[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "Material"
    redshift_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_BRDF] = 1
    redshift_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_FRESNEL_MODE] = 2
    redshift_material.GetOutPort(0).Connect(output.GetInPort(0))

    return redshift_material, gvNodeMaster, output

def MakeNodes(shaderChannels, asset, name):

    matx = 100
    maty = 250

    redshift_material, gvNodeMaster, output = CreateMaterial(matx, maty)

    # Make nodes
    posx = matx - 250
    posy = 100
    
    for chan in shaderChannels:

        matPort = redshift_material.AddPort(c4d.GV_PORT_INPUT,id= shaderChannels[chan][5],message=True)
        node = gvNodeMaster.CreateNode(gvNodeMaster.GetRoot(), 1036227, gvNodeMaster.GetRoot(), posx, posy)
        
        if chan == 'Height':
            offset = 250
            # Add dispport to Output node
            output.AddPort(c4d.GV_PORT_INPUT,id= c4d.GV_REDSHIFT_OUTPUT_DISPLACEMENT,message=True)
            # Set type to displacement
            node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "Displacement"
            node.AddPort(c4d.GV_PORT_INPUT,id= c4d.REDSHIFT_SHADER_DISPLACEMENT_TEXMAP,message=True)
            node[c4d.REDSHIFT_SHADER_DISPLACEMENT_SCALE] = 0.1
            node[c4d.REDSHIFT_SHADER_DISPLACEMENT_NEWRANGE_MIN] = - 0.5
            node[c4d.REDSHIFT_SHADER_DISPLACEMENT_NEWRANGE_MAX] = 0.5
            #Connect to disp port on Output disp
            node.GetOutPort(0).Connect(output.GetInPort(1))

            # Make a new TextureSampler
            dispTex = gvNodeMaster.CreateNode(gvNodeMaster.GetRoot(), 1036227, gvNodeMaster.GetRoot(), posx - 135, posy)
            dispTex[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
            dispTex.AddPort(c4d.GV_PORT_INPUT,id= c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,message=True)         
            dispTex.GetOutPort(0).Connect(node.GetInPort(0))

        else:
            offset = 100
            if chan == 'Normal':
                # Set type to Normal map
                node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "NormalMap"
                texIn = node.AddPort(c4d.GV_PORT_INPUT,id= c4d.REDSHIFT_SHADER_NORMALMAP_TEX0,message=True)               
            else:
                # Set type to TextureSampler
                node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
                texIn = node.AddPort(c4d.GV_PORT_INPUT,id= c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,message=True)
                
            node.GetOutPort(0).Connect(matPort)

        node[c4d.ID_BASELIST_NAME] = chan
            #texIn.Connect(matPort)
        


        subNode = gvNodeMaster.CreateNode(gvNodeMaster.GetRoot(), 1036762, gvNodeMaster.GetRoot(), posx - offset, posy)
        
        subShd = c4d.BaseShader(1032171)
        subNode[c4d.GV_REDSHIFT_BAKER_SHADER] = subShd
        subNode.InsertShader(subShd)
        subNode[c4d.GV_REDSHIFT_BAKER_SHADER][c4d.SUBSTANCESHADER_ASSET] = asset
        subNode[c4d.GV_REDSHIFT_BAKER_SHADER][c4d.SUBSTANCESHADER_CHANNEL] = shaderChannels[chan][1]

        if chan == 'Height':
            subNode.GetOutPort(0).Connect(dispTex.GetInPort(0))
        else:
            subNode.GetOutPort(0).Connect(node.GetInPort(0))

        posy += 75
        #print shaderChannels[chan][5]

def main():

    doc = c4d.documents.GetActiveDocument()
    assets = c4d.modules.substance.GetSubstances(doc, 1)

    if len(assets) == 0:
        c4d.gui.MessageDialog('Please select a Substance Asset')
        return

    model = {
    'Base Color': c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR,
    'Ambient Occlusion': c4d.REDSHIFT_SHADER_MATERIAL_OVERALL_COLOR,
    'Roughness': c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS,
    'Metallic': c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT,
    'Opacity': c4d.REDSHIFT_SHADER_MATERIAL_OPACITY_COLOR,
    'Emissive': c4d.REDSHIFT_SHADER_MATERIAL_EMISSION_COLOR,
    'Normal': c4d.REDSHIFT_SHADER_MATERIAL_BUMP_INPUT,
    'Height': c4d.REDSHIFT_SHADER_DISPLACEMENT_TEXMAP,
    }

    # model = ['Base Color','Roughness','Metallic','Height','Normal','Ambient Occlusion']
    channels, name, asset = GetChannels(doc, assets, model)
    # channels = getChannels(model)

    MakeNodes(channels, asset, name)
    # makeMaterial(channels, asset, name)
    c4d.EventAdd()
    
if __name__=='__main__':
    main()
