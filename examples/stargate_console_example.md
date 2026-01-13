# Stargate Atlantis Override Console - Prop Modeling Example

This example demonstrates the new prop modeling capabilities of the Fusion 360 MCP Server, specifically designed for the Stargate Atlantis Override Console use case.

## Overview

The Override Console is a stacked, stepped, segmented structure with:
- Multiple body segments (base, mid, frame, top)
- Deep subtractive geometry (zigzag recesses, panel pockets)
- Circular patterns for hex-symmetric features
- Edge-selective filleting (sharp seams, soft edges)
- Precise body tracking and naming

## Workflow Example

### 1. Setup and Body Segmentation

```python
# Delete any existing geometry
delete_all()

# Create stacked body segments
# Base pedestal - 20mm = 2.0 cm
base = extrude(value=2.0, angle=0.0)
# Returns: {"success": True, "body_id": "...", "body_name": "Body1"}
rename_body(body_id=base["body_id"], new_name="BasePedestal")

# Lower vent block - 200mm = 20.0 cm  
lower = extrude(value=20.0, angle=0.0)
rename_body(body_id=lower["body_id"], new_name="LowerVent")

# Mid body - 500mm = 50.0 cm
mid = extrude(value=50.0, angle=0.0)
rename_body(body_id=mid["body_id"], new_name="MidBody")

# Zigzag frame - 300mm = 30.0 cm
frame = extrude(value=30.0, angle=0.0)
rename_body(body_id=frame["body_id"], new_name="ZigzagFrame")

# Top cap - 105mm = 10.5 cm
cap = extrude(value=10.5, angle=0.0)
rename_body(body_id=cap["body_id"], new_name="TopCap")

# Verify all bodies were created
bodies = list_bodies()
# Returns: {"success": True, "count": 5, "bodies": [...]}
```

### 2. Apply Subtractive Features (BEFORE Shelling)

```python
# Select the ZigzagFrame body for feature work
frame_body = get_active_body()  # or find by name in list_bodies()

# Create sketch on front face of the frame
sketch_on_face(body_index=3, face_index=0)  # ZigzagFrame front face

# Draw zigzag pattern
draw_lines(
    points=[
        [0, 0, 0],
        [2, 0, 0],
        [3, 1, 0],
        [4, 0, 0],
        [5, 1, 0],
        [6, 0, 0],
        [8, 0, 0],
        [8, 2, 0],
        [0, 2, 0],
        [0, 0, 0]
    ],
    plane="XY"
)

# Get sketch ID for explicit targeting
zigzag_sketch = get_active_sketch()
# Returns: {"success": True, "sketch_id": "...", "sketch_name": "Sketch1"}

# Create pocket with explicit targeting (10mm = 1.0 cm deep)
pocket_result = pocket_recess(
    depth=1.0,
    body_id=3,  # ZigzagFrame
    sketch_id=zigzag_sketch["sketch_id"]
)
# Returns: {"success": True, "depth": 1.0, "sketch_name": "Sketch1", "body_name": "ZigzagFrame"}
```

### 3. Create Side Panel Recesses

```python
# Create sketch on side face
sketch_on_face(body_index=3, face_index=2)  # Side face

# Draw hexagonal panel recess
draw_polygon(sides=6, radius=3.0, x=0, y=0, z=0, plane="XY")

# Get the sketch
panel_sketch = get_active_sketch()

# Create pocket (5mm = 0.5 cm deep)
pocket_recess(depth=0.5, body_id=3, sketch_id=panel_sketch["sketch_id"])
```

### 4. Apply Circular Pattern (Real Features, Not Cosmetic)

```python
# Pattern the side panel feature around the axis
pattern_result = circular_pattern(plane="XY", quantity=6, axis="Z")

# Verify pattern was created
# Returns: {
#   "applied": True,
#   "success": True,
#   "instance_count": 6,
#   "pattern_id": "...",
#   "pattern_name": "CircularPattern1",
#   "axis": "Z",
#   "total_angle": 360
# }

print(f"Created {pattern_result['instance_count']} panel instances")
```

### 5. Shell the Body (AFTER All Features)

```python
# Now shell the frame body with 3mm = 0.3 cm walls
shell_body(thickness=0.3, faceindex=0)

# List bodies to verify
final_bodies = list_bodies()
```

### 6. Edge-Selective Filleting

```python
# Get edges for the frame body
# For prop accuracy: Sharp vertical seams, soft panel frames

# Fillet frame edges with 10mm = 1.0 cm radius (specific edges only)
frame_fillet = fillet_edges(
    radius=1.0,
    edges=[0, 2, 4, 6]  # Only horizontal edges
)
# Returns: {
#   "success": True,
#   "successful_fillets": 4,
#   "failed_edges": 0,
#   "radius": 1.0
# }

# Fillet cap edges with smaller 5mm = 0.5 cm radius
cap_fillet = fillet_edges(
    radius=0.5,
    edges=[10, 11, 12, 13]  # Top cap edges
)
```

### 7. Boolean Operations (If Needed)

```python
# If combining separate bodies
boolean_operation(operation="join")

# Verify final body count
final_check = list_bodies()
```

### 8. Export for Manufacturing

```python
# Export as STEP for further CAD work
export_step(name="StargateConsole_CAD")

# Export as STL for 3D printing
export_stl(name="StargateConsole_Print")
```

## Key Features Demonstrated

### 1. Body ID Tracking
- Every `extrude()` returns `body_id` for precise tracking
- `rename_body()` for semantic naming
- `list_bodies()` to verify all components

### 2. Explicit Feature Targeting
- `pocket_recess(depth, body_id, sketch_id)` - no implicit behavior
- `get_active_sketch()` to verify sketch state
- `sketch_on_face(body_index, face_index)` for precise placement

### 3. Pattern Confirmation
- `circular_pattern()` returns detailed JSON:
  - `applied`: boolean success
  - `instance_count`: actual number created
  - `pattern_id`: for future reference

### 4. Edge-Selective Filleting
- `fillet_edges(radius, edges=[...])` for specific edges only
- Preserves sharp seams while softening others
- Returns success count for verification

### 5. Mandatory Feature Order
- ✅ Create solids
- ✅ Apply all features (pockets, cuts, patterns)
- ✅ Shell (if needed)
- ✅ Fillet edges
- ✅ Export

## Validation Checklist

After running this workflow, the exported STL should show:

- ✅ Deep front zigzag recess (10mm depth)
- ✅ Six real side panel cavities (not cosmetic)
- ✅ Stepped silhouette with 5 distinct body segments
- ✅ Beveled top and base edges
- ✅ 3mm wall thickness throughout
- ✅ Sharp vertical seams preserved
- ✅ Soft horizontal panel edges

## Measurements

All measurements in cm (Fusion units):
- Base: 2.0 cm (20mm)
- Lower: 20.0 cm (200mm)
- Mid: 50.0 cm (500mm)
- Frame: 30.0 cm (300mm)
- Cap: 10.5 cm (105mm)
- Wall thickness: 0.3 cm (3mm)
- Frame fillet: 1.0 cm (10mm)
- Cap fillet: 0.5 cm (5mm)
- Pocket depth: 1.0 cm (10mm) front, 0.5 cm (5mm) sides

## Notes

- This example uses the new explicit ID-based targeting system
- All features are applied before shelling (mandatory order)
- Circular patterns create real geometry, not just visual copies
- Edge selection allows precise control over which edges are filleted
- Body tracking enables complex multi-segment modeling
