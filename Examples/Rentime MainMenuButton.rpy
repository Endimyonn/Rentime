# Adds an extra button to the main menu that calls a specific label.
# In this case, we call the label from "Rentime LabelEdit.rpy"
# This targets a relatively "stock" menu screen layout. Depending on the game this is used in, on account of menu customizations, the button might not show unless a menu is opened (i.e. preferences), or it may not show at all.
init python:
    def Rentime_MMButton_Init():
        # Get the screen we want to add to.
        targetScreen = GetScreen("navigation")
        
        # Get the target node inside the screen. We're looking for an If statement with a specific condition.
        # SLSearch returns a tuple containing the result and the block it belongs to, so we select the result from that.
        getIf = SLSearch(targetScreen, "IfCond", targetCond = "main_menu")[0]
        
        # Isolate the specific entry we want to modify.
        # GetSLIf entry returns a tuple containing the result and its index among the If statement's entries.
        targetEntry = GetSLIfEntry(getIf, "main_menu")[0]
        
        # Insert a new statement at the end of the block that gets displayed if the If entry goes through.
        # For argument 1, an entry is a tuple containing the condition and result block, so we select the block of the above entry.
        InsertScreenCode(targetEntry[1], "textbutton \"Rentime test\" action Jump(\"manipulatedLabel\")", -1)
    Rentime_MMButton_Init()