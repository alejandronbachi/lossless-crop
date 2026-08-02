
# Lossless Crop

## Use case
This application is useful to quickly crop several images in a directory one after the other.

## Supported Formats
- **JPEG**: Lossless or Lossy cropping modes
- **PNG**: Lossless 
- **BMP**: Lossless
- **WebP**: Lossy

## A note on lossless cropping
Grid snapping  is required to perform lossless a crop on a *JPEG* picture, that happens  JPEG images group pixels into blocks called Minimum Coded Units (MCUs). The crop boundaries must align with these blocks to perform cropping without recompression and quality loss.
That is the reason that when you select engine lossless on a JPEG picture the selected area to crop will jump around to adjust to the closest MCU blocks. If you do not want this, you can use the pixel-perfect engine which is lossy but lets use choose your cropping area freely.
*PNG* or *BMP* cropping is always lossless and doesn't require snapping.
*WebP* in this application is handled as lossy cropping.

## Basic Workflow
1. Open a directory with images 
2. Draw selection over the image
3. Crop and move to the next image

## Toolbar Options
### Engine
- **Lossless**: Uses jpegtran engine to perform lossless cropping of JPEG images, if image its not a valid *JPEG* this option is ignored.
- **Pixel-Perfect**: Uses Pillow engine to crop, either with some minor quality loss for *JPEG* and *WebP* or losslessly for *PNG* and *BMP*

### Forced Ratio
This option enforce an aspect ratio on the cropping box, available options:
- Freeform
- Source Ratio
- 1:1 Square
- 16:9 Widescreen
- 4:3 Standard

### Snapping Feedback
Switch how the grid snapping is shown to the user.
This only applies to lossless cropping, meaning that Lossless engine must be selected and a valid JPEG picture.
there are 3 options:
- **Real Time Snap:** Snapping is retrofitted while the user is drawing the cropping area
- **Post Release Snap**: Snapping is only shown when the user finish drawing
- **Ghosting**: Another box is drawn while the user draws that shows the snapped grid

### Cropping area manual Inputs
The spinboxes can be used to input the desired cropping area size.
*Important*: For the values to register the user must press enter or leave the spinboxes edit fields.

### Keep selection
Useful to carry the selection box from one image to the other if cropping sizes are expected to be similar

### Overwrite
Activating this option overwrites the source file after cropping

### Settings Gear
Opens the settings drawer

## Settings drawer
Provides many visibility and persistence options.
### General settings
- Save settings : persist the user settings and reload them next time the app is used.
- Auto-open last folder: open last used working directory on app start up
- Fit preview: changes how the image is shown in the preview hud. Activating it shows the complete selected area.
- Dark Theme: enables dark theme. Light theme is applied otherwise

### Show / Display
Affects what it's shown or hidden in the user interface

### Layout Memory
- Main Window: reload main application window size and position on app load.
- Preview HUD: reload preview HUD size and position on app load.

## Menu Bar
The menu bar can be toggled with *Alt*. 
Regular commands are explained in the commands section, here only the special actions are explained.

- File -> See Logs: Open the folder with the application logs for the user to read them, if needed.
- Recent -> Directory : Opens the selected directory from the recent list.
- Help -> User Manual: shows you this user manual.
- Help -> About: Displays about window.

## Keyboard Global Shortcuts

- **Space** : Crop & Next
- **S**: Crop & Stay
- **O** : Open Directory
- **I** : Open Image
- **F/D** : Skip Forward
- **B/A**: Skip Backward
- **R** : Rotate Clockwise
- **P/Q** : Toggle Preview
- **Alt**  : Toggle Menu Bar
- **Esc**: Exit App

## Mouse actions

**Left-Click Drag**: Draw Box
**Right-Click Drag**: Move Box
**Middle-Click**: Crop
**Scroll**: Navigate


## Commands
There several ways to perform the same actions in the application, choose whichever suits you best
- *Open Directory*: Opens a folder with images and loads it in the application. Must contain valid images.
- *Open Image*: Lets you choose an individual image to open the directory at the specific image.
- *Skip forward*: Move to the next image
- *Skip backward*: Move to the next image
- *Crop*: Crop the selected area
- *Crop & Next*: Crops and skips forward
- *Rotate*: Rotate the image clockwise
- *Exit*: Quits the application

## Drag and Drop Support
- Dragging a directory into the app is the same as Open Directory command
- Dragging a picture into the app is the same as Open Image command

## Toolbar Icons
On the left of the toolbar the icons can be used to trigger Open Directory, Open Image, Crop, Crop & Next and Rotate in that order of appeareance.
