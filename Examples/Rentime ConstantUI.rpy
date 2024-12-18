# This mod defines a screen that shows a box in the corner of the screen
# It then modifies the game to ensure it shows at all times.
# Finally, it modifies the screen itself to add text to it.

# Define the screen
init screen Rentime_ConstantUI_Screen():
    zorder 9999
    
    $ position = int(config.screen_width / 40)
    $ xSize = int(config.screen_width / 8)
    $ ySize = int(xSize / 3)
    
    frame area (position, position, xSize, ySize) background Solid("#ffffff")

# Apply modifications
init python:
    # Modify the game to show the screen at all times
    def Rentime_ConstantUI_ApplyHooks():
        # Script line to show the screen
        insertCode = "show screen Rentime_ConstantUI_Screen"
        
        # Insert the script line at key labels
        # Not every game uses all of these, so we individually check if they exist.
        # The screen may not show depending on which (if any) are missing
        InsertBlock(GetLabel("start"), insertCode)
        if renpy.has_label("splashscreen"):
            # A label object counts as an AST node (the root of a tree), so we can insert between it and its first node.
            InsertBlock(GetLabel("splashscreen"), insertCode)
        if renpy.has_label("main_menu"):
            InsertBlock(GetLabel("main_menu"), insertCode)
        if renpy.has_label("before_main_menu"):
            InsertBlock(GetLabel("before_main_menu"), insertCode)
        if renpy.has_label("after_load"):
            InsertBlock(GetLabel("after_load"), insertCode)
        if renpy.has_label("after_warp"):
            InsertBlock(GetLabel("after_warp"), insertCode)
    
    # Modify the screen to add text inside
    def Rentime_ConstantUI_EditScreen():
        # Get the screen to be modified
        targetScreen = GetScreen("Rentime_ConstantUI_Screen")
        
        # Scan the screen for the 'frame' displayable.
        # We select element 0 of the return value because SLSearch returns a tuple containing the result and the block it's contained in (to allow context-based operations). We don't need the block for this.
        targetFrame = None
        if renpy.version_only >= "8.0.0":
            # Searching by displayable type became possible in Ren'Py 8.0.0, so we do that in this case if possible.
            targetFrame = SLSearch(targetScreen, "DispName", targetDisp = "frame")[0]
        else:
            # Search by a key-value property we know the frame has
            targetFrame = SLSearch(targetScreen, "KeyVal", targetKey = "background", targetValue = "Solid(\"#ffffff\")")[0]
        
        # This will be compiled into a new SLAST node
        newElement = "text \"Rentime\" xalign 0.5 yalign 0.5 color \"#000000\""
        
        # Insert the element into the frame at index 0
        # (InsertScreenCode does the compiling for us)
        InsertScreenCode(targetFrame, newElement, 0)
        
        # Bonus: it was split up for clarity, but all of this could be done in a single line!:
        # InsertScreenCode(SLSearch(GetScreen("Rentime_ConstantUI_Screen"), "DispName", targetDisp = "frame")[0], "text \"Rentime\" xalign 0.5 yalign 0.5 color \"#000000\"", 0)
        
        # Bonus 2: let's modify the text we just added.
        targetText = targetFrame.children[0]
        # Due to how Displayables work, we use Rentime's helper function to ensure that the node gets re-analyzed and updated following the text edit.
        # If this is done mid-game, you may need to rebuild the gui for changes to reflect.
        ChangeSLNodePositional(targetText, 0, targetText.positional[0][1:-1] + "!")
    
    # The above functions exist because if we were to run them directly under the init python statement, any variables
    # defined in them would become part of the global store. Having them be local to functions keeps things clean.
    Rentime_ConstantUI_ApplyHooks()
    Rentime_ConstantUI_EditScreen()