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

### Issue: Shell Compute Errors
**Problem:** Shell operations fail with `RuntimeError: Shell2 / Compute Failed // ASM_RBI_NO_LUMP_LEFT`

**Why:** The shell thickness or face selection creates invalid geometry (e.g., walls that are thicker than the body, or removing critical faces).

**Workaround:**
- Use smaller shell thickness values
- Try different face indices
- Ensure the body has sufficient material for the shell thickness
- Verify body volume is adequate before shelling

**Error is now logged but won't block workflow.**

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
