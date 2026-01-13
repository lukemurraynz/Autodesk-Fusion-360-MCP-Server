# Known Limitations and Workflow Constraints

This document outlines known limitations of the Fusion MCP integration and best practices to work around them.

## Sketch and Face Topology Issues

### Issue: Sketch Re-creation on Same Face

**Problem:** After creating and closing a sketch on a face, attempting to create another sketch on the same face can fail silently.

**Why:** Fusion's API sometimes rejects creating multiple sketches on the same face in rapid succession, particularly after topology changes.

**Workaround:**

- Use different faces for sequential sketches when possible
- Add delays between operations (though this is not ideal for automation)
- Use work planes for additional sketching surfaces

### Issue: Face Topology Changes After Pockets

**Problem:** When a pocket/recess is applied to a body, the face geometry changes, making face_index references stale. Subsequent operations referencing the old face index will fail or target wrong faces.

**Why:** Fusion regenerates face indices after boolean operations (cuts, pockets, etc.). The face you referenced as index 0 might now be index 3, or might not exist at all.

**Workaround:**

- Complete all sketches on a face before applying pockets
- Re-query face indices after topology changes using `list_bodies()`
- Use body naming to track geometry: `rename_body()` before operations
- Consider using construction planes instead of faces for reference

### Issue: Rapid-Fire Operations

**Problem:** Multiple sequential sketch→close→pocket operations cause silent failures. The operations appear to complete but don't actually modify the geometry.

**Why:** Fusion's internal state management can't keep up with rapid API calls. The geometry engine needs time to process topology changes.

**Workaround:**

- Batch similar operations together
- Allow time between major topology changes
- Verify results with `list_bodies()` after critical operations
- Use explicit body_id and sketch_id parameters in `pocket_recess()`

### Issue: Limited Sketch Geometry

**Problem:** Complex geometry operations (zigzag patterns, multi-segment lines in same sketch) often return empty responses or only create partial geometry.

**Why:** The API may have limitations on complexity within a single sketch operation, or there may be ordering issues with curve creation.

**Workaround:**

- Break complex sketches into multiple simple sketches
- Create profiles separately and combine with loft/sweep
- Use simpler geometry patterns (rectangles, circles) instead of complex polylines

## Shell Operation Failures

### Issue: Shell Compute Errors - ASM_LOP_HOL_MULTI_SHELL

## Shell Operation Failures

### Issue: Generic API Failure - ASM_API_FAILED

**Problem:** Shell operations fail with `RuntimeError: Shell5 / Compute Failed // ASM_API_FAILED - The operation failed`

**Why:** Generic Fusion API failure, typically caused by:

- Invalid face selection for the specific geometry
- Body geometry is not a valid closed solid
- Face topology incompatibility with shell operation
- Complex geometry that Fusion's solver cannot process
- Face index does not reference a valid removable face

**Root Cause Analysis:**

- Not all faces can be shelled - some are internal or critical to geometry
- Complex geometry with many features may have unstable face topology
- The specific face selected may be geometrically incompatible with shelling
- Body may have topology issues from previous operations

**Solutions (in order of effectiveness):**

1. **Try different face indices** (Most effective):

   ```python
   # Systematically test each face
   for face_index in range(6):  # 0-5 for simple box
       result = shell_body(thickness=0.1, faceindex=face_index)
       if result.get("success"):
           print(f"Success on face {face_index}")
           break
       else:
           undo()
   ```

2. **Reduce thickness slightly**:

   ```python
   # Even if thickness seems small, smaller often helps
   undo()
   shell_body(thickness=0.08, faceindex=0)
   shell_body(thickness=0.05, faceindex=0)  # Extremely thin
   ```

3. **Verify body geometry**:

   ```python
   # Check that body is valid
   bodies = list_bodies()
   history = get_feature_history(body_id=0)

   # Look for failed operations in history
   failed = [f for f in history["features"] if f["status"] == "failed"]
   if failed:
       print("Body has failed features - rebuild recommended")
   ```

4. **Use alternative approach**:

   ```python
   # If shell fails persistently, create hollow geometry differently
   # Instead of shelling, extrude a thin-walled profile
   extrude_thin(value=5.0, thickness=0.1)
   ```

5. **Rebuild geometry if needed**:
   ```python
   # If body is corrupted or too complex, start fresh
   delete_all()
   # Recreate with simpler geometry
   # Avoid complex features before shelling
   ```

**Diagnostic approach:**

```python
# Test shell operation systematically
status = check_shell_status(body_id=0)
if status["has_shell"]:
    print("Already shelled")
else:
    # Try systematically
    thicknesses = [0.05, 0.08, 0.1, 0.15, 0.2]
    for thickness in thicknesses:
        for face in range(6):
            result = shell_body(thickness=thickness, faceindex=face)
            if result.get("success"):
                print(f"✓ Success: thickness={thickness}cm, face={face}")
                exit()
            undo()
    print("✗ No successful shell found - use extrude_thin() instead")
```

**Error is now detected with systematic troubleshooting steps.**

---

### Issue: Shell Thickness Too Large - ASM_RBI_NO_LUMP_LEFT / Meaningful Shape Change

**Problem:** Shell operations fail with:

- `RuntimeError: Shell4 / Compute Failed // ASM_RBI_NO_LUMP_LEFT`
- `RuntimeError: The operation does not cause a meaningful shape change`

**Why:** The shell thickness is too large for the body. Walls thicker than the available material causes the operation to fail. This is a fundamental CAD constraint.

**Root Cause Analysis:**

- Shell thickness removes material inward from selected face
- If thickness > body dimensions, no valid geometry remains
- Example: 5cm body with 0.5cm shell → removes too much → fails

**Solutions (in order of effectiveness):**

1. **REDUCE THICKNESS (Most Common Fix)**:

   ```python
   # WRONG - too thick
   shell_body(thickness=0.5, faceindex=0)    # ❌ Fails
   shell_body(thickness=0.3, faceindex=0)    # ❌ May fail

   # CORRECT - start small
   shell_body(thickness=0.1, faceindex=0)    # ✅ 1mm - almost always works
   shell_body(thickness=0.15, faceindex=0)   # ✅ 1.5mm - safe
   shell_body(thickness=0.2, faceindex=0)    # ✅ 2mm - medium thickness
   ```

2. **Try different face indices**:

   ```python
   # If faceindex=0 fails, try removing different face
   undo()
   shell_body(thickness=0.1, faceindex=1)  # Try face 1

   # If still fails, try face 2, 3, 4, 5
   # Not all faces may work - experiment systematically
   ```

3. **Use extrude_thin() as alternative**:

   ```python
   # If shell consistently fails, create hollow geometry differently
   # Instead of shelling existing body, extrude a thin-walled profile
   draw_box(10, 10, 5, 0, 0, 0, "XY")
   extrude_thin(value=5.0, thickness=0.1)  # Thin walls from sketch
   ```

4. **Increase body size** (if possible):
   ```python
   # Larger bodies tolerate thicker shells better
   draw_box(20, 20, 10, 0, 0, 0, "XY")      # Bigger box
   shell_body(thickness=0.2, faceindex=0)    # Now 0.2cm works
   ```

**Thickness Guidelines:**

- **Recommended starting point:** 0.1 cm (1mm)
- **Safe range:** 0.1-0.2 cm (1-2mm)
- **Maximum:** ~5% of smallest body dimension
- **Rule of thumb:** If error occurs, REDUCE thickness by 50%

**Validation approach:**

```python
# Always check for errors and adapt
result = shell_body(thickness=0.2, faceindex=0)
if not result.get("success"):
    print(f"Failed: {result.get('message')}")
    if "lump" in result.get("message", "").lower() or "meaningful" in result.get("message", "").lower():
        # Thickness issue - try smaller
        undo()
        shell_body(thickness=0.1, faceindex=0)
```

**Error is now detected with adaptive suggestions.**

## Shell Operation Workflow Errors

### Issue: Already Shelled

**Problem:** Shell operations fail with `RuntimeError: Shell3 / Compute Failed // ASM_LOP_HOL_MULTI_SHELL - The selected body appears to have already been shelled`

**Why:** Fusion 360 does not allow shelling a body that has already been shelled. This is a fundamental limitation of the CAD kernel.

**Solutions:**

1. **Prevention (Recommended)**: Use `check_shell_status(body_id)` before calling `shell_body()`:

   ```python
   status = check_shell_status(body_id=0)
   if not status["has_shell"]:
       shell_body(thickness=0.1, faceindex=0)
   else:
       print("Body already shelled - skipping")
   ```

2. **Recovery**: If you accidentally shell twice:

   ```python
   # Option A: Undo the failed operation
   undo()

   # Option B: Start fresh
   delete_all()
   # Rebuild your model
   ```

3. **Workflow**: Always shell LAST in your modeling sequence:

   ```python
   # CORRECT ORDER:
   # 1. Create base geometry
   draw_box(10, 10, 5, 0, 0, 0, "XY")

   # 2. Add all features (pockets, patterns, etc.)
   sketch_on_face(body_index=0, face_index=4)
   draw_circle(radius=2, x=0, y=0, z=0)
   pocket_recess(depth=1.0, body_id=0)
   circular_pattern(quantity=6, axis="Z", plane="XY")

   # 3. Shell (ONE TIME ONLY) - use small thickness!
   shell_body(thickness=0.1, faceindex=0)

   # 4. Final touches (fillets)
   fillet_edges(radius=0.2, edges=[0, 1, 2])
   ```

**Error is now detected and prevented with helpful guidance.**

## Transform and Move Operations

### Issue: Invalid Transform Errors

**Problem:** Move operations fail with `RuntimeError: invalid transform`

**Why:** The transformation matrix is malformed or contains invalid values (NaN, infinity, or incompatible rotation/translation).

**Workaround:**

- Verify x, y, z values are valid floats
- Avoid extreme values (> 10000 or < -10000)
- Use relative moves instead of absolute positions
- Check that bodies exist before attempting to move them

**Error is now logged but won't block workflow.**

## Best Practices

### 1. Sequential Modeling Workflow

```python
# GOOD: Complete one feature entirely before starting the next
draw_box(10, 10, 2, 0, 0, 0)
sketch_on_face(body_index=-1, face_index=4)  # Top face
draw_polygon(sides=6, radius=3, x=0, y=0, z=0)
pocket_recess(depth=0.5)  # Complete pocket before next sketch

# AVOID: Interleaving operations
draw_box(10, 10, 2, 0, 0, 0)
sketch_on_face(body_index=-1, face_index=4)
draw_polygon(sides=6, radius=3, x=0, y=0, z=0)
sketch_on_face(body_index=-1, face_index=4)  # Will likely fail
draw_circle(radius=1, x=0, y=0, z=0)
pocket_recess(depth=0.5)
```

### 2. Track Body and Sketch IDs

```python
# Use explicit IDs for complex operations
draw_box(10, 10, 2, 0, 0, 0)
body_info = get_active_body()  # Returns body_id
rename_body(body_info['body_id'], 'MainBody')

sketch_on_face(body_index=-1, face_index=4)
sketch_info = get_active_sketch()  # Returns sketch_id

draw_circle(radius=2, x=0, y=0, z=0)
pocket_recess(depth=0.5, body_id=body_info['body_id'], sketch_id=sketch_info['sketch_id'])
```

### 3. Verify Operations

```python
# Check results after critical operations
extrude_result = extrude_last_sketch(value=5, taperangle=0)
if not extrude_result.get('success'):
    print(f"Extrude failed: {extrude_result.get('error')}")

# Verify body count
bodies = list_bodies()
print(f"Current body count: {bodies['count']}")
```

### 4. Use Simple Patterns

When creating complex shapes, break them down:

```python
# Instead of one complex sketch with many lines
# Use multiple simple sketches or primitive shapes

# AVOID:
draw_lines([(0,0), (1,1), (2,0), (3,1), (4,0)])  # Complex zigzag

# PREFER:
# Break into separate features or use patterns
draw_box(1, 1, 0.5, 0, 0, 0)
circular_pattern(quantity=5, axis='Z', plane='XY')
```

## Silent Failures

Some operations may complete without errors but not produce the expected result. This typically happens when:

1. **Geometry doesn't intersect**: Pocket operations require the sketch to overlap with the target body
2. **Invalid parameters**: Values are out of acceptable range but don't trigger exceptions
3. **Topology constraints**: The operation would create invalid geometry so Fusion silently skips it

**Always verify results visually or programmatically after critical operations.**

## Error Handling Updates

Recent improvements to error handling:

- Success notifications removed - operations complete silently on success
- Failure notifications still appear to alert you to problems
- RuntimeErrors for shell and move operations now provide clear error messages
- Informational warnings about open sketches removed (open sketches are valid for paths, etc.)

## Reporting Issues

If you encounter persistent failures:

1. Check this document for known workarounds
2. Verify your parameters are within valid ranges
3. Try simplifying the operation
4. Report the issue with minimal reproduction steps

## Future Improvements

Areas being investigated:

- Better state tracking between operations
- Automatic retry logic for topology-sensitive operations
- Enhanced error messages with suggested fixes
- Batch operation queuing with automatic spacing
