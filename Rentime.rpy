# Copyright 2024 Endimyonn (https://github.com/Endimyonn)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Rentime is a set of tools used to modify Ren'Py games at runtime, as opposed to modifying official game files ahead-of-time.
# It primarily provides tools used to seek out parts of a game's script and UI code, and manipulate it from there.
# It also provides LayeredRen, a set of three tools to substitute game files with mod files without replacing them on disk.
init -1000 python:
    ############
    # Script Tools:
    # Tools for working with game-script content - primarily labels and the content contained by them.
    ############

    def GetLabel(name):
        return renpy.game.script.lookup(name)
    
    # Scans an AST node tree for a specific node.
    # Returns the result if found, otherwise None.
    # The subAvoid field should not be altered, as it is used for recursion.
    # Currently supported node types:
    # - "Say":
    #     Query should be any portion of the said text
    # - "Sayer":
    #     Query should be any portion of a speaker name
    # - "Python":
    #     Query should be any portion of the source of the Python statement
    #     The "$ " preceding it must be omitted.
    # - "If":
    #     Query should be any portion of the condition string of any branch of the desired If node
    # - "Menu":
    #     Query should be any portion of any choice of the desired Menu node
    def FindNode(baseNode, nodeType, query, exactMatch = False, subAvoid = None):
        iterNode = baseNode
        while iterNode != None and iterNode != subAvoid:
            if type(iterNode) == renpy.ast.Say or (Rentime_Compat_HasTranslateSay == True and type(iterNode) == renpy.ast.TranslateSay):
                if nodeType == "Say":
                    if (exactMatch == True and iterNode.what == query) or (exactMatch == False and query in iterNode.what):
                        return iterNode
                elif nodeType == "Sayer":
                    if (exactMatch == True and iterNode.who == query) or (exactMatch == False and query in iterNode.who):
                        return iterNode
            
            if nodeType == "Python" and type(iterNode) == renpy.ast.Python:
                if (exactMatch == True and iterNode.code.source == query) or (exactMatch == False and query in iterNode.code.source):
                    return iterNode
            
            if type(iterNode) == renpy.ast.If:
                for ifEntry in iterNode.entries:
                    if nodeType == "If":
                        if (exactMatch == True and ifEntry[0] == query) or (exactMatch == False and query in ifEntry[0]):
                            return iterNode
                    # Check sub-branches contained by If node
                    checkBranch = FindNode(ifEntry[1][0], nodeType, query, exactMatch, iterNode.next)
                    if checkBranch is not None:
                        return checkBranch
            
            # Scan Translate blocks
            if type(iterNode) == renpy.ast.Translate:
                checkBranch = FindNode(iterNode.block[0], nodeType, query, exactMatch, iterNode.next)
                if checkBranch is not None:
                    return checkBranch
            
            # Scan Menu branches
            if type(iterNode) == renpy.ast.Menu:
                for menuItem in iterNode.items:
                    if menuItem[2] is not None: # don't check menu captions
                        if nodeType == "Menu":
                            if (exactMatch == True and menuItem[0] == query) or (exactMatch == False and query in menuItem[0]):
                                return iterNode
                        # Check sub-branches contained by Menu node
                        checkBranch = FindNode(menuItem[2][0], nodeType, query, exactMatch, iterNode.next)
                        if checkBranch is not None:
                            return checkBranch
            
            # Scan While loops
            if type(iterNode) == renpy.ast.While:
                checkBranch = FindNode(iterNode.block[0], nodeType, query, exactMatch, iterNode.next)
                if checkBranch is not None:
                    return checkBranch
            
            # Scan sub-labels
            if type(iterNode) == renpy.ast.Label and len(iterNode.block) > 0:
                checkBranch = FindNode(iterNode.block[0], nodeType, query, exactMatch, iterNode.next)
                if checkBranch is not None:
                    return checkBranch
            
            # Check the next node
            iterNode = iterNode.next
        return None
    
    # Changes the 'next' node of a node to a new target, and scans child branches of the node to do the same.
    # Also changes the new target's 'next' to the original 'next' node.
    def ReplaceNext(node, newNext):
        def ScanTree(base, old, new, subAvoid = None):
            iterNode = base
            while iterNode != None and iterNode != subAvoid:
                if type(iterNode) == renpy.ast.If:
                    for ifEntry in iterNode.entries:
                        ScanTree(ifEntry[1][0], old, new, iterNode.next)
                
                if type(iterNode) == renpy.ast.Menu:
                    for menuItem in iterNode.items:
                        if menuItem[2] != None:
                            ScanTree(menuItem[2][0], old, new, iterNode.next)
                
                if type(iterNode) == renpy.ast.While:
                    ScanTree(iterNode.block[0], old, new, iterNode.next)
                
                if iterNode != node and iterNode != newNext:
                    if iterNode.next == old:
                        iterNode.next = new
                    elif type(iterNode.next) == renpy.ast.Return:
                        iterNode.next = new
                
                iterNode = iterNode.next
        
        prevNext = node.next
        if type(newNext).__name__ == "list":
            node.next = newNext[0]
            ScanTree(node, prevNext, newNext[0], newNext[0])
            ScanTree(newNext[-1], prevNext, prevNext, prevNext)
        else:
            node.next = newNext
            ScanTree(node, prevNext, newNext, newNext)
            ScanTree(newNext, prevNext, prevNext, prevNext)
    
    # Creates a 'Say' AST node
    def CreateSay(who, what):
        return CreateBlock(who + " \"" + what + "\"")[0]
    
    # Inserts a 'Say' AST node between an existing node and the one following it
    def InsertSay(node, who, what):
        newSay = CreateSay(who, what)
        ReplaceNext(node, newSay)
        return newSay
    
    # Creates a block of AST statements.
    # 'connectLoose' (optional) should be a node to connect any loose ends on created sub-blocks to, typically a node following the end of the block, if applicable.
    def CreateBlock(rawRpy, connectLoose = None, stripReturn = True):
        newAST = renpy.game.script.load_string("Rentime.rpy", rawRpy)[0]
        if newAST == None:
            raise Exception("The provided script block could not be interpreted correctly. Check for script errors in it.")
        if type(newAST[-1]) == renpy.ast.Return and stripReturn == True:
            newAST = newAST[:-1]
        return newAST
    
    # Inserts an AST block between an existing node and the one following it
    def InsertBlock(node, rawRpy, stripReturn = True):
        newAST = CreateBlock(rawRpy, stripReturn)
        ReplaceNext(node, newAST)
    
    # Gets the values and index of a Menu node's item matching provided criteria.
    # Multiple types of criteria may be provided, and only the entry matching all will be returned.
    def GetMenuItem(menuNode, label = None, condition = None, containing = True):
        if label == None and condition == None:
            raise Exception("At least one criterion must be provided.")
        iter = -1
        for mLabel, mCond, mBlock in menuNode.items:
            iter += 1
            if label != None:
                if containing == True and label not in mLabel:
                    continue
                if containing == False and label != mLabel:
                    continue
            if condition != None:
                if containing == True and condition not in mCond:
                    continue
                if containing == False and condition != mCond:
                    continue
            return (menuNode.items[iter], iter)
        raise Exception("No item matching the provided criteria was found in the menu.")
    
    # Inserts an additional item to a Menu node
    def InsertMenuItem(menuNode, label, condition, rawRpy, index = None):
        newAST = CreateBlock(rawRpy)
        if index == None:
            menuNode.items.append((label, condition, newAST))
            if Rentime_Compat_MenuIArgs == True:
                menuNode.item_arguments.append(None)
        else:
            menuNode.items.insert(index, (label, condition, newAST))
            if Rentime_Compat_MenuIArgs == True:
                menuNode.item_arguments.insert(index, None)
    
    # Replaces the text of a Menu's item
    def ChangeMenuLabel(menuNode, index, newLabel):
        menuNode.items[index] = (newLabel, menuNode.items[index][1], menuNode.items[index][2])
    
    # Replaces the condition for a Menu's item to be shown
    def ChangeMenuCondition(menuNode, index, newCondition):
        menuNode.items[index] = (menuNode.items[index][0], newCondition, menuNode.items[index][2])
    
    # Replaces the result block of a Menu's item
    def ChangeMenuBlock(menuNode, index, newBlock):
        menuNode.items[index] = (menuNode.items[index][0], menuNode.items[index][1], newBlock)
    
    # Adds a caption to a Menu node.
    # A speaker may be included, as a string representing a Character variable.
    def AddMenuCaption(menuNode, caption, who = None, replaceExisting = False):
        if Rentime_Compat_MenuCaption == False:
            raise Exception("Automated Menu caption editing is currently unavailable below Ren'Py 7.3.3.")
        if who != None:
            if menuNode.statement_start == menuNode or replaceExisting == True:
                menuNode.statement_start = renpy.ast.Say(("Rentime.rpy", 0), who, caption, None)
        else:
            iter = 0
            for mLabel, mCond, mBlock in menuNode.items:
                if mBlock == None:
                    if replaceExisting == True:
                        menuNode.items[iter] = (newCaption, mCond, mBlock)
                    return
            menuNode.items.append((caption, "True", None))
    
    # Replaces the text of a Menu's caption
    def ChangeMenuCaption(menuNode, newCaption):
        if Rentime_Compat_MenuCaption == False:
            raise Exception("Automated Menu caption editing is currently unavailable below Ren'Py 7.3.3.")
        if menuNode.statement_start != menuNode:
            menuNode.statement_start.what = newCaption
            return
        else:
            iter = 0
            for mLabel, mCond, mBlock in menuNode.items:
                if mBlock == None:
                    menuNode.items[iter] = (newCaption, mCond, mBlock)
                    return
                iter += 1
        raise Exception("The provided Menu does not have a caption!")
    
    # Changes the speaker of a Menu's caption.
    # 'who' should be a string representing the Character's variable name, or None to remove the speaker.
    def ChangeMenuCaptionSayer(menuNode, who):
        if Rentime_Compat_MenuCaption == False:
            raise Exception("Automated Menu caption editing is currently unavailable below Ren'Py 7.3.3.")
        if menuNode.statement_start != menuNode:
            if who != None:
                menuNode.statement_start.who = who
            else:
                menuNode.items.append((menuNode.statement_start.what, "True", None))
                menuNode.statement_start = menuNode
            return
        else:
            iter = 0
            for mLabel, mCond, mBlock in menuNode.items:
                if mBlock == None:
                    menuNode.statement_start = renpy.ast.Say(("Rentime.rpy", 0), who, mLabel, None)
                    menuNode.items.pop(iter)
                    return
                iter += 1
        raise Exception("The provided Menu does not have a caption.")
    
    # Removes the caption from a Menu
    def RemoveMenuCaption(menuNode):
        if Rentime_Compat_MenuCaption == False:
            raise Exception("Automated Menu caption editing is currently unavailable below Ren'Py 7.3.3.")
        if menuNode.statement_start != menuNode:
            menuNode.statement_start = menuNode
        else:
            iter = 0
            for mLabel, mCond, mBlock in menuNode.items:
                if mBlock == None:
                    menuNode.items.pop(iter)
                    return
                iter += 1
    
    # Provided an If node, gets the entry matching the provided condition and its index.
    def GetIfEntry(ifNode, condition, containing = True):
        # Return the 'else' entry if it is desired and present
        if condition in [None, "else"] and ifNode.entries[-1][0] == None:
            return (ifNode.entries[-1], len(ifNode.entries) - 1)
        
        GetIfEntry_Iter = 0
        for ifEntry in ifNode.entries:
            if ifEntry[0] == condition or (containing == True and condition in ifEntry[0]):
                return (ifEntry, GetIfEntry_Iter)
            GetIfEntry_Iter += 1
        
        return None
    
    # Inserts a new branch into an If node
    # 'condition' should be a string that evaluates to True/False
    # 'result' should be an AST block
    def InsertIfBranch(ifNode, index, condition, result):
        ifNode.entries.insert(index, (condition, result))
    
    # Replaces the condition of an If node's branch
    # 'newCondition' should be a string that evaluates to True/False
    def ChangeIfCondition(ifNode, index, newCondition):
        ifNode.entries[index] = (newCondition, ifNode.entries[index][1])
    
    # Replaces the result of an If node's branch
    # 'newResult' should be an AST block
    def ChangeIfBlock(ifNode, index, newResult):
        ifNode.entries[index] = (ifNode[index][0], newResult)
    


    ############
    # UI
    ############
    
    # Gets the Screen with the specified name.
    # Pass a variant name to get a specific variant of the screen, if it was defined.
    def GetScreen(screenName, variant = None):
        if screenName not in renpy.display.screen.screens_by_name:
            raise KeyError("The screen \"" + screenName + "\" does not exist.")
        if variant not in renpy.display.screen.screens_by_name[screenName]:
            raise KeyError("The \"" + variant + "\" variant of screen \"" + screenName + "\" does not exist.")
        return renpy.display.screen.screens_by_name[screenName][variant]
    
    # Gets the base-level items of a Screen as an array
    def GetScreenItems(screenName):
        return GetScreen(screenName).ast.children
    
    # Scans a UI tree, starting from a base set of >0 nodes, to find a specific element. A Screen object will usually be the base.
    # If a result is found, a tuple containing the result and the branch it's contained in will be returned.
    # Supports three target-matching goals:
    # - "KeyVal":
    #     Expected kwargs: targetKey (string), targetValue (string)
    #     Returns the element with a matching Key/Value pair in its keywords
    # - "Positional":
    #     Expected kwargs: targetPositional (string)
    #     Returns the element with a positional argument matching the provided one.
    #     Checks the 'positional' storage of compatible elements first, and 'positional_values' second.
    # - "IfCond":
    #     Expected kwargs: targetCond (string)
    #     Returns the 'if' element with a condition matching the provided one.
    # - "DispName" (available only on Ren'Py 8):
    #     Expected kwargs: targetDisp (string)
    #     Returns the element of type SLDisplayable whose name (i.e. add, hbox, viewport) matches the provided one.
    #     Particularly useful when paired with the 'offset' setting.
    # Optional kwargs:
    # - containing (bool): causes matching to match any result containing the input, aside from KeyVal's targetKey
    # - offset (int): the first n valid results will be skipped
    def SLSearch(base, goal, **kwargs):
        # Validate entrypoint
        if type(base) is renpy.display.screen.Screen:
            base = base.ast.children
        elif type(base) is renpy.sl2.slast.SLScreen or type(base) is renpy.sl2.slast.SLBlock or issubclass(type(base), renpy.sl2.slast.SLBlock):
            base = base.children
        elif str(type(base)) != "<class 'list'>":
            raise Exception("Invalid starting block specified. Must be either list, Screen, SLScreen or SLBlock(-derived)")
        
        # Check target
        if goal == "KeyVal":
            targetKey = kwargs["targetKey"]
            targetValue = kwargs["targetValue"]
        elif goal == "Positional":
            targetPositional = kwargs["targetPositional"]
        elif goal == "IfCond":
            targetCond = kwargs["targetCond"]
        elif goal == "DispName":
            if Rentime_Compat_DisplayableName == False:
                raise Exception("SLSearch goal \"DispName\" is only available on Ren'Py 8.0.0 and newer (running " + renpy.version_only + ")")
            targetDisplayable = kwargs["targetDisp"].lower()
        else:
            raise Exception("Invalid goal specified. Must be either \"KeyVal\", \"Positional\", or \"IfCond\"")
        
        # Initialize control variables
        storage = {"containing": False, "offset": 0, "result": None, "resultBranch": None}
        
        if "containing" in kwargs:
            storage["containing"] = kwargs["containing"]
        
        if "offset" in kwargs:
            storage["offset"] = kwargs["offset"]
        
        def FoundGoal(item, branch):
            if storage["offset"] > 0:
                storage["offset"] -= 1
            else:
                storage["result"] = item
                storage["resultBranch"] = branch
        
        def SearchBranch(branch):
            if storage["result"] != None:
                return
            
            for branchItem in branch:
                # Evaluate current node against targeting
                if goal == "KeyVal" and hasattr(branchItem, "keyword"):
                    for kwItem in branchItem.keyword:
                        if kwItem[0] == targetKey:
                            if kwItem[1] == targetValue or (storage["containing"] == True and targetValue in kwItem[1]):
                                FoundGoal(branchItem, branch)
                elif goal == "Positional":
                    if hasattr(branchItem, "positional"):
                        for posItem in (branchItem.positional if hasattr(branchItem, "positional") and branchItem.positional != None else []) + (branchItem.positional_values if hasattr(branchItem, "positional_values") and branchItem.positional_values != None else []):
                            if posItem == targetPositional or (storage["containing"] == True and targetPositional in posItem):
                                FoundGoal(branchItem, branch)
                elif goal == "IfCond" and type(branchItem) is renpy.sl2.slast.SLIf:
                    for ifEntry in branchItem.entries:
                        if ifEntry[0] == targetCond or (storage["containing"] == True and targetCond in ifEntry[0]):
                            FoundGoal(branchItem, branch)
                elif goal == "DispName" and type(branchItem) is renpy.sl2.slast.SLDisplayable:
                    if branchItem.name == targetDisplayable:
                        FoundGoal(branchItem, branch)
                
                # Exit the loop if the goal has been found
                if storage["result"] != None:
                    break
                
                # Search sub-branches
                if type(branchItem) is renpy.sl2.slast.SLIf:
                    for ifEntry in branchItem.entries:
                        SearchBranch(ifEntry[1].children)
                        if storage["result"] != None:
                            break
                elif hasattr(branchItem, "block") and branchItem.block != None:
                    if len(branchItem.block.children) > 0:
                        SearchBranch(branchItem.block.children)
                        if storage["result"] != None:
                            break
                elif hasattr(branchItem, "children") and len(branchItem.children) > 0:
                    SearchBranch(branchItem.children)
                    if storage["result"] != None:
                            break
        
        SearchBranch(base)
        return (storage["result"], storage["resultBranch"])
    
    # Creates a new Screen and registers it, similar to CreateBlock for standard scripting
    def CreateScreen(rawRpy, variant=None):
        newAST = renpy.game.script.load_string("Rentime.rpy", rawRpy)[1]
        if newAST == None:
            raise Exception("The provided script block could not be interpreted correctly. Check for script errors in it.")
        renpy.display.screen.screens[newAST[0][1].name[0], variant] = newAST[0][1]
        renpy.display.screen.screens_by_name[newAST[0][1].name[0]][variant] = newAST[0][1]
        return newAST[0][1]
    
    # Places arbitrary screen code at the specified index of a screen or displayable object
    def InsertScreenCode(recipient, rawRpy, index = 0):
        if type(recipient) is renpy.ast.Screen:
            recipient = recipient.screen
        elif type(recipient) is renpy.display.screen.Screen:
            recipient = recipient.ast
        elif type(recipient) not in [renpy.sl2.slast.SLBlock, renpy.sl2.slast.SLScreen] and not hasattr(recipient, "children"):
            raise ValueError("Invalid type of recipient screen \"" + str(type(recipient)) + "\". Must be \"renpy.sl2.slast.SLBlock\", \"renpy.ast.Screen\", \"renpy.display.screen.Screen\", or \"renpy.sl2.slast.SLScreen\"")
        
        if index < 0:
            index = len(recipient.children) + (index + 1)
        
        newAST = renpy.game.script.load_string("Rentime.rpy", "screen insertScreen():\n    " + rawRpy)[1][0][1].screen.children
        recipient.children = recipient.children[0:index] + newAST + recipient.children[index:]
    
    # Places a "use" statement at the beginning of another screen/screen block, to embed a desired screen.
    # The target screen should either be a screen object or the screen's name.
    # Arguments for the use statement, if any, should be included through the useArgs field as a string without enclosing parenthesis (i.e. 'useArgs = "1, True, argThree = "name"').
    # For more granular control over the placement of the use statment, use InsertScreenCode instead.
    def InsertScreenUse(recipient, screen, useArgs = None):
        if type(screen) is renpy.ast.Screen:
            screen = screen.name[0]
        elif type(screen) is renpy.display.screen.Screen:
            screen = screen.ast.name
        elif type(screen) is renpy.sl2.slast.SLScreen:
            screen = screen.name
        elif type(screen) is not str:
            raise ValueError("Invalid type of insert-screen. Must be \"renpy.ast.Screen\", \"renpy.display.screen.Screen\", \"renpy.sl2.slast.SLScreen\", or \"str\"")
        
        rawRpy = "use " + screen
        if useArgs != None:
            useArgs = useArgs.lstrip('(').rstrip(')')
            rawRpy += ("(" + useArgs + ")")
        InsertScreenCode(recipient, rawRpy, 0)
    
    # Changes a positional value of a node
    def ChangeSLNodePositional(node, index, value):
        node.positional[index] = "\"" + value + "\""
        RePrepSLNode(node)
    
    # Provided an SLIf node, gets the branch matching the provided condition and its index.
    def GetSLIfEntry(targetIf, cond, containing = False):
        # Return the 'else' entry if it is desired and present
        if cond in [None, "else"] and targetIf.entries[-1][0] == None:
            return (targetIf.entries[-1], len(targetIf.entries) - 1)
        
        GetSLIfEntry_Iter = 0
        for ifEntry in targetIf.entries:
            if ifEntry[0] == cond or (containing == True and cond in ifEntry[0]):
                return (ifEntry, GetSLIfEntry_Iter)
            GetSLIfEntry_Iter += 1
        
        return None
    
    # Assistant method for quickly replacing the condition of an SLIf node branch
    def ChangeSLIfCondition(targetIf, index, newCondition):
        targetIf.entries[index] = (newCondition, targetIf.entries[index][1])
        RePrepSLNode(targetIf)
    
    # Assistant method for quickly replacing the result of an SLIf node branch
    def ChangeSLIfResult(targetIf, index, newResult):
        targetIf.entries[index] = (targetIf.entries[index][0], newResult)

    # Reruns preparation on an SL2 node. Necessary after making certain changes that require code analysis, such as altering an SLIf branch condition
    def RePrepSLNode(node):
        node.prepare(renpy.pyanalysis.Analysis())



init -1501 python:
    ##############
    # LayeredRen: allows mods to have their files load in place of base game files.
    ##############
    
    # An FSPatch specifies that a target directory located somewhere inside "game" should be considered as a second "game" directory. Any files inside the FSPatch directory will then be layered over the originals.
    # For instance, a few new directories are created under the "game" directory: "mods/MyMod/layer". The "layer" directory contains the subdirectories-and-file "art/charname/character.png", a character graphic meant to replace an existing one. An FSPatch is created, pointing to "mods/MyMod/layer/". Should the game then request "art/charname/character.png", it will instead be provided "mods/MyMod/layer/art/charname/character.png".
    # Typically, a single mod will never need more than one FSPatch.
    # Use LayeredRen_AddFSPatch() to create one.
    class LayeredRen_FSPatch:
        def __init__(self, dirPath, priority, condition):
            self.dirPath = dirPath
            self.priority = priority
            self.condition = condition
            self.files = []
            self.Prepare()
        
        def Prepare(self):
            pathIndex = len(renpy.config.gamedir) + len(self.dirPath) + 1
            for path, subdirectories, files in os.walk(os.path.join(renpy.config.gamedir, self.dirPath)):
                for fileName in files:
                    self.files.append((os.path.join(path, fileName)[pathIndex:].replace('\\', '/')).lstrip('/'))
        
        def EvaluateCondition(self):
            result = renpy.python.py_eval(self.condition)
            if type(result) is bool:
                return result
            return False
    
    # Creates and registers a FSPatch. Requires the subdirectory of the "game" directory to treat as the layered directory
    # For instance, "mods/MyMod/layer/".
    # Optional parameters:
    # - priority (int): if multiple valid patches exist for the same base path, the one with the highest priority will be the only one applied.
    # - condition: a Python expression which must evaluate to a boolean. Determines whether the patch is valid at the time of consideration.
    def LayeredRen_AddFSPatch(dirPath, priority = 0, condition = "True"):
        LayeredRen_FSPatches.append(LayeredRen_FSPatch(dirPath.lstrip('/').lstrip('\\'), priority, condition))
    
    # A FilePatch allows a mod to have a file normally loaded by the game replaced with another.
    # Use LayeredRen_AddFilePatch() to create one.
    class LayeredRen_FilePatch:
        def __init__(self, targetPath, replacementPath, targetDirectory, replacementDirectory, priority, condition):
            self.targetPath = targetPath
            self.replacementPath = replacementPath
            self.targetDirectory = targetDirectory
            self.replacementDirectory = replacementDirectory
            self.priority = priority
            self.condition = condition
        
        def EvaluateCondition(self):
            result = renpy.python.py_eval(self.condition)
            if type(result) is bool:
                return result
            return False
    
    # Creates and registers a FilePatch. Requires the original path and the path it should be substituted with.
    # Optional parameters:
    # - targetDirectory (string): only apply patch if the target is also in the specified archive-directory
    # - replacementDirectory (string or None): the archive-directory to add the path to. Typically an RPA file. Can be None (un-archived), "" (no change), or a string (archive-directory name).
    # - priority (int): if multiple valid patches exist for the same base path, the one with the highest priority will be the only one applied.
    # - condition: a Python expression which must evaluate to a boolean. Determines whether the patch is valid at the time of consideration. Useful for game version checks.
    def LayeredRen_AddFilePatch(targetPath, replacementPath, targetDirectory = "", replacementDirectory = "", priority = 0, condition = "True"):
        LayeredRen_FilePatches.append(LayeredRen_FilePatch(targetPath, replacementPath, targetDirectory, replacementDirectory, priority, condition))
    
    # A DirPatch allows a mod to redirect load calls for any file in a specific path-directory to another path-directory.
    # FilePatches will take precedence over DirPatches if both exist for a single path, unless the DirPatch has higher priority.
    # Use LayeredRen_AddDirPatch() to create one.
    class LayeredRen_DirPatch:
        def __init__(self, targetLeadup, replacementLeadup, targetDirectory, replacementDirectory, priority, condition):
            self.targetLeadup = targetLeadup
            self.replacementLeadup = replacementLeadup
            self.targetDirectory = targetDirectory
            self.replacementDirectory = replacementDirectory
            self.priority = priority
            self.condition = condition
        
        def EvaluateCondition(self):
            result = renpy.python.py_eval(self.condition)
            if type(result) is bool:
                return result
            return False
    
    # Creates and registers a DirPatch. Requires the part of the path to replace, from the beginning to the desired subdirectory, and the equivalent new subpath
    # For instance, any file inside audio/music/ could be loaded from mods/MyMod/music/ instead.
    # Optional parameters:
    # - targetDirectory (string): only apply patch if the target is also in the specified archive-directory
    # - replacementDirectory (string or None): the archive-directory to add the path to. Typically an RPA file. Can be None (un-archived), "" (no change), or a string (archive-directory name).
    # - priority (int): if multiple valid patches exist for the same base path, the one with the highest priority will be the only one applied.
    # - condition: a Python expression which must evaluate to a boolean. Determines whether the patch is valid at the time of consideration.
    def LayeredRen_AddDirPatch(targetLeadup, replacementLeadup, targetDirectory = "", replacementDirectory = None, priority = 0, condition = "True"):
        LayeredRen_DirPatches.append(LayeredRen_DirPatch(targetLeadup, replacementLeadup, targetDirectory, replacementDirectory, priority, condition))
    
    
    
    ########################################
    # LayeredRen internals - do not touch! #
    ########################################
    
    LayeredRen_FSPatches = []
    LayeredRen_FilePatches = []
    LayeredRen_DirPatches = []
    
    # Hooks Ren'Py's file-load function to apply patches
    def LayeredRen_LoadPrefix(name, directory = None, tl = True):
        # Perform leading-slash-strip early
        name = name.lstrip('/')
        
        # Check if any FSPatches exist which include a file with this path
        fsCandidate = None
        for fsPatch in LayeredRen_FSPatches:
            if name in fsPatch.files:
                if fsPatch.EvaluateCondition() == True:
                    if fsCandidate == None or fsPatch.priority > fsCandidate.priority:
                        fsCandidate = fsPatch
        
        # Check if any FilePatches exist for this path
        fileCandidate = None
        for filePatch in LayeredRen_FilePatches:
            if name == filePatch.targetPath and (filePatch.targetDirectory == "" or directory == filePatch.targetDirectory):
                if filePatch.EvaluateCondition() == True:
                    if fileCandidate == None or filePatch.priority > fileCandidate.priority:
                        fileCandidate = filePatch
        
        # Check if any DirPatches exist for this path
        dirCandidate = None
        for dirPatch in LayeredRen_DirPatches:
            if len(dirPatch.targetLeadup) < len(name) and name.startswith(dirPatch.targetLeadup):
                if dirPatch.targetDirectory == "" or directory == dirPatch.targetDirectory:
                    if dirPatch.EvaluateCondition() == True:
                        if dirCandidate == None or dirPatch.priority > dirCandidate.priority:
                            dirCandidate = dirPatch
        
        # Apply the winning patch, if any
        if fileCandidate != None:
            if (dirCandidate == None or fileCandidate.priority >= dirCandidate.priority) and (fsCandidate == None or fileCandidate.priority >= fsCandidate.priority):
                name = fileCandidate.replacementPath
                if fileCandidate.replacementDirectory != "":
                    directory = fileCandidate.replacementDirectory
        if fsCandidate != None:
            if (fileCandidate == None or fsCandidate.priority > fileCandidate.priority) and (dirCandidate == None or fsCandidate.priority >= dirCandidate.priority):
                name = (os.path.join(fsCandidate.dirPath, name)).replace('\\', '/')
                directory = None
        if dirCandidate != None:
            if (fileCandidate == None or dirCandidate.priority > fileCandidate.priority) and (fsCandidate == None or dirCandidate.priority > fsCandidate.priority):
                name = dirCandidate.replacementLeadup + name[len(dirCandidate.targetLeadup):]
                if dirCandidate.replacementDirectory != "":
                    directory = dirCandidate.replacementDirectory
        
        if Rentime_Compat_LayeredRen_LoadSignature == 0: # Ren'Py >= 7.6.0
            return LayeredRen_LoadOrig(name, directory, tl)
        elif Rentime_Compat_LayeredRen_LoadSignature == 1: # Ren'Py >= 6.99.13
            return LayeredRen_LoadOrig(name, tl)
        elif Rentime_Compat_LayeredRen_LoadSignature == 2:
            return LayeredRen_LoadOrig(name)
        else:
            raise Exception("Rentime: Unhandled signature for renpy.loader.load! Please report this.")
    LayeredRen_LoadOrig = renpy.loader.load
    renpy.loader.load = LayeredRen_LoadPrefix
    
    # Hooks the live-reload function to undo hooks prior to a reload. This is necessary as reloading does not reset modifications to engine internals.
    def LayeredRen_ReloadPrefix():
        # Remove load hook
        global LayeredRen_LoadOrig
        renpy.loader.load = LayeredRen_LoadOrig
        
        # Remove this hook
        global LayeredRen_ReloadOrig
        renpy.exports.reload_script = LayeredRen_ReloadOrig
        
        LayeredRen_ReloadOrig()
    LayeredRen_ReloadOrig = renpy.exports.reload_script
    renpy.exports.reload_script = LayeredRen_ReloadPrefix


#############
# Init
#############
init -1510 python:
    import os
    
    # Version support helpers
    Rentime_Compat_HasTranslateSay = hasattr(renpy.ast, "TranslateSay")
    Rentime_Compat_LayeredRen_LoadSignature = 0
    Rentime_Compat_MenuIArgs = "item_arguments" in renpy.ast.Menu.__slots__
    Rentime_Compat_DisplayableName = renpy.version_only >= "8.0"
    Rentime_Compat_MenuCaption = renpy.version_only >= "7.3.3"
    
    if sys.version_info.major == 2:
        # Rentime_Compat_LayeredRen_LoadSignature
        if "directory" not in renpy.loader.load.func_code.co_varnames:
            Rentime_Compat_LayeredRen_LoadSignature += 1
            if "tl" not in renpy.loader.load.func_code.co_varnames:
                Rentime_Compat_LayeredRen_LoadSignature += 1
    elif sys.version_info.major == 3:
        # Rentime_Compat_LayeredRen_LoadSignature
        if "directory" not in renpy.loader.load.__code__.co_varnames:
            Rentime_Compat_LayeredRen_LoadSignature += 1
            if "tl" not in renpy.loader.load.__code__.co_varnames:
                Rentime_Compat_LayeredRen_LoadSignature += 1
    
    #############
    # Declare mod
    #############
    Rentime_version = "1.0.0"