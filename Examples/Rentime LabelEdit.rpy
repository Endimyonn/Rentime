# This example serves to demonstrate many of the script-related capabilities of Rentime.
# It defines a label, and then uses Rentime to heavily modify it.

define RTChar = Character("Rentime Narrator")
label manipulatedLabel:
    "This is a label in the base game."
    with Pause(1)
    "It contains a certain amount of unmodified content."
    if 1 == 0:
        "This message should never be shown."
    else:
        "This message should always be shown."
    label manipulatedLabel.choice:
        $ RenTime_LabelEdit_MenuIterative()
        menu:
            "Choice 1":
                "You selected choice 1."
                jump manipulatedLabel.choice
            
            "Choice 2":
                "You selected choice 2."
                jump manipulatedLabel.choice
            
            "Secret third choice" if 0 == 1:
                "Congratulations! This choice shouldn't be possible."
                jump manipulatedLabel.choice
            
            "Nevermind":
                pass
    "Now we'll see two menus with captions, with and without a speaker assigned."
    menu:
        "This menu uses a speaker-less caption."
        "Okay":
            pass
    menu:
        RTChar "This menu uses a caption with a speaker."
        "Okay":
            pass
    "All done!"
    $ renpy.full_restart()

# Edit the label
init python:
    def Rentime_LabelEdit():
        # Get the label
        findLabel = GetLabel("manipulatedLabel")
        
        # Change what someone says
        getSay = FindNode(findLabel, "Say", "unmodified content")
        getSay.what = "It contains some modified content."
        
        # Change an If condition
        getIf = FindNode(findLabel, "If", "1 == 0")
        ChangeIfCondition(getIf, 0, "2 in [1,2,3]")
        
        # Change a Menu entry's label
        getMenuEntry = FindNode(findLabel, "Menu", "Choice 1")
        ChangeMenuLabel(getMenuEntry, 1, "Choice B")
        
        # Modify the result of a Menu entry
        FindNode(getMenuEntry.items[1][2][0], "Say", "choice 2").what = "You selected choice B." # tuple index 2 is the AST block of the choice
        
        # Change a Menu condition
        ChangeMenuCondition(getMenuEntry, 2, "True")
        
        # Add a new Menu item
        InsertMenuItem(getMenuEntry, "New Choice (4th)", "True", "\"Wow! This choice doesn't exist in the unedited label.\"\njump manipulatedLabel.choice", -1)
        
        # Change the caption of a Menu
        if Rentime_Compat_MenuCaption == True: # caption editing is unavailable below Ren'Py 7.3.3
            AddMenuCaption(getMenuEntry, "Pick your next choice... if you dare!")
        
        # Insert a new block
        additionalBlock = '"Want to know something neat?"\n'
        additionalBlock += '"This text doesn\'t exist in the base game either."'
        InsertBlock(getMenuEntry, additionalBlock)
    Rentime_LabelEdit()
    
    RenTime_LabelEdit_TimesMenuVisited = 0
    def RenTime_LabelEdit_MenuIterative():
        global RenTime_LabelEdit_TimesMenuVisited
        RenTime_LabelEdit_TimesMenuVisited += 1
        getMenu = FindNode(GetLabel("manipulatedLabel.choice"), "Menu", "Choice 1")
        if Rentime_Compat_MenuCaption == True: # caption editing is unavailable below Ren'Py 7.3.3
            ChangeMenuCaption(getMenu, "Pick your next choice. (round " + str(RenTime_LabelEdit_TimesMenuVisited) + ")")