# Future Enhancement Specification: Production-Grade CAD Automation

**Status:** Specification - Not Yet Implemented  
**Target:** Transform reliability from ~40% to 99%+ for multi-step CAD workflows  
**Priority:** High (enables complex prop replicas and architectural modeling)

---

## Executive Summary

This document specifies 15 new/enhanced MCP tools to address fundamental workflow constraints in the current Fusion 360 MCP integration. The enhancements add validation, state tracking, semantic face selection, batch operations, and transaction support.

**Current State:** Operations fail silently, face indices become stale, sequential operations accumulate errors, no audit trail.

**Target State:** Every operation returns explicit success/failure, semantic face selection prevents stale indices, batch operations reduce errors, complete audit trail enables debugging.

---

## Problem Statement

### Current Workflow Failures

```python
# Example: Create hexagonal tower with 5 recessed vent bands
# Current approach (FAILS ~60% of the time):

draw_polygon(radius=14.7, sides=6)
extrude(value=20)
sketch_on_face(body_index=1, face_index=1)  # ✅ Works first time
draw_2d_rectangle()  
pocket_recess(depth=0.5)  # ⚠️ May fail silently
sketch_on_face(body_index=1, face_index=1)  # ❌ Face index now stale!
draw_2d_rectangle()
pocket_recess(depth=0.5)  # ❌ Fails but no error
# Result: Blue sketch lines rendered, not actual pockets
```

### Root Causes

| Problem | Current Symptom | Missing Tool |
|---------|-----------------|--------------|
| Sketch geometry silently rejected | Returns generic "created" message | `get_sketch_status()` validation |
| Face indices become stale | Next sketch_on_face() fails silently | `list_faces()` topology tracking |
| Pocket doesn't actually cut | No error, but volume unchanged | `pocket_recess_safe()` with validation |
| Multi-sketch failures accumulate | Can't diagnose which step failed | `get_operation_log()` audit trail |
| Hardcoded face indices fragile | Break after any boolean operation | `find_face_by_property()` semantic selection |
| Multiple rectangles draw inefficiently | Error rate increases per call | `draw_rectangles_batch()` |
| No atomic operations | One failure ruins entire sequence | `begin_transaction()` / `commit()` |

---

## Proposed Enhancement Phases

### Phase 1: Critical (Fixes Immediate Failures)

#### 1. `get_sketch_status()` - Validate Sketch Before Closing

**Purpose:** Verify sketch geometry was actually accepted before closing.

**Parameters:**
```json
{
  "sketch_id": "string (optional, current sketch if null)",
  "include_geometry": "boolean (default: true)"
}
```

**Returns:**
```json
{
  "sketch_id": "sketch_12345",
  "is_valid": true,
  "profile_count": 5,
  "closed_profiles": 5,
  "open_profiles": 0,
  "geometry_valid": true,
  "bounds": {"min": [-10, -10, 0], "max": [10, 10, 5]},
  "message": "Sketch valid: 5 closed profiles, 23 segments"
}
```

**Usage:**
```python
draw_lines(points=[...])
status = get_sketch_status()
assert status["geometry_valid"], f"Sketch invalid: {status.get('error_message')}"
close_sketch()
```

---

#### 2. `list_faces()` - Query Face Topology with Properties

**Purpose:** Get all faces with geometric properties (not just indices).

**Parameters:**
```json
{
  "body_id": "string (required)"
}
```

**Returns:**
```json
{
  "body_id": "body_0",
  "face_count": 8,
  "faces": [
    {
      "index": 0,
      "type": "planar",
      "area": 250.5,
      "normal": [0, 0, 1],
      "position_center": [0, 0, 10],
      "orientation": "top",
      "is_planar": true
    }
  ]
}
```

**Usage:**
```python
faces = list_faces(body_id=1)
front_face = next(f for f in faces["faces"] if f["normal"] == [0, 1, 0])
sketch_on_face(body_id=1, face_index=front_face["index"])
```

---

#### 3. `pocket_recess_safe()` - Enhanced with Validation

**Purpose:** Create pocket with complete validation and result confirmation.

**Parameters:**
```json
{
  "body_id": "string (required)",
  "sketch_id": "string (required)",
  "depth": "float (required)",
  "validate_before": "boolean (default: true)",
  "validate_after": "boolean (default: true)"
}
```

**Returns:**
```json
{
  "success": true,
  "volume_removed": 9.5,
  "geometry_valid": true,
  "operation_applied": true,
  "message": "Pocket created: 9.5 cm³ removed"
}
```

**Usage:**
```python
result = pocket_recess_safe(body_id=1, sketch_id=5, depth=0.5)
if not result["success"]:
    print(f"ERROR: {result['error']}")
    undo()
```

---

#### 4. `get_feature_history()` - Audit Trail

**Purpose:** List all features applied to a body with success/failure status.

**Parameters:**
```json
{
  "body_id": "string (required)",
  "include_parameters": "boolean (default: true)"
}
```

**Returns:**
```json
{
  "body_id": "body_1",
  "feature_count": 6,
  "features": [
    {
      "index": 0,
      "type": "Extrude",
      "status": "valid",
      "volume_change": 2940.0
    },
    {
      "index": 1,
      "type": "Pocket",
      "status": "failed",
      "error_message": "Sketch profile is open",
      "volume_change": 0
    }
  ]
}
```

---

### Phase 2: High Priority (Enables Robust Geometry)

#### 5. `find_face_by_property()` - Semantic Face Selection

**Purpose:** Locate faces by geometric criteria instead of fragile indices.

**Parameters:**
```json
{
  "body_id": "string (required)",
  "selector": "string (enum: front|back|top|bottom|left|right|largest)"
}
```

**Returns:**
```json
{
  "primary_face_index": 1,
  "faces": [
    {
      "index": 1,
      "selector_match": "front",
      "normal": [0, 1, 0],
      "area": 200.0
    }
  ]
}
```

---

#### 6. `draw_rectangles_batch()` - Atomic Batch Geometry

**Purpose:** Draw multiple rectangles in one operation.

**Parameters:**
```json
{
  "plane": "string (XY|YZ|XZ)",
  "rectangles": [
    {"x_min": float, "x_max": float, "y_min": float, "y_max": float}
  ]
}
```

**Returns:**
```json
{
  "rectangle_count": 5,
  "rectangles_drawn": 5,
  "rectangles_failed": 0,
  "geometry_valid": true
}
```

---

#### 7. `pocket_smart()` - Intelligent Depth Modes

**Purpose:** Create pockets with smart depth calculation (absolute, through, wall_thickness, percentage).

**Parameters:**
```json
{
  "body_id": "string (required)",
  "sketch_id": "string (required)",
  "depth_mode": "string (absolute|through|wall_thickness|percentage)",
  "depth_value": "float (required)"
}
```

---

#### 8. Enhanced `sketch_on_face()` - Require Explicit body_id

**Breaking Change:** Require string body_id instead of integer body_index.

**NEW Parameters:**
```json
{
  "body_id": "string (REQUIRED)",
  "face_index": "int (required)",
  "verify_face_exists": "boolean (default: true)"
}
```

---

### Phase 3: Medium Priority (Architectural Quality)

#### 9-10. Transaction Support

- `begin_transaction(transaction_id)`
- `commit_transaction(transaction_id)`
- `rollback_transaction(transaction_id)`
- `get_operation_log()`

**Purpose:** Atomic multi-step operations with rollback.

---

#### 11-12. Additional Validation Tools

- `create_sketch_on_body_plane()` - Sketch without face dependency
- `validate_face_exists()` - Check face validity

---

### Phase 4: Nice-to-Have

#### 13-15. Polish Tools

- `select_faces_by_semantic()` - Batch semantic selection
- `clear_sketch()` - Clear without closing
- `extrude_safe()` - Enhanced with validation

---

## Implementation Priority

### Must Have (Phase 1)
These tools fix immediate silent failures and enable basic validation:
1. ✅ `get_sketch_status()` - Critical for validation
2. ✅ `list_faces()` - Fixes face topology issues
3. ✅ `pocket_recess_safe()` - Ensures operations actually work
4. ✅ `get_feature_history()` - Enables debugging

### Should Have (Phase 2)
These tools make workflows robust and efficient:
5. `find_face_by_property()` - Prevents stale face indices
6. `draw_rectangles_batch()` - Reduces error accumulation
7. `pocket_smart()` - Enables parametric design
8. Enhanced `sketch_on_face()` - Explicit IDs prevent ambiguity

### Nice to Have (Phase 3-4)
These tools add polish and advanced features:
9-15. Transactions, operation log, additional validation

---

## Expected Improvements

### Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Multi-step operation success rate | ~40% | 99%+ |
| Silent failures | Frequent | None |
| Face index breakage after topology changes | Always | Never |
| Debugging failed builds | Manual trial-and-error | Complete audit trail |
| Batch operation efficiency | Sequential, error-prone | Atomic, validated |

### Test Case: 5-Band Vent Segment

**Current Workflow (40% success):**
```python
sketch_on_face(body_index=1, face_index=1)
draw_2d_rectangle()
pocket_recess(depth=0.5)  # Might fail silently
sketch_on_face(body_index=1, face_index=1)  # Face index stale!
# Result: Blue sketch lines, not pockets
```

**Enhanced Workflow (99% success):**
```python
begin_transaction("vent_bands")
front = find_face_by_property(body_id=1, selector="front")
sketch_on_face(body_id="body_1", face_index=front["primary_face_index"])
result = draw_rectangles_batch(plane="XY", rectangles=[...])
assert result["rectangles_failed"] == 0
status = get_sketch_status()
assert status["profile_count"] == 5
close_sketch()
pocket_result = pocket_recess_safe(body_id="body_1", depth=0.5)
assert pocket_result["success"]
commit_transaction("vent_bands")
# Result: 5 actual pockets cut into geometry
```

---

## Mandatory Workflow Rules (for AI Agents)

When these tools are implemented, AI agents should follow these rules:

1. **SKETCH VALIDATION:**
   - ALWAYS call `get_sketch_status()` after drawing complex geometry
   - NEVER `close_sketch()` if `geometry_valid=false`

2. **FACE SELECTION:**
   - ALWAYS use `list_faces()` to discover current face topology
   - PREFER semantic face selection over hardcoded indices
   - NEVER assume face_index stays constant between operations

3. **POCKET OPERATIONS:**
   - ALWAYS use `pocket_recess_safe()` (never plain `pocket_recess()`)
   - ALWAYS check `success=true` before proceeding
   - ALWAYS call `get_feature_history()` to verify pocket was applied

4. **MULTI-STEP OPERATIONS:**
   - For sequences >3 operations, use `begin_transaction()`
   - If any step fails, call `rollback_transaction()`

5. **BATCH GEOMETRY:**
   - ALWAYS use `draw_rectangles_batch()` for 2+ rectangles
   - ALWAYS verify `batch result["rectangles_failed"] == 0`

6. **ERROR DIAGNOSTICS:**
   - Upon ANY operation failure, call `get_operation_log(status_filter="failed")`
   - Check `get_feature_history()` to find which feature failed

---

## Implementation Notes

### For Server Developers

This specification requires:
1. **New HTTP endpoints** in `MCP_Server.py` for each tool
2. **New Python functions** in `MCP.py` (Fusion add-in) for API calls
3. **State tracking** for transactions and operation log
4. **Validation logic** for geometry checks
5. **Unit tests** (100+ tests recommended)

### Breaking Changes

- `sketch_on_face()` will require string `body_id` instead of int `body_index`
- Migration path: Phase 1 adds new tools without breaking existing ones
- Phase 2 introduces breaking changes with deprecation warnings

### Estimated Implementation Effort

- **Phase 1:** 2-3 weeks (4 critical tools)
- **Phase 2:** 2-3 weeks (4 high-priority tools)
- **Phase 3:** 3-4 weeks (transactions + operation log)
- **Phase 4:** 1-2 weeks (polish)
- **Total:** 8-12 weeks for complete implementation

---

## References

- **Original Issue:** Notification suppression and error handling
- **Related Documentation:** KNOWN_LIMITATIONS.md
- **Use Case:** Stargate Atlantis Ancient Override Control Console (112.5cm prop replica)
- **Fusion 360 API:** https://developers.autodesk.com/en/docs/fusion-360/

---

## Status

**Current Status:** Specification complete - awaiting implementation decision

**Next Steps:**
1. Review and approve specification
2. Prioritize which phases to implement
3. Create implementation tasks/issues
4. Begin Phase 1 development

**Note:** This is a substantial feature enhancement that would significantly improve the reliability and usability of the Fusion MCP integration. The current PR focuses on immediate notification and error handling fixes (completed). This specification outlines the next major evolution of the toolkit.
