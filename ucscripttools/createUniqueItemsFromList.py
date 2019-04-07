#! python
import os, fnmatch
from optparse import OptionParser
from tempfile import mkstemp
from shutil import move


# uniqueItemList = ['BoneClaws','WornLeatherJacket','ExperimentalRepulsors',
# 'DaddyDeadpoolDevice','ArmorShreddingAmmo','SHIELDLifeSupportGear',
# 'UruEnhancedShield','ZeroPointEnergyShield',
# 'AdvancedTurretControlDevice','AlwaysAngry','AsgardWarriorsCloak',
# 'HyperViper','KnivesofZawavari','BootsoftheCoalTiger','YelenasBite',
# 'GlovesoftheSiberianWinter','AskanisonBodysuit',
# 'MightyFistsoftheJuggernaut','KittysFavoriteShirt','MKraanVisor',
# 'LegacyofPunchclops','ShadowyMaskoftheHand','HornheadsHandyClubs',
# 'TheGunsWithNoName','TrickShotsBow','HulkbusterArrows','FocusedRage',
# 'GlovesoftheLightBrigade','FutureFoundationBelt','UruInfusedArmor',
# 'MKraanNexusMask','GlovesoftheTwelve','AirForceFlightSuit',
# 'BootsoftheNewAvenger','BeltofEndlessAmmo','OldPainless',
# 'AsylumWardenJacket','GauntletsofChaosShaping','HexcraftHeadpiece',
# 'HorizonLabsWebShooters','ShadowedMaskofKaine','BootsoftheMorlocks',
# 'CapeoftheBeautifulWindrider','ImmortalStaminaofKirby',
# 'StateUniversityJersey','HammeroftheThunderbringer',
# 'FrostInternationalScarf','MassachusettsAcademyGloves']
# 
# 
uniqueItemList = ['BaxterBuildingMicroturrets','BlessedBeltofthePantherGod',
'EidolonWarwear','KidpoolsLaserKatanas','FacetoftheUni-Power',
'LoveofCaieratheOldstrong','SwordGun','EbonyBlade','KimoyoCard',
'HellfireAmmunition','NisantiCloakOfInvisibility','CosmicEggOfThePhoenix',
'DeepSpaceHelmet','RoxxonSupertechLaserSight','TonyStarksCheckbook',
'DeptKTacticalWeaponsVest','KatanasofGratuitousViolence',
'MagicSatchelofUnlimitedWeaponry','GodlyGunsOfGoodness',
'ClanRebellionBodysuit','EyeOfTheEggbreaker','RubyQuartzSunglasses',
'HelmOfTheSkyfather','BurrowersBodyArmor','KreeTurretControlMatrix',
'LocketOfTheLordsCardinal','TraskCommanderHelm','BlackWidowBoots',
'IronSpiderBreastplate','CerebroRemoteInterface','BookoftheVishanti']

        

def FindTemplateMatches(userpath, templateName):
    for path, dirs, files in os.walk(os.path.abspath(userpath)):
        for filename in fnmatch.filter(files, templateName):
            filepath = os.path.join(path, filename)
            return filepath

 
def CreateNewChangeList(description):
    "Create a new changelist and returns the changelist number as a string"
    p4in, p4out = os.popen2("p4 changelist -i")
    p4in.write("change: new\n")
    p4in.write("description: " + description)
    p4in.close()
    changelist = p4out.readline().split()[1]
    return changelist


def P4AddFile(fpath, changelist = ""):
    """Open a file for add, 
    if a changelist is passed in then open it in that list"""
    if not fpath: return
    cmd = "p4 add "
    if changelist:
        cmd += " -c " + changelist + " "
    ret = os.popen(cmd + fpath).readline().strip()
    if not ret.endswith("opened for add"):
        print "Couldn't open", fpath, "for add:"
        print ret
        raise ValueError

def CreateUniqueFromTemplate(template, className, skelMeshName):
    newItemPath = template.replace('MarvelItemUniqueTemplate',className)
    #if the emote exists, dont proceed
    if os.path.isfile(newItemPath): return
    replacements = {'MarvelItemUniqueTemplate':className,'Mesh.acorn':skelMeshName}
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(template)
    # newLines = replace.split('\n')
    #replace class
    for line in old_file:
        for i, j in replacements.iteritems():
            line = line.replace(i,j)
        new_file.write(line)
    #close temp file
    new_file.close()
    os.close(fh)
    old_file.close()
    #Move new file
    move(abs_path, newItemPath)
    return newItemPath

def main():
    usage = "usage: createUniqueItemsFromList.py  [options] arg"
    parser = OptionParser(usage)
# 
#     parser.add_option("-e","--emoteName", dest = "emote",
#                      help ="New Emote name")
# 
#     parser.add_option("-a","--animation", dest = "anim",
#                      help ="animation name string")
# 
#     (options, args) = parser.parse_args()
#     #determine user input
#     if not (options.emote) and not (options.anim):
#         parser.error("must specifiy emote name and animation")
#     
    # print "creating new emote uc files from %s with %s " % \
    #     (options.emote, options.anim)

    searchpath = os.getcwd()
    mychangelist = None

    template = FindTemplateMatches(searchpath,'MarvelItemUniqueTemplate.uc')
    
    description = "createUniqueItemsFromList automated changelist"
        
    if not mychangelist:
        mychangelist = CreateNewChangeList (description)

    for i, itemname in enumerate(uniqueItemList):
        index = '{0:03d}'.format(i+49)
        classname = 'MarvelItem_Unique'+index+'_'+itemname
        print classname
        newItemFile = CreateUniqueFromTemplate(template, classname, itemname)
        P4AddFile(newItemFile,mychangelist)



if __name__ == "__main__":
    main()

