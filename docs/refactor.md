# Technical Debt & Refactor Ideas

## 🏗️ Architecture & Component Redesign (Brainstorming)
* **Decouple UI from Session**: Should we split `ImageSession` into a pure data wrapper and extract a `ImageRepository` to handle file changes? 
ImageSession class. Right now, it handles directory navigation, loading files, extracting metadata, and caching objects for the GUI.
if you want to add a "Batch Processing" feature that crops 100 images automatically without launching the GUI. 
Because ImageSession is tightly bound to GUI elements like QPixmap and ImageQt, trying to use it for a headless command-line script might cause crashes or require weird workarounds. You are now paying "interest" in wasted time.
The Clean Way (Paying it off): You spend a day breaking ImageSession into two smaller classes: a pure FileNavigator and a GuiCacheManager. Now, your code is modular, and building the batch processor becomes effortless.
I could also just write a another manager for batch operations avoiding ImageSession completely.

* **State Machine for Crop Engine**: Consider converting `CropSettings` and `CropResult` handling into a formal finite state machine (FSM) if multi-step adjustments get too messy.



## 🧪 Icebox & Experimental Ideas (Not Guaranteed)

### Keyboard controller
### Mouse controller
### Preview manager

### Move helper math to  geometry.py
 (or/+ (canvas_translator.py / selection_manager.py) )
    snapping
    coordinate conversion
    scaling
    aspect ratios
    geometry

### Reduce widget coupling 
instead of self.main_app...
For example FloatingZoomPreview directly accesses the main window.
Use
- signals
- callbacks
That makes widgets reusable.

### 14. Introduce an event bus ⭐⭐⭐☆☆
```
crop changed
↓
update HUD
↓
update preview
↓
update telemetry
↓
update spinboxes
↓
update labels
```
emit a single event:
`crop_changed`
Each component updates itself independently.


## 🛠️ Low-Level Code Cleanup & Classes
* **Custom Type Aliases**: Implement `type Coordinate = tuple[int, int]` across `DisplayState` to replace separate X/Y fields.
